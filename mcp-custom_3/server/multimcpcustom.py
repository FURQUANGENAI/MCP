from typing import Any, Dict
import httpx,json,os
import io,sys
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


# Initialize FastMCP server
mcp = FastMCP("multimcpcustom")

load_dotenv()
os.environ["NEWSAPI_KEY"]=os.getenv("NEWSAPI_KEY")
os.environ["ALPHAVANTAGE_KEY"]=os.getenv("ALPHAVANTAGE_KEY")

# Constants
NEWS_API_BASE = "https://newsapi.org/v2"
ALPHAVANTAGE_API_BASE = "https://www.alphavantage.co/query"
USER_AGENT = "api-client/1.0"

async def make_news_request(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any] | None:
    """Make a request to the News API with proper error handling."""
    if not os.getenv("NEWSAPI_KEY"):
        print("NEWSAPI_KEY environment variable is not set", file=sys.stderr)
        return None
        
    if params is None:
        params = {}
    
    params["apiKey"] = os.getenv("NEWSAPI_KEY")
    
    headers = {
        "User-Agent": USER_AGENT,
        "X-Api-Key": os.getenv("NEWSAPI_KEY")
    }
    
    url = f"{NEWS_API_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            print(f"Request to {url} timed out", file=sys.stderr)
            return None
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code} for {url}: {e.response.text}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Unexpected error for {url}: {str(e)}", file=sys.stderr)
            return None

async def make_alphavantage_request(params: Dict[str, Any] = None) -> Dict[str, Any] | None:
    """Make a request to the Alpha Vantage API with proper error handling."""
    if not os.getenv("ALPHAVANTAGE_KEY"):
        print("ALPHAVANTAGE_KEY environment variable is not set", file=sys.stderr)
        return None
        
    if params is None:
        params = {}
    
    params["apikey"] = os.getenv("ALPHAVANTAGE_KEY")
    
    headers = {
        "User-Agent": USER_AGENT
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(ALPHAVANTAGE_API_BASE, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            print(f"Request to {ALPHAVANTAGE_API_BASE} timed out", file=sys.stderr)
            return None
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code} for {ALPHAVANTAGE_API_BASE}: {e.response.text}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Unexpected error for {ALPHAVANTAGE_API_BASE}: {str(e)}", file=sys.stderr)
            return None


async def make_api_request(url: str, params: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Dict[str, Any] | None:
    """Make an async HTTP request with error handling."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            print(f"Request to {url} timed out", file=sys.stderr)
            return None
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code} for {url}: {e.response.text}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Unexpected error for {url}: {str(e)}", file=sys.stderr)
            return None

@mcp.tool()
async def get_news(topic: str) -> str:
    """Fetch news articles for a given topic.

    Args:
        topic (str): The topic to search for news (e.g., 'technology').

    Returns:
        str: Formatted string of news titles and links, or an error message.
    """
    if not topic.strip():
        return "Topic cannot be empty"
    
    params = {"q": topic, "language": "en", "sortBy": "publishedAt"}
    data = await make_news_request("everything", params)
    
    if not data:
        return "Unable to fetch news (API key may be missing or invalid)"
    
    if "articles" not in data or not data["articles"]:
        return "No articles found for the given topic"
    
    # Limit to 10 articles to avoid overwhelming output
    articles = data["articles"][:10]
    
    formatted_articles = []
    for article in articles:
        formatted_articles.append(
            f"Title: {article.get('title', 'No title')}\n"
            f"Source: {article.get('source', {}).get('name', 'Unknown source')}\n"
            f"Published: {article.get('publishedAt', 'Unknown date')}\n"
            f"Link: {article.get('url', '#')}"
        )
    
    return "\n---\n".join(formatted_articles)

@mcp.tool()
async def get_stock_price(symbol: str) -> str:
    """Get stock price information for a given symbol.

    Args:
        symbol (str): The stock symbol to look up (e.g., 'AAPL', 'MSFT').

    Returns:
        str: Formatted string of stock price information, or an error message.
    """
    if not symbol.strip():
        return "Stock symbol cannot be empty"
    
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "5min"
    }
    
    data = await make_alphavantage_request(params)
    
    if not data:
        return "Unable to fetch stock data (API key may be missing or invalid)"
    
    if "Error Message" in data:
        return f"Error: {data['Error Message']}"
    
    if "Time Series (5min)" not in data or not data["Time Series (5min)"]:
        return f"No stock data found for symbol '{symbol}'"
    
    try:
        latest_time = list(data["Time Series (5min)"].keys())[0]
        latest_data = data["Time Series (5min)"][latest_time]
        
        return (
            f"Symbol: {symbol.upper()}\n"
            f"Price: ${latest_data.get('4. close', 'N/A')}\n"
            f"Open: ${latest_data.get('1. open', 'N/A')}\n"
            f"High: ${latest_data.get('2. high', 'N/A')}\n"
            f"Low: ${latest_data.get('3. low', 'N/A')}\n"
            f"Volume: {latest_data.get('5. volume', 'N/A')}\n"
            f"Last Updated: {latest_time}"
        )
    except (KeyError, IndexError) as e:
        print(f"Error parsing stock data: {str(e)}", file=sys.stderr)
        return f"Error processing stock data for '{symbol}'"

TASKS_FILE = "tasks.json"

def ensure_tasks_file():
    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "w") as f:
            json.dump([], f)

@mcp.tool()
def add_task(task: str) -> str:
    ensure_tasks_file()
    with open(TASKS_FILE, "r") as f:
        tasks = json.load(f)
    tasks.append({"title": task, "status": "pending", "id": len(tasks) + 1})
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f)
    return f"Task '{task}' added with ID {len(tasks)}"