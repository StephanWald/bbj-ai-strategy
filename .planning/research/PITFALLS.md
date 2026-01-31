# Domain Pitfalls: RAG Ingestion Pipeline for BBj Technical Documentation

**Domain:** Multi-source RAG ingestion pipeline for niche programming language documentation
**Researched:** 2026-01-31
**Focus:** 5 source types (MadCap Flare XHTML, PDFs, WordPress/LearnPress, Docusaurus MDX, BBj code samples) with generation-aware metadata tagging

---

## Critical Pitfalls

Mistakes that cause rewrites, produce wrong answers, or poison the entire vector store.

### 1. Generation Mistagging Produces Confidently Wrong Answers

**What goes wrong:** A chunk from the Visual PRO/5 era (using `PRINT (sysgui)'WINDOW'(...)` mnemonic syntax) gets tagged as DWC-era, or a DWC chunk (using `BBjWindow::addButton`) gets no generation tag at all. When a developer asks "how do I create a button in BBj DWC?", the RAG returns 1990s Visual PRO/5 syntax with high confidence. The developer copy-pastes it. It fails silently or throws runtime errors that are difficult to debug because the syntax looks plausible.

**Why it happens:**
- BBj spans 4 generations (character UI, Visual PRO/5, BBj GUI/Swing, DWC/browser) and the documentation corpus mixes all of them, often on the same page or in the same PDF
- Vector similarity cannot distinguish between generations because the language patterns are nearly identical across eras -- `sysgui!` appears in both BBj GUI/Swing and DWC code
- Many documentation pages discuss multiple generations for comparison purposes, so naive "one tag per page" approaches fail
- Some concepts (like `OPEN` or `READ`) exist across all 4 generations with subtly different semantics
- The MadCap Flare documentation uses condition tags to single-source content across product versions, but these conditions are stripped in Clean XHTML output and invisible in web crawl output

**Consequences:**
- Developers get syntactically valid but semantically wrong code for their target generation
- Trust in the AI system collapses after a few wrong-generation responses
- The problem is invisible in evaluation unless test queries specifically target generation boundaries
- Fixing mistagged data requires re-processing the entire corpus, not just patching individual chunks

**Prevention:**
- Build a generation classifier as a dedicated pipeline stage, not an afterthought. Every chunk must have a `generation` metadata field with values from an enum: `character_ui`, `visual_pro5`, `bbj_gui_swing`, `dwc_browser`, `cross_generation`, `unknown`
- Use the BBj GUI programming reference PDF (GuideToGuiProgrammingInBBj.pdf) as a Rosetta Stone -- it contains complete working examples across all 4 generations with clear labels. Extract generation-specific API signatures to build classification rules
- Parse MadCap Flare condition tags (before they are stripped) to identify version-targeted content. If using Clean XHTML output, the conditions are already gone -- use the Flare project source instead
- For pages discussing multiple generations, chunk at the generation boundary, not at the section boundary. A section titled "Creating a Window" that shows all 4 approaches should become 4 separate chunks, each with its own generation tag
- At retrieval time, require generation metadata as a filter, not just a boost signal. If the user's context indicates DWC, exclude Visual PRO/5 chunks entirely rather than downranking them
- Build evaluation sets with generation-boundary queries: "How do I create a window in DWC?" must never return Visual PRO/5 syntax, even if the embeddings are similar

**Detection:** Test with 10 queries per generation. If any response contains syntax from the wrong generation, the tagging pipeline is broken.

**Phase:** Must be designed in the schema/architecture phase, implemented during every parser, and validated with evaluation queries before any other feature work.

### 2. MadCap Flare Proprietary Markup Contaminates Chunks

**What goes wrong:** MadCap Flare XHTML contains an extensive proprietary namespace (`xmlns:MadCap="http://www.madcapsoftware.com/Schemas/MadCap.xsd"`) with custom elements and attributes: `MadCap:snippetBlock`, `MadCap:dropDown`, `MadCap:toggler`, `MadCap:keyword`, `MadCap:concept`, `MadCap:conditionalText`, `MadCap:xref`, plus data attributes like `data-mc-target-type`, `MadCap:lastBlockDepth`, `MadCap:lastHeight`, `MadCap:lastWidth`, `MadCap:tocPath`, `MadCap:medium`, `MadCap:RuntimeFileType`. If you parse Flare XHTML with a generic HTML parser (BeautifulSoup, lxml) without removing this namespace, you embed invisible metadata noise into your chunks that dilutes semantic signal and wastes embedding dimensions.

**Why it happens:**
- Two ingestion paths exist: Clean XHTML export (stripping MadCap tags is done by Flare) vs. crawling the live HTML5 site (where Flare-injected JavaScript and `data-mc-*` attributes persist in the DOM)
- Even the Clean XHTML output preserves MadCap-generated CSS classes (prefixed `MC`) that are meaningless outside Flare
- The live HTML5 site at documentation.basis.cloud uses hash-based URLs (`Default.htm#TopicName.htm`) with dynamic content loading via JavaScript, meaning a simple HTTP GET returns a shell page, not the topic content
- The HTML5 output injects navigation chrome (sidebar TOC, breadcrumbs, search UI, top nav bar) that gets scraped alongside actual documentation content
- Drop-downs (`MadCap:dropDown`) are converted to inline text in Clean XHTML but remain JavaScript-driven toggles on the live site -- content inside collapsed dropdowns may not be visible to a scraper

**Consequences:**
- Chunks contain `[MadCap:dropDownHead]Creating a Window[/MadCap:dropDownHead]` instead of "Creating a Window"
- Navigation breadcrumbs like "Home > BBj > API Reference > BBjWindow" appear in chunks, wasting tokens and embedding dimensions
- Collapsed dropdown content is silently missing from crawled output
- CSS class names like `MCDropDownBody` and `MCToggler` appear as text in chunks

**Prevention:**
- Prefer Clean XHTML export over web crawling when Flare project access is available. Clean XHTML removes the MadCap namespace, JavaScript, and most proprietary tags. Document both paths but recommend Clean XHTML as primary
- For Clean XHTML: still strip the generated `MC` CSS class attributes and the `MadCap.css` link. Parse as valid XML (which it is) rather than tag-soup HTML
- For web crawl: use a headless browser (Playwright/Puppeteer) to render JavaScript, expand all dropdowns and togglers before extraction, then extract only from the topic content container (typically `div.body-container` or equivalent), ignoring navigation elements
- Build a Flare-specific content extractor that strips: all `MadCap:*` elements and attributes, all `data-mc-*` attributes, all `mc-*` CSS properties, navigation chrome (TOC sidebar, breadcrumbs, header/footer), MadCap-injected script tags
- Generate a sitemap or enumerate topic files directly from the output directory rather than crawling links, because Flare's hash-based URLs make link-following unreliable
- Validate extraction output: after parsing 10 sample topics, manually inspect that no MadCap markup remains in the extracted text

**Detection:** Search extracted chunks for strings containing "MadCap", "data-mc", or "MCDrop". Any matches indicate incomplete cleanup.

**Phase:** Parser implementation phase. This must be the first parser built, because the Flare documentation is the largest and most complex source.

### 3. PDF Extraction Silently Loses Tables, Code Blocks, and Formatting

**What goes wrong:** PDF extraction using basic libraries (PyPDF2, PyMuPDF, pdfplumber) produces text where code examples are mangled, tables are flattened into nonsensical character sequences, multi-column layouts interleave columns, and headers/footers repeat on every page. The BBj Guide to GUI Programming PDF specifically contains multi-generation code samples, comparison tables, and annotated screenshots -- all of which degrade catastrophically with naive extraction.

**Why it happens:**
- PDFs are a page-layout format, not a semantic format. Text is positioned by coordinates, not by logical structure
- BBj code examples in the GUI programming guide use fixed-width formatting that relies on spatial positioning to convey structure (indentation, alignment of parameters)
- Tables comparing features across BBj generations lose their column associations when extracted as flat text, creating meaningless sequences like "Visual PRO/5 Yes BBj Swing No DWC Yes" without column headers
- Headers and footers ("Guide to GUI Programming in BBj -- Page 47") repeat in extracted text, appearing mid-content between actual documentation paragraphs
- OCR-based approaches introduce character-level errors that are especially damaging for code (`!` becomes `l`, `0` becomes `O`, `|` becomes `l`)
- A 2025 ICCV paper ("OCR Hinders RAG") demonstrated that even small OCR noise levels significantly degrade RAG retrieval accuracy

**Consequences:**
- Code examples in chunks are syntactically broken -- a developer copy-pasting them gets compile errors
- Table data loses column associations, so generation comparison information becomes meaningless noise
- The same header/footer text appears in dozens of chunks, diluting search relevance
- Embedding quality degrades because garbage text reduces the semantic signal-to-noise ratio

**Prevention:**
- Use a layout-aware PDF parser like LlamaParse (rated 10/10 for RAG in 2025 benchmarks), Docling, or the NVIDIA NeMo Retriever extraction pipeline, not PyPDF2/PyMuPDF
- For the BBj GUI programming guide specifically: extract code blocks by detecting monospace font regions and preserving whitespace exactly. Validate extracted code against known-good examples from the Flare documentation
- Strip repeating headers/footers by detecting text that appears in the same position on 3+ consecutive pages
- For tables: use a table-aware extractor that preserves row/column structure, then convert to Markdown table format before chunking. If table extraction fails, flag the table's page range for manual review rather than ingesting garbled text
- Pre-process extracted text: remove page numbers, normalize whitespace, rejoin hyphenated words split across line breaks
- Validate a sample of 5 extracted pages manually before running the full pipeline. If code examples are broken, stop and upgrade the extraction tool

**Detection:** Extract 3 pages containing code examples and 2 pages containing tables. Manually verify the output is syntactically valid and structurally correct.

**Phase:** Parser implementation phase. PDF parsing is the highest-risk extraction and should be prototyped first to validate tool selection.

### 4. Chunking Destroys Code Example Integrity

**What goes wrong:** A recursive text splitter cuts a BBj code example in the middle of a function, a class definition, or a multi-line statement. The resulting chunk contains half a code example that is syntactically invalid and semantically useless. When retrieved, the LLM either hallucinates the completion or produces a response based on an incomplete example.

**Why it happens:**
- Standard text splitters (LangChain's `RecursiveCharacterTextSplitter`, LlamaIndex's `SentenceSplitter`) treat code blocks as regular text and split at character/sentence boundaries
- BBj code examples can be 30-100 lines long (the GUI programming guide has complete programs spanning multiple pages)
- Code examples in documentation are surrounded by explanatory text, so a chunk might contain "the beginning of the explanation + the first half of the code" while the next chunk contains "the second half of the code + the conclusion" -- neither chunk is useful alone
- Overlap between chunks is typically 10-20%, which is not enough to reconstruct a 50-line code example split across chunks

**Consequences:**
- Retrieved code is broken, producing hallucinated completions when the LLM tries to "fix" it
- The explanatory context for code is in one chunk while the code is in another -- retrieval gets one but not the other
- Evaluation shows high recall (the chunks are retrieved) but poor answer quality (the code is broken)

**Prevention:**
- Implement a structure-aware splitter that treats code blocks as atomic units. A code block (fenced with triple backticks or detected via `<pre>`/`<code>` tags) must never be split, even if it exceeds the target chunk size
- If a code block exceeds the chunk size limit, include it as a standalone chunk with its preceding header/description as a prefix
- For BBj specifically, detect code blocks by: fenced code blocks in MDX/Markdown, `<pre>` tags in XHTML, monospace font regions in PDFs, and lines starting with BBj-specific syntax patterns (`REM`, `LET`, `PRINT`, `OPEN`, `sysgui!`, `declare`)
- Use a two-pass chunking approach: first pass identifies and extracts code blocks as protected regions, second pass chunks the surrounding narrative text normally, then reassemble with code blocks attached to their nearest descriptive context
- Set minimum chunk size high enough to accommodate typical code examples with context (400-800 tokens, not 200)
- For the DWC-Course source (Docusaurus MDX with embedded BBj samples), split on Markdown headers first, then on paragraphs, never inside fenced code blocks

**Detection:** After chunking, search for chunks containing ` ``` ` (incomplete code fences) or chunks where code indentation starts mid-block without a function/class declaration. Any matches indicate broken code blocks.

**Phase:** Chunking pipeline implementation. Must be tested with actual BBj code samples from all 5 sources before production ingestion.

### 5. WordPress/LearnPress Content Is Invisible to HTTP Scrapers

**What goes wrong:** The WordPress sites at `basis.cloud/knowledge-base/` (LearnPress LMS) and `basis.cloud/advantage-index/` (magazine articles) render lesson content, course structures, and article bodies via JavaScript. A simple `requests.get()` returns the WordPress page shell with navigation, menus, and footer, but the actual educational content is loaded dynamically via AJAX calls after page load. The scraper appears to succeed (it gets HTML) but the chunks contain only navigation boilerplate.

**Why it happens:**
- LearnPress loads course content, lessons, and quiz content dynamically via JavaScript after the initial page load
- WordPress themes with lazy loading and infinite scroll defer content rendering
- Some Knowledge Base articles may be behind access controls or use WordPress membership features
- Advantage magazine articles use WordPress shortcodes and blocks that resolve to empty containers on the server side
- The WordPress REST API exists but returns raw blocks/shortcodes that require additional processing to extract clean text

**Consequences:**
- Chunks contain "Home | About | Contact | Knowledge Base | Advantage" (navigation) instead of actual documentation content
- The vector store appears populated (correct number of chunks) but contains zero useful content
- This failure is silent -- the pipeline reports success, and the problem only surfaces when retrieval returns irrelevant results

**Prevention:**
- Use a headless browser crawler (Crawl4AI with Playwright, or Scrapy with Splash) that executes JavaScript before extraction, not `requests` + BeautifulSoup
- Configure the crawler to wait for content-specific selectors before extracting (e.g., wait for `.lesson-content` or `.entry-content` to have text content, not just exist in the DOM)
- Strip WordPress chrome: navigation menus, sidebars, footers, cookie banners, comment sections, "Share this" buttons, author bio blocks, breadcrumbs, pagination controls
- For LearnPress specifically: check whether a sitemap or course API endpoint exists that lists all lesson URLs, avoiding the need to discover them via crawling
- For the Advantage index: check whether articles are available as printable/single-page views that avoid JavaScript-dependent rendering
- Validate extraction by comparing total extracted text length against what a human sees in the browser. If extracted text is less than 50% of visible text, the scraper is missing dynamically loaded content
- Consider the WordPress REST API (`/wp-json/wp/v2/posts`, `/wp-json/wp/v2/pages`) as a cleaner extraction path than web scraping, if the API is publicly accessible

**Detection:** For 5 sample URLs, compare `requests.get()` response length against Playwright-rendered page text length. If the Playwright version has 2x+ more text, the static scraper is losing content.

**Phase:** Parser implementation phase. Test the WordPress scraping approach early -- if the REST API is available, it changes the entire extraction strategy.

---

## Moderate Pitfalls

Mistakes that cause inaccurate retrieval, wasted effort, or technical debt that compounds.

### 6. Cross-References Between Documents Become Dead Links in Chunks

**What goes wrong:** The MadCap Flare documentation is heavily cross-referenced -- topics link to other topics via `MadCap:xref` elements and standard hyperlinks. When individual topics are chunked, these cross-references become meaningless text like "See Creating a Window" without the target URL, or worse, they reference a chunk ID that doesn't exist. The LLM has no way to follow the reference, and the retrieval system doesn't know that chunk A's mention of "See Also: BBjWindow Class" means chunk B should also be retrieved.

**Why it happens:**
- Cross-references in Flare output are HTML links with relative paths to other topic files. During chunking, these links are either stripped (losing the connection) or preserved as raw HTML (adding noise)
- The same cross-reference pattern exists in the DWC-Course Docusaurus MDX files (Markdown links to other pages)
- PDF cross-references ("see page 47" or "refer to Chapter 3") lose meaning entirely outside the PDF context

**Prevention:**
- During parsing, convert cross-references to metadata: store `related_chunks: ["bbj_window_class", "creating_controls"]` as metadata on each chunk rather than embedding the link text
- Build a chunk relationship graph that captures explicit cross-references, so that retrieval can expand to related chunks when a cross-reference is detected in a retrieved chunk
- For "See Also" sections, extract the referenced topic titles and store them as metadata for retrieval-time expansion
- Strip the raw hyperlink markup from chunk text but preserve the semantic meaning: "See Creating a Window (BBjWindow class)" becomes "For details on creating windows, see the BBjWindow class documentation."

**Phase:** Chunking and metadata enrichment phase.

### 7. Embedding Model Lock-In Through Hardcoded Dimensions

**What goes wrong:** The pgvector column is defined as `VECTOR(1536)` for OpenAI's text-embedding-3-small, and this dimension is hardcoded throughout the schema, ingestion scripts, and query code. Six months later, the team wants to switch to Voyage AI's voyage-3-large (1536 dimensions but different semantic space) or Cohere embed-v4 (1024 dimensions). Switching requires re-creating the table, re-indexing everything, and updating every query. The entire corpus must be re-embedded, which costs time and money.

**Why it happens:**
- Embedding models are evolving rapidly (the MTEB leaderboard changes quarterly)
- Teams pick the first model that works and hardcode its dimension throughout
- There is no abstraction layer between the embedding model and the storage schema
- The starter kit becomes the production schema, and the hardcoded dimension propagates

**Consequences:**
- Switching embedding models requires full re-ingestion (re-embedding the entire corpus)
- The pgvector HNSW or IVFFlat index must be dropped and rebuilt (which for HNSW can take 30x+ longer than IVFFlat)
- If the new model has different dimensions, the column type must be altered, which in PostgreSQL means rewriting the entire table

**Prevention:**
- Store the embedding model name and version in a metadata table, not just in documentation. Include: `model_name`, `model_version`, `dimensions`, `distance_metric`, `embedding_date`
- Define the vector column dimension as a configuration variable, not a magic number in SQL
- Design the schema to support re-embedding: include a `source_text` column (or reference to it) so that chunks can be re-embedded without re-parsing the source documents
- For the starter kit: use `text-embedding-3-small` (1536d, $0.02/M tokens) as the default because it's the cheapest option for development and prototyping. Document the upgrade path to `text-embedding-3-large` (3072d), Voyage AI `voyage-3-large` (1536d), or Cohere `embed-v4` (1024d) with benchmark data
- Consider Matryoshka representations (supported by OpenAI and Voyage AI): embed at full dimension but store at reduced dimension (e.g., 512d) for the starter kit, with the option to store full dimensions later
- Use cosine similarity consistently (`vector_cosine_ops` in pgvector) as it is the standard metric for all major embedding models

**Phase:** Schema design phase. The dimension and model must be configurable from day one.

### 8. pgvector Index Misconfiguration Kills Query Performance

**What goes wrong:** The pgvector index is created with default parameters, the wrong distance operator, or at the wrong time. Query latency is 10x worse than expected, or recall drops below 90%, or the index silently does nothing because it wasn't analyzed after creation.

**Why it happens:**
- IVFFlat requires data to be present before index creation (it clusters existing vectors). Creating an IVFFlat index on an empty table and then inserting data means the index is useless until rebuilt
- HNSW index creation with default `m=16, ef_construction=64` on a large dataset takes hours and may OOM on a developer's laptop
- Using `vector_l2_ops` (Euclidean distance) when the embedding model is optimized for cosine similarity produces subtly wrong rankings
- Not running `ANALYZE` after IVFFlat index creation means PostgreSQL's query planner doesn't know about the index statistics

**Prevention:**
- For a starter kit (under 50K chunks): start without an index and use exact nearest neighbor search (`<=>` cosine distance without any index). pgvector's exact search is fast enough for small datasets and provides perfect recall. Add an index only when query latency becomes unacceptable
- When adding an index, use HNSW (not IVFFlat) for a RAG system where documents are continuously added. HNSW handles inserts without degradation; IVFFlat's centroids become stale
- Match the distance operator to your similarity metric: `vector_cosine_ops` for cosine similarity, `vector_l2_ops` for Euclidean, `vector_ip_ops` for inner product. All major embedding models use cosine similarity
- If using IVFFlat: only create the index after all initial data is loaded, then run `ANALYZE` on the table. Set `lists` to `sqrt(num_vectors)` as a starting point (e.g., 224 lists for 50K vectors)
- If using HNSW: use `m=16, ef_construction=64` for the starter kit (the defaults are fine for under 100K vectors). Increase `ef_search` at query time to trade latency for recall
- Document the index creation as a separate migration step, not part of the initial schema. This prevents the "empty table index" mistake

**Phase:** Schema design phase (document the plan), then index creation after initial data load.

### 9. Docusaurus MDX Parsing Strips JSX Components and Loses Content

**What goes wrong:** The DWC-Course source (github.com/BasisHub/DWC-Course) is a Docusaurus MDX site with embedded React components, import statements, and JSX syntax interspersed with Markdown. A standard Markdown parser either chokes on the JSX or strips it, losing content that was rendered by those components (interactive examples, tabs showing multiple code variants, admonitions with important warnings).

**Why it happens:**
- MDX is not Markdown. It allows `import` statements, JSX components (`<Tabs>`, `<TabItem>`, custom components), and JavaScript expressions (`{variable}`) inline with Markdown
- A standard Markdown parser (mistune, markdown-it, python-markdown) doesn't understand JSX and will either error or treat it as raw text
- Docusaurus-specific components like `<Tabs>` and `<TabItem>` contain content that is only visible when rendered, not when parsed as text
- Partial MDX files (prefixed with `_`) may be imported into other files, creating content that exists in the partial but is rendered elsewhere

**Prevention:**
- Parse MDX files in two steps: (1) extract and strip all `import` and `export` statements, (2) convert remaining JSX-like tags to their text content. For `<Tabs>` and `<TabItem>`, extract the `label` attribute and the text content within each tab
- Use `gray-matter` (the same library Docusaurus uses) to extract YAML frontmatter, which provides title, description, sidebar_position, and any custom metadata fields
- For content inside JSX components: write a regex or AST-based extractor that unwraps `<ComponentName>content</ComponentName>` to just `content`, preserving the component name as a metadata annotation
- Exclude partial files (`_*.mdx`) from direct ingestion but note that their content appears in the files that import them
- Handle fenced code blocks in MDX carefully: they use triple backtick syntax with optional language identifiers (`\`\`\`bbj`, `\`\`\`java`, `\`\`\`javascript`). The language identifier is valuable metadata for generation tagging

**Phase:** Parser implementation phase for the DWC-Course source.

### 10. No Evaluation Framework Means No Measurable Quality

**What goes wrong:** The pipeline is built, chunks are stored, embeddings are generated, but there is no way to know if retrieval quality is good. The team manually asks a few questions, gets "seems right" responses, and ships. In production, users report wrong answers, but there is no baseline to compare against and no systematic way to measure whether changes improve quality.

**Why it happens:**
- Building evaluation datasets is tedious and seems optional for a starter kit
- "It works on my queries" creates false confidence
- The team focuses on building the pipeline end-to-end rather than measuring quality at each stage
- Without evaluation, there is no feedback loop to improve chunking, embedding, or retrieval strategies

**Prevention:**
- Create a minimum evaluation set of 30 query-answer pairs before building the pipeline. Include:
  - 10 generation-specific queries (e.g., "How to create a window in DWC?" expects DWC syntax, not Visual PRO/5)
  - 10 cross-source queries (e.g., "What is BBjGrid?" should retrieve from both Flare docs and the DWC-Course)
  - 5 "trick" queries that should NOT retrieve certain content (e.g., "How to use BBjGrid?" should NOT return Visual PRO/5 character-mode grid examples)
  - 5 queries about concepts that span multiple chunks (e.g., "What are the deployment options for BBj apps?" requires synthesizing information from multiple sources)
- Measure retrieval quality at the chunk level, not just final answer quality. For each query, record which chunks are retrieved and whether they are relevant (precision) and whether all relevant chunks are retrieved (recall)
- Automate evaluation: run the 30-query test set after every pipeline change and track metrics over time
- This evaluation set doubles as documentation for what the RAG system is expected to do

**Phase:** Design phase (create the evaluation set), then automated after pipeline is functional.

---

## Minor Pitfalls

Mistakes that cause friction, wasted debugging time, or suboptimal quality but are fixable without rework.

### 11. Flare Clean XHTML Export Includes All Topics, Not Just TOC-Selected Ones

**What goes wrong:** When generating Clean XHTML output from Flare, even with a TOC that includes only a subset of topics, Flare exports ALL topics in the project. The ingestion pipeline processes hundreds of topics that were intentionally excluded from the documentation, including drafts, deprecated content, internal notes, and test topics.

**Prevention:** After Clean XHTML export, filter topics against the TOC file (an XML file mapping topic hierarchy). Only ingest topics that appear in the TOC. Alternatively, use Flare's condition tags to exclude internal content, but verify that the condition expressions in the Clean XHTML target are correctly configured.

**Phase:** Flare parser implementation.

### 12. Duplicate Content Across Sources Inflates the Index

**What goes wrong:** The same BBj API reference content appears in the MadCap Flare documentation, the DWC-Course, and PDF guides. Without deduplication, the same concept is embedded 3 times, wasting storage and retrieval slots. Worse, the duplicates may have slight differences (different wording, different generation context), causing conflicting retrieved chunks.

**Prevention:**
- Implement content fingerprinting (hash the normalized text of each chunk) to detect near-duplicates during ingestion
- When duplicates are detected from multiple sources, prefer the source with the most authoritative/complete version and tag it with `sources: ["flare", "dwc-course"]` metadata
- At minimum, deduplicate within each source (e.g., the same Flare topic appearing in multiple output folders)

**Phase:** Post-chunking deduplication step in the pipeline.

### 13. WordPress Rate Limiting or Blocking During Crawl

**What goes wrong:** Crawling `basis.cloud/knowledge-base/` and `basis.cloud/advantage-index/` too aggressively triggers WordPress rate limiting, Cloudflare protection, or the hosting provider's bot detection. The crawler gets blocked partway through, producing an incomplete corpus. Or worse, it gets soft-blocked (returns CAPTCHAs or redirect loops) and the pipeline treats the error pages as content.

**Prevention:**
- Respect `robots.txt` and add a 1-2 second delay between requests
- Set a realistic User-Agent string (not the default `python-requests/2.x`)
- Prefer the WordPress REST API (`/wp-json/wp/v2/`) over web scraping if the API is publicly accessible -- it is not affected by bot detection
- Check response status codes and page content before processing -- a 200 response containing "Please verify you are human" is not valid content
- Use a sitemap (`/sitemap.xml` or `/sitemap_index.xml`) to enumerate URLs rather than recursive link-following

**Phase:** WordPress parser implementation.

### 14. BBj Code Samples Lack Language Identification

**What goes wrong:** BBj code samples embedded in Markdown and XHTML are not consistently tagged with a language identifier. Some use ` ```bbj `, some use ` ```basic `, some use ` ``` ` with no language, and some are inline code that happens to be BBj. The chunking pipeline cannot reliably identify which text blocks are BBj code versus regular prose or other languages (Java, JavaScript, SQL) that also appear in the documentation.

**Prevention:**
- Build a BBj code detector that identifies BBj syntax patterns: `REM` comments, `LET` assignments, `PRINT` statements, `OPEN` channels, `sysgui!` object references, `declare BBj*` type declarations, `CALLBACK` event handlers, numbered line labels (e.g., `0100`), and the `!` suffix on object variable names
- When a code block has no language identifier, run the detector and add the language tag to the chunk metadata
- Distinguish BBj from other BASIC dialects (the documentation may reference generic Business BASIC concepts) -- BBj-specific indicators include `BBj` class names, `DWC` references, and `sysgui!`/`syspri!`/`sysstr!` system objects

**Phase:** Chunking pipeline implementation, as a post-processing step on extracted code blocks.

### 15. Flare Dropdown and Toggler Content Gets Concatenated Without Structure

**What goes wrong:** In Clean XHTML output, MadCap Flare converts dropdown and toggler elements (which are interactive on the live site) to inline text. A dropdown titled "BBj Code Example" with content spanning 30 lines appears as a flat block of text with no visual or structural separator between the dropdown title and the dropdown content. The chunker treats it as continuous prose and may split the dropdown title from its content.

**Prevention:**
- In the Flare parser, detect patterns where dropdown titles (from the `MCDropDownHead` class, or text that was formerly `MadCap:dropDownHead`) precede dropdown bodies. Insert Markdown headers or separator markers to preserve the structural boundary
- Treat each dropdown body as a potential chunk boundary -- it is a self-contained unit of content

**Phase:** Flare parser implementation.

### 16. Ignoring Document Recency Causes Stale Answers

**What goes wrong:** The corpus includes documentation from 2007 (the GUI programming PDF), 2015 (older Flare topics), and 2025 (recent DWC-Course updates). Without recency metadata, a query about "current best practice" may retrieve a 2007 recommendation that has been superseded.

**Prevention:**
- Extract and store `last_modified` metadata for every chunk. Sources:
  - Flare topics: look for `MadCap:lastBlockDepth`/`MadCap:lastHeight` attributes (present in source XHTML) or file modification dates
  - PDFs: extract creation/modification date from PDF metadata
  - WordPress: use the `modified` field from the REST API or the page's published/updated date
  - DWC-Course: use git commit dates for each file
- At retrieval time, provide recency as a boost signal (not a hard filter, since older content may be the only source for legacy generation questions)

**Phase:** Metadata enrichment phase.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Schema design | Hardcoded embedding dimensions (Pitfall 7) | Make dimension configurable, store model metadata |
| Schema design | No evaluation framework planned (Pitfall 10) | Create 30-query eval set before writing any parser code |
| Flare parser | Proprietary markup contamination (Pitfall 2) | Build Flare-specific extractor, validate against 10 sample topics |
| Flare parser | All topics exported regardless of TOC (Pitfall 11) | Filter against TOC XML, exclude drafts and deprecated content |
| Flare parser | Dropdown content loses structure (Pitfall 15) | Detect and re-structure dropdown patterns |
| PDF parser | Tables and code blocks destroyed (Pitfall 3) | Use layout-aware parser (LlamaParse), validate code extraction |
| WordPress parser | Content invisible to HTTP scraper (Pitfall 5) | Use headless browser or REST API, validate against visible content |
| WordPress parser | Rate limiting blocks crawler (Pitfall 13) | Throttle requests, prefer REST API, check robots.txt |
| MDX parser | JSX components stripped (Pitfall 9) | Two-step parse: strip imports, unwrap JSX to text content |
| Chunking pipeline | Code examples split mid-block (Pitfall 4) | Structure-aware splitter with code block protection |
| Chunking pipeline | No language identification (Pitfall 14) | BBj syntax pattern detector as post-processing |
| Metadata enrichment | Generation mistagging (Pitfall 1) | Dedicated generation classifier, per-chunk tagging, eval queries |
| Metadata enrichment | Cross-references lost (Pitfall 6) | Convert links to metadata, build chunk relationship graph |
| Metadata enrichment | No recency metadata (Pitfall 16) | Extract dates from all source types |
| Embedding & storage | Model lock-in (Pitfall 7) | Config-driven dimensions, store source text for re-embedding |
| Embedding & storage | Index misconfiguration (Pitfall 8) | Start without index, add HNSW after initial load, match distance ops |
| Deduplication | Cross-source duplicates (Pitfall 12) | Content fingerprinting, prefer authoritative source |

---

## Sources

### MadCap Flare
- [Clean XHTML Output in MadCap Flare 2017](https://www.madcapsoftware.com/blog/2017/02/21/new-feature-highlight-clean-xhtml-output-madcap-flare-2017/) -- Clean XHTML stripping behavior (HIGH confidence)
- [About Clean XHTML Output (Flare 2017r3)](https://help.madcapsoftware.com/flare2017r3/Content/Flare/Output/Clean-XHTML/About-Clean-XHTML-Output.htm) -- What gets stripped vs preserved (HIGH confidence)
- [Clean XHTML Scope Issue (Forum)](https://forums.madcapsoftware.com/viewtopic.php?f=9&t=30269) -- All topics published regardless of TOC (MEDIUM confidence)
- [Flare XHTML vs HTML Discussion (Forum)](https://forums.madcapsoftware.com/viewtopic.php?f=75&t=13021) -- Proprietary namespace "detritus" (MEDIUM confidence)
- [Advanced Condition Tags and Single Sourcing](https://www.madcapsoftware.com/webinars/advanced-use-of-condition-tags-single-sourcing-in-madcap-flare) -- Condition-based versioning (HIGH confidence)
- [HTML5 Output and Search Crawlers (Forum)](https://forums.madcapsoftware.com/viewtopic.php?t=30021) -- Hash-based URLs, crawling limitations (MEDIUM confidence)

### PDF Extraction
- [Fix RAG Hallucinations: Top PDF Parsers Ranked 2025 (Medium)](https://infinityai.medium.com/3-proven-techniques-to-accurately-parse-your-pdfs-2c01c5badb84) -- LlamaParse 10/10, Unstructured degraded (MEDIUM confidence)
- [OCR Hinders RAG (ICCV 2025)](https://openaccess.thecvf.com/content/ICCV2025/papers/Zhang_OCR_Hinders_RAG_Evaluating_the_Cascading_Impact_of_OCR_on_ICCV_2025_paper.pdf) -- OCR noise cascades into retrieval degradation (HIGH confidence)
- [Approaches to PDF Data Extraction (NVIDIA)](https://developer.nvidia.com/blog/approaches-to-pdf-data-extraction-for-information-retrieval/) -- Specialized pipeline beats VLM for retrieval (HIGH confidence)

### RAG Pipeline Best Practices
- [If I Had to Build a RAG Pipeline Today (Medium, Dec 2025)](https://medium.com/@faryalriz9/if-i-had-to-build-a-rag-pipeline-today-id-do-it-this-way-2080c4ab0b69) -- Chunking > model selection, evaluation early (MEDIUM confidence)
- [RAG is a Data Problem (HackerNoon)](https://hackernoon.com/rag-is-a-data-problem-pretending-to-be-ai) -- Data quality determines RAG quality ceiling (MEDIUM confidence)
- [Data Ingestion for RAG (IBM)](https://www.ibm.com/architectures/papers/rag-cookbook/data-ingestion) -- Complex format handling (HIGH confidence)
- [23 RAG Pitfalls and How to Fix Them (NB Data)](https://www.nb-data.com/p/23-rag-pitfalls-and-how-to-fix-them) -- Comprehensive pitfall catalog (MEDIUM confidence)

### Chunking
- [Best Chunking Strategies for RAG 2025 (Firecrawl)](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025) -- 400-token chunks, 10-20% overlap (MEDIUM confidence)
- [Optimizing RAG Context for Technical Docs (DEV Community)](https://dev.to/oleh-halytskyi/optimizing-rag-context-chunking-and-summarization-for-technical-docs-3pel) -- Preserving code blocks, custom splitter (MEDIUM confidence)
- [Code Chunking with AST (EMNLP 2025)](https://aclanthology.org/2025.findings-emnlp.430.pdf) -- AST-based chunking for code RAG (HIGH confidence)
- [Mastering Code Chunking for RAG (Medium)](https://medium.com/@joe_30979/mastering-code-chunking-for-retrieval-augmented-generation-66660397d0e0) -- Code block integrity (MEDIUM confidence)

### Metadata and Versioning
- [RAG Failure Modes (Snorkel AI)](https://snorkel.ai/blog/retrieval-augmented-generation-rag-failure-modes-and-how-to-fix-them/) -- Version confusion, stale data (HIGH confidence)
- [Metadata for RAG (Unstructured)](https://unstructured.io/insights/how-to-use-metadata-in-rag-for-better-contextual-results) -- Metadata filtering improves retrieval accuracy (MEDIUM confidence)
- [Advanced Metadata Filtering (NVIDIA RAG Blueprint)](https://docs.nvidia.com/rag/2.3.0/custom-metadata.html) -- Natural language filter generation for multi-version docs (HIGH confidence)

### pgvector
- [pgvector HNSW vs IVFFlat (AWS Blog)](https://aws.amazon.com/blogs/database/optimize-generative-ai-applications-with-pgvector-indexing-a-deep-dive-into-ivfflat-and-hnsw-techniques/) -- Index comparison, when to use each (HIGH confidence)
- [Debunking pgvector Myths (Nile)](https://www.thenile.dev/blog/pgvector_myth_debunking) -- Index not always needed, distance operator matching (HIGH confidence)
- [pgvector GitHub](https://github.com/pgvector/pgvector) -- Official documentation, HNSW parallel builds in 0.7.0 (HIGH confidence)

### Embedding Models
- [Top Embedding Models 2026 (Elephas)](https://elephas.app/blog/best-embedding-models) -- MTEB rankings, pricing, dimension comparison (MEDIUM confidence)
- [Embedding Models Compared (Document360)](https://document360.com/blog/text-embedding-model-analysis/) -- Vendor dimension differences (MEDIUM confidence)
- [Embedding Models in 2026 (AIMultiple)](https://research.aimultiple.com/embedding-models/) -- Cohere embed-v4, OpenAI, Voyage comparison (MEDIUM confidence)

### WordPress/Web Crawling
- [Crawl4AI for LLM Pipelines](https://www.blog.brightcoding.dev/2025/05/03/open-source-tool-for-web-crawling-scraping-and-data-extraction-for-llms-and-ai-pipelines/) -- JavaScript rendering, markdown output (MEDIUM confidence)
- [Web Scraping for RAG (Scrapfly)](https://scrapfly.io/blog/posts/how-to-use-web-scaping-for-rag-applications) -- Irrelevant chrome, authentication handling (MEDIUM confidence)

### Cross-References
- [Better RAG Using Links (Medium)](https://medium.com/data-science/your-documents-are-trying-to-tell-you-whats-relevant-better-rag-using-links-386b7433d0f2) -- Linked documents model for cross-references (MEDIUM confidence)
- [Why RAG Fails on Technical Documents (Medium, Jan 2026)](https://medium.com/@officialchiragp1605/why-your-rag-system-fails-on-technical-documents-and-how-to-fix-it-5c9e5be7948f) -- Hierarchy-aware parsing, structure preservation (MEDIUM confidence)

### BBj Language
- [BBj Changes from Earlier Versions](https://documentation.basis.cloud/BASISHelp/WebHelp/usr/BBj_Enhancements/bbj_bbx_differences.htm) -- Cross-generation syntax differences (HIGH confidence)
- [BBj VS Code Extension](https://marketplace.visualstudio.com/items?itemName=BEU.bbj-vscode) -- Language support exists but limited (MEDIUM confidence)
- [Guide to GUI Programming in BBj](https://documentation.basis.cloud/WhitePapers/GuideToGuiProgrammingInBBj.pdf) -- Authoritative cross-generation code reference (HIGH confidence)

---

*Research completed: 2026-01-31*
*Confidence: HIGH for MadCap Flare and pgvector pitfalls (verified with official docs), MEDIUM for WordPress/PDF extraction (verified with multiple sources), MEDIUM for generation tagging (domain-specific extrapolation from version management research)*
