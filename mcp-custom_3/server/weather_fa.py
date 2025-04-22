from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weatherfa")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"
VALID_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split())

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
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

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
        Event: {props.get('event', 'Unknown')}
        Area: {props.get('areaDesc', 'Unknown')}
        Severity: {props.get('severity', 'Unknown')}
        Description: {props.get('description', 'No description available')}
        Instructions: {props.get('instruction', 'No specific instructions provided')}
        """

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state (str): Two-letter US state code (e.g., 'CA', 'NY').

    Returns:
        str: Formatted string of active weather alerts, or an error message if no data is available.

    Raises:
        ValueError: If the state code is invalid.
        httpx.HTTPStatusError: If the NWS API request fails.
    """
    state = state.upper()
    if state not in VALID_STATES:
        raise ValueError(f"Invalid state code: {state}. Use a two-letter US state code.")
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource with optional transformation."""
    return f"Resource echo: {message.upper()}"

