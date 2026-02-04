# Phase 27: Remote Access - Context

**Gathered:** 2026-02-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Enable engineers on the local network to access the RAG system (chat UI + MCP server) from their own machines without running Docker locally. This includes Streamable HTTP MCP for Claude Desktop and network-accessible web interface.

</domain>

<decisions>
## Implementation Decisions

### Deployment Topology
- Support both shared server and per-engineer local setups
- Self-serve documentation for whoever wants to host a shared server (no designated admin)
- Single docker-compose.yml with profiles (not separate files)
- Per-engineer local setup requires their own Anthropic API key (bring your own key)

### MCP Transport
- Streamable HTTP only (no SSE fallback)
- No authentication for alpha (LAN trust model)
- Document troubleshooting steps for connection failures
- "Latest Claude Desktop" — no specific version pinning required

### Network Exposure
- Single port (10800) for everything — web, MCP, and API
- Basic firewall note only ("ensure port 10800 is accessible")
- Engineers know the server IP — no discovery instructions needed
- Docker-only verification (verify 0.0.0.0 binding, assume network works)

### Configuration Management
- Default behavior (no profile) binds to 0.0.0.0 (shared mode by default)
- Deployment instructions in main README.md (not separate doc)
- Include copy-paste Claude Desktop config snippet for remote MCP

### Claude's Discretion
- Profile name for compose (if profiles are even needed given shared default)
- Exact troubleshooting steps for MCP connection issues
- README section organization and formatting

</decisions>

<specifics>
## Specific Ideas

- Shared default (0.0.0.0) means simpler setup — just `docker compose up` works for both local and shared
- Copy-paste Claude Desktop config example reduces friction for engineers connecting

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 27-remote-access*
*Context gathered: 2026-02-04*
