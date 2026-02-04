# BBj AI Strategy

This repo contains the AI strategy documentation for BBj (a Business BASIC language by BASIS International) and a RAG ingestion pipeline for processing BBj documentation into a vector database. The documentation site covers LLM fine-tuning, IDE integration, documentation chat, and RAG database design across 7 chapters.

**Live site:** https://stephanwald.github.io/bbj-ai-strategy/

## What's Here

- **`/docs`** and root Docusaurus config -- the strategy documentation site (Docusaurus 3, TypeScript, deployed to GitHub Pages)
- **`/rag-ingestion`** -- Python ingestion pipeline for processing BBj documentation sources into pgvector (Python 3.12+, uv)

## Tech Stack

| Component           | Stack                                          |
| ------------------- | ---------------------------------------------- |
| Documentation site  | Docusaurus 3.9, Rspack, TypeScript, GitHub Pages |
| Ingestion pipeline  | Python 3.12+, uv, pgvector/PostgreSQL          |

## Getting Started

**Documentation site** -- visit the [live site](https://stephanwald.github.io/bbj-ai-strategy/) to read the strategy docs.

**Ingestion pipeline** -- set up the Python development environment:

```bash
cd rag-ingestion
uv sync
make check
```

Full setup details will be in `rag-ingestion/README.md`.

## Deployment

### Shared Server Setup

Deploy the RAG system on a shared server for LAN access.

**Prerequisites:**
- Docker and Docker Compose
- Ollama running on host with `OLLAMA_HOST=0.0.0.0:11434`

**Setup:**

```bash
cd rag-ingestion
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
docker compose up -d
```

**Access URLs (replace with your server IP):**
- Chat UI: `http://<server-ip>:10800/chat`
- MCP endpoint: `http://<server-ip>:10800/mcp`
- REST API: `http://<server-ip>:10800/search`

Port 10800 must be accessible on your network (check firewall settings).

### Claude Desktop Configuration

Connect Claude Desktop to the shared MCP server using `mcp-remote`.

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bbj-knowledge": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "http://192.168.1.100:10800/mcp",
        "--allow-http"
      ]
    }
  }
}
```

**Config file locations:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Replace `192.168.1.100` with your server's actual IP address.

### Troubleshooting

- **"Connection refused"** - Verify server IP and that Docker is running (`docker compose ps`)
- **"--allow-http required"** - mcp-remote blocks HTTP by default; the `--allow-http` flag is required for non-HTTPS servers
- **"Task group not initialized"** - Internal MCP SDK error; restart the Docker container
