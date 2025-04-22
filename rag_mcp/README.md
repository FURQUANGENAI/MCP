# MCP-RAG Server Developed by Furquan.

A Retrieval-Augmented Generation (RAG) server built with the Model Context Protocol (MCP) framework, integrating GroundX for document ingestion and search, and OpenAI for generating responses. This server enables developers to upload documents, search their content, and query them using an AI-powered assistant.

## Features
- **Document Ingestion**: Upload PDF documents to a GroundX knowledge base.
- **Content Search**: Retrieve relevant context from ingested documents based on user queries.
- **AI-Powered Responses**: Generate detailed answers using OpenAI's GPT-4o model, leveraging GroundX's semantic retrieval.
- **Configurable**: Supports customizable API keys, models, and bucket IDs via a Pydantic-based configuration.

## Prerequisites
- Python 3.9 or higher
- `uv` (for dependency management)
- Access to GroundX API
- OpenAI API key

## Installation

### 1. Clone the Repository
```bash
git https://github.com/FURQUANGENAI/MCP.git
cd mcp-rag

===========

open Cursor ide
open terminal 
go to command prompt ( run conda activate command)
uv init rag-mcp
== Initialized project `rag-mcp` at `C:\MCPWorkspace\rag-mcp`
uv sync
.venv\Scripts\activate -activate the environment.

uv add "mcp[cli]"   -- add library for mcp
uv add GroundX
uv sync - this will update the pyprojectoml file
uv add openai

you can select python runtime 

uv run mcp dev server/server.py  - to see the output on Interceptor.
uv run mcp install server/server.py  - to see the output on Claude Desktop APP