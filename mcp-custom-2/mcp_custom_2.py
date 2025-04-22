from mcp.server.fastmcp import FastMCP
import os
import httpx
from dotenv import load_dotenv
from typing import Dict, Optional
import json
import sys
from duckduckgo_search import DDGS
import asyncio

# Load environment variables
load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

# Validate API key
if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY must be set in environment variables")

# Server and file configuration
mcp = FastMCP("Weather Search")
NOTES_FILE = os.path.join(os.path.dirname(__file__), "mynotes.txt")

def ensure_file() -> None:
    """Ensure the notes file exists, creating it if it doesn't."""
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            pass  # Create empty file

@mcp.tool()
def add_note(message: str) -> str:
    """
    Append a new note to the note file.

    Args:
        message (str): The note content to be added.

    Returns:
        str: Confirmation message indicating the note was saved.

    Raises:
        IOError: If writing to the file fails.
    """
    ensure_file()
    try:
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(message.strip() + "\n")
        return "Note saved successfully!"
    except IOError as e:
        raise IOError(f"Failed to write note: {e}")

@mcp.tool()
async def duckduckgo_search_results(query: str) -> Dict[str, any]:
    """
    Fetch search results from DuckDuckGo using the duckduckgo-search library.

    Args:
        query (str): The search query to perform.

    Returns:
        Dict[str, any]: JSON-like response containing search results.

    Raises:
        Exception: If the search fails or returns an error.
    """
    try:
        # Use synchronous DDGS.text and run in event loop
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: DDGS().text(query, max_results=10))
        formatted_results = {"results": [{"title": r["title"], "link": r["href"]} for r in results]}
        print(f"DuckDuckGo Response: {json.dumps(formatted_results)}", file=sys.stderr)
        return formatted_results
    except Exception as e:
        print(f"DuckDuckGo Search Error: {str(e)}", file=sys.stderr)
        raise

@mcp.tool()
async def fetch_weather(city: str) -> Dict[str, any]:
    """
    Fetch current weather for a city using WeatherAPI.

    Args:
        city (str): The city name to query.

    Returns:
        Dict[str, any]: Weather data including temperature, condition, etc.

    Raises:
        httpx.HTTPStatusError: If the API request fails.
        ValueError: If the response is not valid JSON.
    """
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            if "current" not in data:
                raise ValueError("Invalid weather data received")
            return data
    except httpx.HTTPStatusError as e:
        print(f"Weather API Error: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        raise
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        raise

@mcp.tool()
def read_notes() -> str:
    """
    Read and return all notes from the note file.

    Returns:
        str: All notes as a single string separated by line breaks, or a default message.

    Raises:
        IOError: If reading the file fails.
    """
    ensure_file()
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return content or "No notes yet."
    except IOError as e:
        raise IOError(f"Failed to read notes: {e}")

@mcp.resource("notes://latest")
def get_latest_note() -> str:
    """
    Get the most recently added note from the note file.

    Returns:
        str: The last note entry, or a default message if none exist.

    Raises:
        IOError: If reading the file fails.
    """
    ensure_file()
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-1].strip() if lines else "No notes yet."
    except IOError as e:
        raise IOError(f"Failed to read latest note: {e}")

@mcp.prompt()
def note_summary_prompt() -> str:
    """
    Generate a prompt asking the AI to summarize all current notes.

    Returns:
        str: A prompt string with all notes for summarization, or a message if none exist.

    Raises:
        IOError: If reading the file fails.
    """
    ensure_file()
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return f"Summarize the current notes: {content}" if content else "There are no notes yet."
    except IOError as e:
        raise IOError(f"Failed to generate summary prompt: {e}")

