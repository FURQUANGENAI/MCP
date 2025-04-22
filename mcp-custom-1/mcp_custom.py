from mcp.server.fastmcp import FastMCP



# Create an MCP server
mcp = FastMCP("CALCFURQUANA")

# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

# Add a subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract the second number from the first"""
    return a - b

# Add a multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

# Add a division tool
@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divide the first number by the second (returns float, raises ZeroDivisionError if b is 0)"""
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

