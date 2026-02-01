# Roadmap: BBj AI Strategy Documentation Site

## Milestones

- v1.0 MVP - Phases 1-5 (shipped 2025-12-01)
- v1.1 Code Corrections & Branding - Phases 6-7 (shipped 2025-12-15)
- v1.2 RAG Ingestion Pipeline - Phases 8-14 (shipped 2026-02-01)
- **v1.3 MCP Architecture Integration** - Phases 15-19 (in progress)

## Phases

<details>
<summary>v1.0 MVP (Phases 1-5) - SHIPPED</summary>

Phase 1: Scaffold & Deploy Pipeline
Phase 2: Content Architecture & Landing Page
Phase 3: Foundation Chapters (Ch1-Ch3)
Phase 4: Execution Chapters (Ch4-Ch7)
Phase 5: Search, SEO & Launch

</details>

<details>
<summary>v1.1 Code Corrections & Branding (Phases 6-7) - SHIPPED</summary>

Phase 6: BBj Code Corrections
Phase 7: Custom Branding

</details>

<details>
<summary>v1.2 RAG Ingestion Pipeline (Phases 8-14) - SHIPPED</summary>

Phase 8: Project Scaffold & README
Phase 9: Schema & Data Models
Phase 10: Flare Parser
Phase 11: BBj Intelligence
Phase 12: Embedding Pipeline
Phase 13: Additional Parsers
Phase 14: Documentation & Quality

</details>

### v1.3 MCP Architecture Integration (In Progress)

**Milestone Goal:** Weave MCP server architecture, compiler validation, and ecosystem integration into existing chapters -- making the concrete "how it all connects" visible to all three audiences.

- [ ] **Phase 15: Strategic Architecture** - Chapter 2 updated with MCP server as the concrete unified architecture
- [ ] **Phase 16: Compiler Validation** - Chapter 4 updated with bbjcpl validation module and proof-of-concept
- [ ] **Phase 17: Chat & Cross-References** - Chapters 5, 3, 6 updated with MCP tool integration and cross-references
- [ ] **Phase 18: Implementation Roadmap** - Chapter 7 updated with MCP deliverables and revised risk assessment
- [ ] **Phase 19: Final Consistency Pass** - Quality verification across all updated chapters

## Phase Details

### Phase 15: Strategic Architecture
**Goal**: Readers of Chapter 2 understand how the MCP server concretely realizes the unified architecture -- three tools, their schemas, and the generate-validate-fix loop
**Depends on**: Nothing (defines MCP vocabulary for all subsequent phases)
**Requirements**: ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05, ARCH-06, ARCH-07, ARCH-08, ARCH-09, ARCH-10
**Success Criteria** (what must be TRUE):
  1. Chapter 2 TL;DR block mentions MCP server, three tools, and generate-validate-fix loop -- a reader skimming gets the key concept in 30 seconds
  2. MCP topology diagram (Host/Client/Server/backends) renders correctly in the live site and communicates the architecture without reading surrounding text
  3. Three MCP tool definitions (`search_bbj_knowledge`, `generate_bbj_code`, `validate_bbj_syntax`) are shown with complete JSON schemas that a developer could implement against
  4. Generate-validate-fix loop sequence diagram shows the compiler feedback cycle as a concrete, repeatable pattern
  5. Decision callout "MCP as the Unified Integration Protocol" follows the established format (Choice, Rationale, Alternatives considered, Status) and frames MCP as evolution, not replacement
**Plans**: TBD

Plans:
- [ ] 15-01: TBD
- [ ] 15-02: TBD

### Phase 16: Compiler Validation
**Goal**: Readers of Chapter 4 understand that BBj's compiler provides ground-truth syntax validation -- and that this is a working, proven pattern (not theoretical)
**Depends on**: Phase 15 (references Ch2's MCP tool definitions and generate-validate-fix vocabulary)
**Requirements**: IDE-01, IDE-02, IDE-03, IDE-04, IDE-05, IDE-06
**Success Criteria** (what must be TRUE):
  1. New "Compiler Validation" section explains bbjcpl concept, error format, and generate-validate-fix loop clearly enough that a developer unfamiliar with BBj understands the value proposition
  2. bbjcpltool proof-of-concept subsection documents what was validated and what it proved -- without exposing implementation details (no file paths, no hook scripts)
  3. Updated architecture diagram shows where compiler validation fits in the IDE completion pipeline (between LLM generation and ghost text presentation)
  4. Decision callout "Compiler Validation via bbjcpl" follows established format and positions this as ground-truth validation (not heuristic)
  5. Chapter status block reflects bbjcpltool v1 shipped and compiler-in-the-loop validated
**Plans**: TBD

Plans:
- [ ] 16-01: TBD
- [ ] 16-02: TBD

### Phase 17: Chat & Cross-References
**Goal**: Chapters 5, 3, and 6 connect to the MCP architecture established in Chapter 2 -- readers following any chapter path encounter consistent MCP integration framing
**Depends on**: Phase 15 (all cross-references point to Ch2's MCP definitions)
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, XREF-01, XREF-02
**Success Criteria** (what must be TRUE):
  1. Chapter 5 presents two tiers for documentation chat: "any MCP client" for quick start and "custom chat backend" for generation-aware UX -- a reader understands both paths
  2. Chapter 5 sequence diagram shows MCP tool calls in the chat flow, replacing or augmenting the existing diagram
  3. Chapter 3 mentions that the fine-tuned model is consumed via MCP `generate_bbj_code` tool and cross-references Chapter 2
  4. Chapter 6 mentions that retrieval is exposed via MCP `search_bbj_knowledge` tool, cross-references Chapter 2, and status reflects v1.2 shipped pipeline
**Plans**: TBD

Plans:
- [ ] 17-01: TBD
- [ ] 17-02: TBD

### Phase 18: Implementation Roadmap
**Goal**: Chapter 7 reflects the current state of the project -- v1.2 accomplishments incorporated, MCP server deliverables woven into phases, compiler validation recognized as hallucination mitigation
**Depends on**: Phases 15, 16, 17 (synthesizes all chapter updates)
**Requirements**: XREF-03, XREF-04
**Success Criteria** (what must be TRUE):
  1. MCP server deliverables appear in the appropriate implementation phases (not as a new top-level phase, but woven into existing ones)
  2. Risk assessment includes compiler validation as a concrete mitigation for the "LLM hallucinates BBj syntax" risk
  3. Status blocks and phase descriptions reflect both v1.2 accomplishments (RAG pipeline shipped) and v1.3 additions (MCP architecture)
**Plans**: TBD

Plans:
- [ ] 18-01: TBD

### Phase 19: Final Consistency Pass
**Goal**: All updated chapters are internally consistent, cross-references resolve, BBj code validates, and the site builds clean
**Depends on**: Phase 18 (all content changes must be complete)
**Requirements**: QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05
**Success Criteria** (what must be TRUE):
  1. All new BBj code samples pass `bbjcpl -N` validation -- no hallucinated syntax in a site that advocates compiler validation
  2. All chapter status blocks (:::note[Where Things Stand]) are updated and internally consistent -- no chapter claims something is "not yet built" when another chapter references it as shipped
  3. Docusaurus build completes with zero broken links and zero warnings
  4. All new decision callouts follow the established format (Choice, Rationale, Alternatives considered, Status)
  5. Landing page chapter descriptions and frontmatter `description` fields match the updated chapter content
**Plans**: TBD

Plans:
- [ ] 19-01: TBD
- [ ] 19-02: TBD

## Progress

**Execution Order:** 15 -> 16 -> 17 -> 18 -> 19

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 15. Strategic Architecture | 0/TBD | Not started | - |
| 16. Compiler Validation | 0/TBD | Not started | - |
| 17. Chat & Cross-References | 0/TBD | Not started | - |
| 18. Implementation Roadmap | 0/TBD | Not started | - |
| 19. Final Consistency Pass | 0/TBD | Not started | - |

---
*Created: 2026-02-01 for milestone v1.3 MCP Architecture Integration*
*Phases continue from v1.2 (ended at Phase 14)*
