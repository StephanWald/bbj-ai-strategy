# Phase 27: Remote Access - Research

**Researched:** 2026-02-04
**Domain:** MCP Streamable HTTP Transport, Docker Network Binding, Claude Desktop Configuration
**Confidence:** HIGH

## Summary

This phase enables engineers on the local network to access the BBJ RAG system (chat UI + MCP server) from their own machines without running Docker locally. The implementation requires:

1. **Streamable HTTP MCP endpoint** mounted on the existing FastAPI app at `/mcp`
2. **Network-accessible binding** via `0.0.0.0` in the Docker Compose configuration
3. **Claude Desktop configuration snippet** for engineers to connect via `mcp-remote`

The MCP Python SDK (v1.25+) fully supports Streamable HTTP transport via `FastMCP.streamable_http_app()`. The key integration challenge is properly managing the lifespan context when mounting the MCP app alongside the existing FastAPI application. Since the decision is "shared mode by default" with no authentication, the implementation is straightforward.

**Primary recommendation:** Mount the MCP Streamable HTTP endpoint directly on the existing FastAPI app using a combined lifespan handler, bind to `0.0.0.0:8000` in Docker, and provide a copy-paste Claude Desktop config using `npx mcp-remote` with the `--allow-http` flag.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mcp[cli] | >=1.25 | MCP Python SDK with FastMCP | Official Anthropic SDK, already installed |
| mcp-remote | latest | stdio-to-HTTP bridge for Claude Desktop | Only option for Claude Desktop HTTP connections |
| FastAPI | >=0.115 | Existing API framework | Already in use, supports ASGI mounting |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uvicorn | >=0.34 | ASGI server | Already in use, supports 0.0.0.0 binding |
| starlette | (bundled) | ASGI utilities | Lifespan context management |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| mcp-remote | Direct HTTP in claude_desktop_config.json | Not supported - Claude Desktop only supports stdio for JSON config servers |
| Mount at /mcp | Separate Starlette app | More complex, would need separate lifespan management |

**Installation:**
```bash
# Already installed in project (mcp[cli]>=1.25)
# Engineers need Node.js for mcp-remote (one-time)
npm install -g mcp-remote  # or use npx
```

## Architecture Patterns

### Recommended Project Structure
```
src/bbj_rag/
├── app.py               # FastAPI app with combined lifespan
├── mcp_server.py        # FastMCP instance + tool definitions (existing)
└── mcp_http.py          # NEW: HTTP mounting utilities
```

### Pattern 1: Combined Lifespan Handler

**What:** Single lifespan context manager that handles both FastAPI startup/shutdown and MCP session manager.

**When to use:** When mounting MCP on existing FastAPI app (our case).

**Example:**
```python
# Source: https://gofastmcp.com/deployment/http (verified)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# Create FastMCP instance with Streamable HTTP settings
mcp = FastMCP(
    "bbj-knowledge",
    stateless_http=True,  # No session state between requests
)

@mcp.tool()
async def search_bbj_knowledge(query: str, limit: int = 5) -> str:
    # ... existing tool implementation
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Existing startup logic (pool, schema, ollama warmup)
    # ...

    # Enter MCP session manager context
    async with mcp.session_manager.run():
        yield

    # Existing shutdown logic
    # ...

app = FastAPI(title="BBJ RAG", lifespan=lifespan)
app.mount("/mcp", mcp.streamable_http_app())
```

### Pattern 2: Claude Desktop Configuration via mcp-remote

**What:** Use `mcp-remote` as a bridge between Claude Desktop (stdio-only) and the HTTP MCP server.

**When to use:** Claude Desktop cannot directly connect to HTTP servers via JSON config.

**Example:**
```json
{
  "mcpServers": {
    "bbj-knowledge": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "http://SERVER_IP:10800/mcp",
        "--allow-http"
      ]
    }
  }
}
```

**Key flags:**
- `--allow-http`: Required for non-HTTPS connections on trusted LAN
- `@latest`: Ensures latest version is used

### Pattern 3: Network Binding in Docker

**What:** Bind to `0.0.0.0` to allow connections from any network interface.

**When to use:** Shared server deployment on LAN.

**Example (already in Dockerfile):**
```bash
CMD ["uvicorn", "bbj_rag.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose verification:**
```yaml
ports:
  - "${APP_PORT_EXTERNAL:-10800}:8000"  # No 127.0.0.1 prefix = 0.0.0.0 binding
```

### Anti-Patterns to Avoid
- **Mounting MCP at root (/):** Conflicts with existing FastAPI routes. Use `/mcp` path.
- **Session-stateful HTTP for multi-instance:** Use `stateless_http=True` for horizontal scaling.
- **Hardcoding server IP in docs:** Use placeholders like `SERVER_IP` for flexibility.
- **Skipping lifespan integration:** Results in "Task group is not initialized" runtime errors.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| stdio-to-HTTP bridge | Custom proxy | mcp-remote | Handles SSE/streaming, maintained by community |
| MCP session management | Manual task groups | FastMCP.session_manager | Proper lifecycle handling, resumability support |
| Streamable HTTP protocol | Raw SSE implementation | mcp.server.streamable_http | JSON-RPC framing, session headers, resumability |

**Key insight:** The MCP SDK abstracts significant protocol complexity (session management, SSE streaming, JSON-RPC framing). Hand-rolling any of this would be error-prone and incompatible with clients.

## Common Pitfalls

### Pitfall 1: Missing Lifespan Context

**What goes wrong:** "Task group is not initialized. Make sure to use run()" error.

**Why it happens:** The MCP session manager requires an async context manager to run. When mounting on FastAPI, Starlette doesn't automatically run sub-application lifespans.

**How to avoid:** Explicitly call `async with mcp.session_manager.run()` in the parent app's lifespan handler.

**Warning signs:** 500 errors on `/mcp` endpoint, error message about task group.

### Pitfall 2: Path Confusion with Mount

**What goes wrong:** 404 errors when accessing MCP endpoint.

**Why it happens:** `streamable_http_app()` internally serves at `/mcp` by default. Mounting at `/mcp` results in `/mcp/mcp`.

**How to avoid:** Either:
1. Mount at `/` and accept `/mcp` as the path, OR
2. Configure `streamable_http_path="/"` in FastMCP constructor, then mount at `/mcp`

**Warning signs:** Requests to `/mcp` return 404 but `/mcp/mcp` works.

### Pitfall 3: Claude Desktop Ignoring JSON Config for Remote

**What goes wrong:** Claude Desktop doesn't connect to the remote server.

**Why it happens:** Claude Desktop only supports stdio transport for servers in `claude_desktop_config.json`. Remote HTTP servers must use Settings > Connectors UI or `mcp-remote` bridge.

**How to avoid:** Use `mcp-remote` as a stdio wrapper around the HTTP endpoint.

**Warning signs:** No errors, but Claude Desktop shows no tools available.

### Pitfall 4: HTTP Blocked Without --allow-http

**What goes wrong:** mcp-remote refuses to connect.

**Why it happens:** mcp-remote requires HTTPS by default for security.

**How to avoid:** Add `--allow-http` flag for trusted LAN connections.

**Warning signs:** Error message about HTTPS requirement.

### Pitfall 5: Firewall Blocking Port 10800

**What goes wrong:** Connection timeout from remote machines.

**Why it happens:** macOS/Windows firewall blocks incoming connections.

**How to avoid:** Ensure port 10800 is allowed in firewall settings.

**Warning signs:** `curl http://server:10800/health` times out from remote machine.

## Code Examples

Verified patterns from official sources:

### MCP HTTP Mounting on FastAPI

```python
# Source: https://gofastmcp.com/deployment/http
# Source: https://github.com/modelcontextprotocol/python-sdk/issues/673
from contextlib import asynccontextmanager
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# Create FastMCP with stateless HTTP mode
mcp = FastMCP(
    "bbj-knowledge",
    stateless_http=True,
    streamable_http_path="/",  # Serve at mount point, not /mcp/mcp
)

@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    # Your existing startup code...

    # Start MCP session manager
    async with mcp.session_manager.run():
        yield

    # Your existing shutdown code...

app = FastAPI(lifespan=combined_lifespan)
app.mount("/mcp", mcp.streamable_http_app())
```

### Claude Desktop Config with mcp-remote

```json
// Source: https://www.npmjs.com/package/mcp-remote
// Location: ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
// Location: %APPDATA%\Claude\claude_desktop_config.json (Windows)
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

### Verifying MCP Endpoint

```bash
# Test MCP endpoint is accessible
curl -X POST http://localhost:10800/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HTTP+SSE (two endpoints) | Streamable HTTP (single endpoint) | 2025-03-26 | Simpler client config, single endpoint |
| stdio-only for Claude Desktop | mcp-remote bridge | 2025 | Enables remote server connections |
| Session-stateful HTTP | stateless_http=True option | 2025 | Horizontal scaling support |

**Deprecated/outdated:**
- SSE transport (`/sse` endpoint): Still supported but deprecated, Streamable HTTP preferred
- Direct HTTP URL in claude_desktop_config.json: Never supported for remote servers

## Open Questions

Things that couldn't be fully resolved:

1. **MCP SDK path mounting behavior**
   - What we know: `streamable_http_app()` defaults to `/mcp` internally
   - What's unclear: Whether `streamable_http_path="/"` fully resolves mount conflicts
   - Recommendation: Test during implementation, document working pattern

2. **mcp-remote version stability**
   - What we know: `@latest` ensures current version
   - What's unclear: Breaking changes between versions
   - Recommendation: Document tested version in README after verification

## Sources

### Primary (HIGH confidence)
- [MCP Transports Specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports) - Official protocol spec
- [MCP Python SDK PyPI](https://pypi.org/project/mcp/) - v1.26.0 current, Streamable HTTP documented
- [FastMCP HTTP Deployment](https://gofastmcp.com/deployment/http) - Official FastMCP docs

### Secondary (MEDIUM confidence)
- [mcp-remote npm](https://www.npmjs.com/package/mcp-remote) - CLI flags and options
- [Claude Desktop Remote MCP](https://support.claude.com/en/articles/11503834-building-custom-connectors-via-remote-mcp-servers) - Anthropic support docs
- [GitHub Issue #673](https://github.com/modelcontextprotocol/python-sdk/issues/673) - Working mount patterns

### Tertiary (LOW confidence)
- None - all patterns verified with official sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Already using mcp[cli], patterns verified in SDK
- Architecture: HIGH - Patterns from official docs and SDK issues
- Pitfalls: HIGH - Documented in SDK issues with solutions
- Claude Desktop config: MEDIUM - mcp-remote is community package

**Research date:** 2026-02-04
**Valid until:** 60 days (stable MCP SDK, unlikely to change)
