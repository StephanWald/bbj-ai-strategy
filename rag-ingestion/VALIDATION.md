# End-to-End Validation Report

**Generated:** 2026-02-02 21:37 UTC
**Status:** FAIL (13/17 queries passed)

## Corpus Stats

| Metric | Value |
|--------|-------|
| Total chunks | 50,392 |
| doc_type: flare | 44,587 |
| doc_type: concept | 2,950 |
| doc_type: article | 1,798 |
| doc_type: tutorial | 951 |
| doc_type: example | 106 |
| generation: bbj | 48,263 |
| generation: dwc | 984 |
| generation: deprecated | 893 |
| generation: superseded | 166 |
| generation: not_implemented | 102 |
| generation: em | 64 |
| generation: bbj_gui | 43 |
| generation: all | 30 |
| generation: bdt | 2 |

## Source-Targeted Queries

### Query 1: BBjWindow addButton method

- **Result:** PASS
- **Reason:** top result from Flare
- **Source:** `flare://Content/bbjobjects/Window/bbjbutton/BBjButton.htm`
- **Title:** BBjButton Methods
- **Score:** 0.0381
- **Snippet:** bbjobjects > Window > bbjbutton > BBjButton Methods > Creation ## Creation `BBjAPI > BBjSysGui > BBjWindow > BBjButton` A BBjButton object is...

### Query 2: customer information program BBj GUI example

- **Result:** FAIL
- **Reason:** top result source_url 'https://documentation.basis.cloud/advantage/v12-2008/clientobject.pdf' does not start with 'pdf://'
- **Source:** `https://documentation.basis.cloud/advantage/v12-2008/clientobject.pdf`
- **Title:** clientobject
- **Score:** 0.0196
- **Snippet:** clientobject > Blowing the Doors Wide Open With ClientObjects ## Blowing the Doors Wide Open With ClientObjects _**By David Wallwork**_ Bj [®]...

### Query 3: DWC web component tutorial getting started

- **Result:** PASS
- **Reason:** top result from MDX
- **Source:** `mdx-dwc://resources.md`
- **Title:** Useful Resource Links
- **Score:** 0.0196
- **Snippet:** Useful Resource Links > DWC Component Reference ## DWC Component Reference - **[dwc.style](https://dwc.style/)** - The official DWC component...

### Query 4: BBj sample source code PROCESS_EVENTS

- **Result:** FAIL
- **Reason:** top result source_url 'https://documentation.basis.cloud/advantage/v11-2007/dragdrop.pdf' does not start with 'file://'
- **Source:** `https://documentation.basis.cloud/advantage/v11-2007/dragdrop.pdf`
- **Title:** dragdrop
- **Score:** 0.0196
- **Snippet:** dragdrop The Drag and Drop Events Example includes a more complex event handler for dragging and dropping between arbitrary controls....

### Query 5: Advantage magazine BBj article

- **Result:** FAIL
- **Reason:** top result source_url 'flare://Content/util/autolic_util_auto_register_and_install_licenses_bbj.htm' does not start with 'https://basis.cloud/'
- **Source:** `flare://Content/util/autolic_util_auto_register_and_install_licenses_bbj.htm`
- **Title:** autolic Utility - Automatically Register and Install Licenses BBj
- **Score:** 0.0196
- **Snippet:** util > autolic Utility - Automatically Register and Install Licenses BBj > BBj-Specific Information ## BBj-Specific Information

### Query 6: documentation.basis.cloud BBj reference

- **Result:** FAIL
- **Reason:** top result source_url 'flare://Content/util/autolic_util_auto_register_and_install_licenses_bbj.htm' does not start with 'https://documentation.basis.cloud/'
- **Source:** `flare://Content/util/autolic_util_auto_register_and_install_licenses_bbj.htm`
- **Title:** autolic Utility - Automatically Register and Install Licenses BBj
- **Score:** 0.0196
- **Snippet:** util > autolic Utility - Automatically Register and Install Licenses BBj > BBj-Specific Information ## BBj-Specific Information

## Topic-Based Queries

### Query 1: How do I create a BBjGrid?

- **Result:** PASS
- **Reason:** keyword match in top result
- **Source:** `flare://Content/gridmethods/bbjgrid/BBjGrid.htm`
- **Title:** BBjGrid Methods
- **Score:** 0.0196
- **Snippet:** gridmethods > bbjgrid > BBjGrid Methods # BBjGrid

### Query 2: BBj string manipulation functions

- **Result:** PASS
- **Reason:** keyword match in top result
- **Source:** `flare://Content/bbjobjects/API/bbjstring/BBjString.htm`
- **Title:** BBjString Methods
- **Score:** 0.0196
- **Snippet:** bbjobjects > API > bbjstring > BBjString Methods # BBjString

### Query 3: DWC web component styling CSS

- **Result:** PASS
- **Reason:** keyword match in top result
- **Source:** `mdx-dwc://02-browser-developer-tools/03-css-custom-properties.md`
- **Title:** CSS Styles and CSS Custom Properties
- **Score:** 0.0377
- **Snippet:** CSS Styles and CSS Custom Properties > DWC vs BUI ### DWC vs BUI The DWC implements BBj controls using web components with shadow DOMs: **DWC...

### Query 4: BBj database connection SQL

- **Result:** PASS
- **Reason:** keyword match in top result
- **Source:** `mdx-beginner://08-database-sql/01-connecting.md`
- **Title:** Connecting to Databases
- **Score:** 0.0348
- **Snippet:** Connecting to Databases # Connecting to Databases Every SQL operation in BBj starts with `SQLOPEN`, which opens a channel to a database. BBj...

### Query 5: Event handling callbacks in BBj

- **Result:** PASS
- **Reason:** keyword match in top result
- **Source:** `mdx-beginner://01-introduction/translation-tables.md`
- **Title:** BBj for Java, Python, and C# Developers
- **Score:** 0.0359
- **Snippet:** BBj for Java, Python, and C# Developers > Events and Callbacks ## Events and Callbacks | Task | Java | Python | C# | BBj |...

### Query 6: BBj file I/O operations

- **Result:** PASS
- **Reason:** keyword match in top result
- **Source:** `mdx-beginner://07-file-io/index.md`
- **Title:** File I/O and Record Access
- **Score:** 0.0196
- **Snippet:** File I/O and Record Access > Practical Example: Customer File Operations ## Practical Example: Customer File Operations ```bbj REM ===== Customer...

### Query 7: Migration from Visual PRO/5 to BBj

- **Result:** PASS
- **Reason:** keyword match in top result
- **Source:** `https://basis.cloud/knowledge-base/kb01220/`
- **Title:** 01220: Live Migration Cron Job Script for Virtual Licensing - BASIS International Ltd
- **Score:** 0.0317
- **Snippet:** 01220: Live Migration Cron Job Script for Virtual Licensing - BASIS International Ltd - FAQsKB - Possible issue in Desktop Apps after Windows...

## Generation-Filtered Query

### Query: DWC web component styling CSS (generation=dwc)

- **Result:** PASS
- **Reason:** keyword match in top result
- **Source:** `mdx-dwc://02-browser-developer-tools/03-css-custom-properties.md`
- **Title:** CSS Styles and CSS Custom Properties
- **Score:** 0.0381
- **Snippet:** CSS Styles and CSS Custom Properties > Concepts Covered in This Section ## Concepts Covered in This Section - The DWC's CSS custom properties - The...

## MCP Validation

### Query M1: BBjWindow addButton method

- **Result:** PASS
- **Response preview:** Found 5 results for: BBjWindow addButton method  ## Result 1: BBjButton Methods *bbjobjects > Window > bbjbutton > BBjButton Methods > Creation*  bbjobjects > Window > bbjbutton > BBjButton Methods >

### Query M2: How do I create a BBjGrid?

- **Result:** PASS
- **Response preview:** Found 5 results for: How do I create a BBjGrid?  ## Result 1: BBjGrid Methods *gridmethods > bbjgrid > BBjGrid Methods*  gridmethods > bbjgrid > BBjGrid Methods  # BBjGrid  Source: flare://Content/gri

### Query M3: Event handling callbacks in BBj

- **Result:** PASS
- **Response preview:** Found 5 results for: Event handling callbacks in BBj  ## Result 1: BBj for Java, Python, and C# Developers *BBj for Java, Python, and C# Developers > Events and Callbacks*  BBj for Java, Python, and C

## Cross-Source Summary

| Source Group | Expected Prefix | Found in Results |
|-------------|-----------------|-----------------|
| Flare | `flare://` | Yes |
| PDF | `pdf://` | No |
| MDX | `mdx-` | Yes |
| BBj Source | `file://` | No |
| WordPress | `https://basis.cloud/` | Yes |
| Web Crawl | `https://documentation.basis.cloud/` | Yes |

## Known Issues

### REST API Failures

- **customer information program BBj GUI example** (source-targeted): top result source_url 'https://documentation.basis.cloud/advantage/v12-2008/clientobject.pdf' does not start with 'pdf://'
- **BBj sample source code PROCESS_EVENTS** (source-targeted): top result source_url 'https://documentation.basis.cloud/advantage/v11-2007/dragdrop.pdf' does not start with 'file://'
- **Advantage magazine BBj article** (source-targeted): top result source_url 'flare://Content/util/autolic_util_auto_register_and_install_licenses_bbj.htm' does not start with 'https://basis.cloud/'
- **documentation.basis.cloud BBj reference** (source-targeted): top result source_url 'flare://Content/util/autolic_util_auto_register_and_install_licenses_bbj.htm' does not start with 'https://documentation.basis.cloud/'

### Missing Source Groups

- **PDF** (`pdf://`): no results found across any query
- **BBj Source** (`file://`): no results found across any query
