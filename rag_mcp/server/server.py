import os
import asyncio
from dotenv import load_dotenv
from groundx import GroundX, Document
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
import openai
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GROUNDX_API_KEY = os.getenv("GROUNDX_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BUCKET_ID = os.getenv("BUCKET_ID")
if not all([GROUNDX_API_KEY, OPENAI_API_KEY, BUCKET_ID]):
    raise ValueError("GROUNDX_API_KEY, OPENAI_API_KEY, and BUCKET_ID must be set")

# Initialize clients
client = GroundX(api_key=GROUNDX_API_KEY)
openai.api_key = OPENAI_API_KEY

mcp = FastMCP("mcp-rag")

class SearchResponse(BaseModel):
    query: str
    score: float
    result: str

class SearchConfig(BaseModel):
    openai_api_key: str = Field(default_factory=lambda: OPENAI_API_KEY)
    groundx_api_key: str = Field(default_factory=lambda: GROUNDX_API_KEY)
    completion_model: str = "gpt-4o"
    bucket_id: int = Field(default_factory=lambda: int(BUCKET_ID))

@mcp.tool()
async def process_search_query(query: str, config: Optional[SearchConfig] = None) -> SearchResponse:
    """Process a search query using GroundX and OpenAI.

    Args:
        query (str): The search query string.
        config (Optional[SearchConfig]): Optional configuration for API keys and settings.

    Returns:
        SearchResponse: Object containing the query, relevance score, and generated result.

    Raises:
        ValueError: If query is empty or API keys are missing.
        Exception: If GroundX or OpenAI API calls fail.
    """
    if not query.strip() or not all(c.isprintable() for c in query):
        raise ValueError("Invalid query string")
    if config is None:
        config = SearchConfig()
    logger.info(f"Processing query: {query}")

    try:
        content_response = await asyncio.to_thread(client.search.content, id=config.bucket_id, query=query)
        results = content_response.search
        logger.info(f"GroundX search results: {results.text}")

        completion = await asyncio.to_thread(
            openai.chat.completions.create,
            model=config.completion_model,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a highly knowledgeable assistant... [Your existing instruction] ===\n{results.text}\n===\n"""
                },
                {"role": "user", "content": query},
            ],
        )
        logger.info(f"OpenAI response: {completion.choices[0].message.content}")
        return SearchResponse(query=query, score=results.score, result=completion.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise

@mcp.tool()
async def search_doc_for_rag_context(query: str) -> str:
    """Searches and retrieves relevant context from a knowledge base.

    Args:
        query (str): The search query supplied by the user.

    Returns:
        str: Relevant text content that can be used by the LLM to answer the query.

    Raises:
        ValueError: If query is invalid.
        Exception: If search fails.
    """
    if not query.strip():
        raise ValueError("Query cannot be empty")
    try:
        response = await asyncio.to_thread(client.search.content, id=int(BUCKET_ID), query=query, n=5)
        return response.search.text
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise

@mcp.tool()
def ingest_documents(local_file_path: str) -> str:
    """Ingest documents from a local file into the knowledge base.

    Args:
        local_file_path: The path to the local file containing the documents to ingest.

    Returns:
        str: A message indicating the documents have been ingested.

    Raises:
        ValueError: If the file path is invalid or unsupported.
        Exception: If ingestion fails.
    """
    if not os.path.exists(local_file_path):
        raise ValueError(f"File not found: {local_file_path}")
    if not local_file_path.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported")
    file_name = os.path.basename(local_file_path)
    try:
        client.ingest(
            documents=[
                Document(
                    bucket_id=int(BUCKET_ID),
                    file_name=file_name,
                    file_path=local_file_path,
                    file_type="pdf",
                    search_data=dict(key="value"),
                )
            ]
        )
        return f"Ingested {file_name} into the knowledge base. It should be available in a few minutes"
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise

async def main():
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())