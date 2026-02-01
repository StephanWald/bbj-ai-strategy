# Requirements: v1.3 MCP Architecture Integration

## Strategic Architecture (Chapter 2)

- [x] **ARCH-01**: Chapter 2 TL;DR block updated to mention MCP server, three tools, and generate-validate-fix loop
- [x] **ARCH-02**: MCP server introduced as concrete realization of existing unified architecture (not a replacement — evolution of the two-layer model)
- [x] **ARCH-03**: Updated architecture diagram showing MCP topology (Host → Client → BBj MCP Server → RAG/Ollama/bbjcpl)
- [x] **ARCH-04**: Three MCP tool definitions with JSON schemas: `search_bbj_knowledge`, `generate_bbj_code`, `validate_bbj_syntax`
- [x] **ARCH-05**: Generate-validate-fix loop pattern described with sequence diagram
- [x] **ARCH-06**: Deployment options documented (local stdio for privacy, remote Streamable HTTP for team sharing)
- [x] **ARCH-07**: webforJ MCP server referenced as organizational precedent (one callout, not belabored)
- [x] **ARCH-08**: Named integration patterns: Generate-Validate-Fix, Documentation Query, Code Review/Migration
- [x] **ARCH-09**: Decision callout: "Decision: MCP as the Unified Integration Protocol" using existing :::info format
- [x] **ARCH-10**: Current Status block updated to reflect v1.2 RAG pipeline shipped and v1.3 MCP architecture

## IDE Integration & Compiler Validation (Chapter 4)

- [x] **IDE-01**: New section "Compiler Validation: Ground-Truth Syntax Checking" covering bbjcpl concept, error format, generate-validate-fix loop
- [x] **IDE-02**: bbjcpltool proof-of-concept subsection documenting concept validated, not implementation details (no file paths, no hook scripts)
- [x] **IDE-03**: MCP integration note — BBj tools work in any MCP-enabled host (Claude, Cursor, VS Code), not just custom extension
- [x] **IDE-04**: Updated architecture diagram showing compiler validation in the completion pipeline
- [x] **IDE-05**: Decision callout: "Decision: Compiler Validation via bbjcpl" using existing :::info format
- [x] **IDE-06**: Current Status block updated to reflect bbjcpltool v1 shipped and compiler-in-the-loop validated

## Documentation Chat (Chapter 5)

- [x] **CHAT-01**: MCP-based architecture framing — chat backend as MCP client, `search_bbj_knowledge` tool for retrieval
- [x] **CHAT-02**: Two-tier presentation: "Quick start: any MCP client" for immediate access, "Optimized: custom chat backend" for generation-aware UX
- [x] **CHAT-03**: Updated sequence diagram showing MCP tool calls in the chat flow
- [x] **CHAT-04**: Decision callout: "Decision: MCP Tool for RAG Access" using existing :::info format
- [x] **CHAT-05**: Current Status block updated

## Cross-References & Updates (Chapters 3, 6, 7)

- [x] **XREF-01**: Chapter 3 (Fine-Tuning) — brief mention that model is consumed via MCP `generate_bbj_code` tool, cross-reference to Ch2
- [x] **XREF-02**: Chapter 6 (RAG Database) — mention retrieval exposed via MCP `search_bbj_knowledge` tool, cross-reference to Ch2, status updated for v1.2 shipped pipeline
- [x] **XREF-03**: Chapter 7 (Implementation Roadmap) — MCP server deliverables woven into existing phases, risk assessment updated with compiler validation as hallucination mitigation
- [x] **XREF-04**: Chapter 7 — status blocks and phase descriptions updated to reflect v1.2 accomplishments and v1.3 MCP additions

## Quality & Consistency

- [x] **QUAL-01**: All new BBj code samples validated via `bbjcpl -N` before publishing
- [x] **QUAL-02**: All chapter status blocks (:::note[Where Things Stand]) updated in coordinated pass — reflect v1.2 shipped RAG pipeline and v1.3 MCP architecture
- [x] **QUAL-03**: Cross-reference verification — all inter-chapter links verified via Docusaurus build (no broken links)
- [x] **QUAL-04**: Landing page chapter descriptions and frontmatter `description` fields updated where chapter content changed
- [x] **QUAL-05**: Decision callout consistency — all new :::info[Decision:] callouts have Choice, Rationale, Alternatives considered, Status fields

## Future Requirements (Deferred)

- MCP server source code implementation — this milestone documents the architecture, a future milestone builds it
- MCP SDK language decision (TypeScript vs Python) — premature for strategy documentation
- MCP Resources and Prompts primitives — only Tools are defined in the concept; Resources/Prompts are future expansion
- Multi-agent orchestration patterns — not part of the BBj strategy
- Embedding fine-tuning — requires baseline retrieval quality measurement first

## Out of Scope

- Standalone Chapter 8 for MCP — MCP is woven into existing chapters per PROJECT.md decision
- MCP protocol tutorial — site documents BBj strategy, not MCP itself; link to official docs
- Server source code or installation guides — strategy docs explain WHAT and WHY, not HOW to install
- JSON-RPC protocol internals — mentioned once as a fact, not explained
- Security/auth implementation details — acknowledged as deployment consideration, not designed
- Agentic RAG features — no query routing, agent loops, or multi-step reasoning

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ARCH-01 | Phase 15 | Complete |
| ARCH-02 | Phase 15 | Complete |
| ARCH-03 | Phase 15 | Complete |
| ARCH-04 | Phase 15 | Complete |
| ARCH-05 | Phase 15 | Complete |
| ARCH-06 | Phase 15 | Complete |
| ARCH-07 | Phase 15 | Complete |
| ARCH-08 | Phase 15 | Complete |
| ARCH-09 | Phase 15 | Complete |
| ARCH-10 | Phase 15 | Complete |
| IDE-01 | Phase 16 | Complete |
| IDE-02 | Phase 16 | Complete |
| IDE-03 | Phase 16 | Complete |
| IDE-04 | Phase 16 | Complete |
| IDE-05 | Phase 16 | Complete |
| IDE-06 | Phase 16 | Complete |
| CHAT-01 | Phase 17 | Complete |
| CHAT-02 | Phase 17 | Complete |
| CHAT-03 | Phase 17 | Complete |
| CHAT-04 | Phase 17 | Complete |
| CHAT-05 | Phase 17 | Complete |
| XREF-01 | Phase 17 | Complete |
| XREF-02 | Phase 17 | Complete |
| XREF-03 | Phase 18 | Complete |
| XREF-04 | Phase 18 | Complete |
| QUAL-01 | Phase 19 | Complete |
| QUAL-02 | Phase 19 | Complete |
| QUAL-03 | Phase 19 | Complete |
| QUAL-04 | Phase 19 | Complete |
| QUAL-05 | Phase 19 | Complete |

---
*Created: 2026-02-01 for milestone v1.3 MCP Architecture Integration*
*Updated: 2026-02-01 — Phase mappings added from roadmap*
