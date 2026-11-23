# Independent Research Quality & Provenance Audit
## Stage 2 Pilot Investigation Audit: 5 Representative SaaS Applications

**Auditor Role:** Independent AI Research Quality & Systems Provenance Auditor  
**Date of Audit:** November 23, 2026  
**Scope of Audit:** 5 Pilot Records (`salesforce`, `github`, `shopify`, `sherlock`, `notebooklm`) generated in `data/results/initial_research.json` and `data/results/individual/`.  
**System Under Test:** Integration Intelligence Autonomous Research Harness (v2.0.0).  

---

### Executive Summary & Verdict

This independent audit evaluated whether the research results generated in Stage 2 contain genuine, externally verified research. 

#### Critical Audit Finding:
1. **Zero Live Network Retrieval (`0% LIVE_FETCHED`)**:
   Due to execution within the sandboxed runtime and default initialization to `MockSearchProvider` and `DocumentFetcher.KNOWLEDGE_BASE`, **no external HTTP network requests were successfully resolved**. 100% of the textual evidence and claims originated from an internal hardcoded dictionary (`DocumentFetcher.KNOWLEDGE_BASE`) and pre-mapped search references (`MockSearchProvider.KNOWN_URL_MAPPINGS`).
2. **False Positives from Negated Text**:
   The regex-based evidence extraction mechanism in `EvidenceExtractor` lacks syntactic negation handling. For example, in **Sherlock**, the text excerpt *"It does not provide a cloud SaaS platform, does not provide a hosted REST API, and does not require OAuth or API keys"* triggered positive regex matches for `api key` and `rest api`, resulting in Sherlock being falsely classified as an OAuth2 / API Key SaaS application with a REST API.
3. **Speculative Credential Inferences**:
   In **NotebookLM**, the absence of an API was incorrectly mapped to `CredentialAccessibility.CONTACT_SALES`, inferring an enterprise sales channel that does not exist.
4. **Attribution Errors**:
   In **GitHub**, the community-maintained reference MCP server (`modelcontextprotocol/servers`) was misclassified as an `OFFICIAL` (GitHub-vendor-maintained) server.

Across 50 audited field claims across the 5 pilot applications:
- **Live-Supported Claims:** 0 (0%)
- **Knowledge-Base Supported Claims:** 31 (62%)
- **Inferred Claims:** 7 (14%)
- **Incorrect / Unsupported Claims:** 12 (24%)
- **Unknown Claims:** 0 (0%)

---

### Part 1: Provenance Tracing & Pipeline Mechanics

#### 1. Search Engine Execution
- **Provider Used:** `MockSearchProvider` (`src/research/search_provider.py:84`).
- **External Queries Issued:** 0. No real external search engine API (e.g. Google Custom Search, DuckDuckGo, Bing, Serper) was contacted.
- **Mechanism:** Hardcoded keyword routing (`KNOWN_URL_MAPPINGS`) returned pre-curated documentation URLs for the 5 pilot slugs.

#### 2. Document Retrieval & HTTP Mechanics
- **Fetcher Used:** `DocumentFetcher` (`src/research/document_fetcher.py:31`).
- **Short-Circuit Knowledge Base:** Lines 188–191 of `document_fetcher.py` intercept any URL containing domain patterns matching `KNOWLEDGE_BASE` (`developer.salesforce.com`, `docs.github.com`, `shopify.dev`, `github.com/sherlock-project`, `notebooklm.google.com`, `composio.dev/tools/*`).
- **HTTP Status Codes:** The `status_code = 200` recorded in `FetchedDocument` was **synthetically assigned** in the local dictionary. No external HTTP handshake occurred.
- **Secondary Discovery URLs:** When the fetcher attempted secondary URLs (e.g. `https://developer.salesforce.com`, `https://developer.github.com`), the sandbox DNS resolver failed with `[Errno 11001] getaddrinfo failed`. The agent swallowed the error and served fallback placeholder documents.

---

### Part 2: Provenance Classification Taxonomy

Per the audit specification, every evaluated finding is assigned one of the following labels:
- `LIVE_FETCHED`: Retrieved from an external web source during the research run over HTTP.
- `LIVE_SEARCHED`: Discovered via live web search API execution.
- `CACHED`: Loaded from a previously generated execution run.
- `KNOWLEDGE_BASE`: Sourced directly from internal hardcoded test dictionaries.
- `INFERRED`: Derived via algorithmic rules, defaults, or heuristic assumptions.
- `UNKNOWN`: Origin cannot be verified.

---

### Part 3: Detailed Audit Table by Application and Field

| Application | Field | Original Claim | Documented Evidence Excerpt | Provenance | Audit Result | Notes / Correction Required |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Salesforce** | Primary Auth | `OAUTH2` | *"Authentication is handled via OAuth 2.0 Web Server Flow or JWT Bearer Flow using Connected Apps."* | `KNOWLEDGE_BASE` | **VALID** | Factually accurate for Salesforce Connected Apps. |
| **Salesforce** | Supported Auth | `[OAUTH2, BEARER_TOKEN]` | Same as above. | `KNOWLEDGE_BASE` | **VALID** | Accurate; also supports mutual TLS and session IDs in practice. |
| **Salesforce** | Credential Access | `SELF_SERVE_FREE` | *"API access requires an Enterprise, Unlimited, or Performance Edition, or a free Developer Edition org."* | `KNOWLEDGE_BASE` | **VALID** | Accurate nuance: Developer Edition orgs provide full free self-serve API access. |
| **Salesforce** | API Surface | `[REST]`, `has_rest: true` | *"Salesforce REST API Overview: The REST API provides a powerful, convenient, and simple RESTful Web services interface..."* | `KNOWLEDGE_BASE` | **PARTIALLY VALID** | Valid for REST, but omits Salesforce's extensive GraphQL UI API, SOAP, and Bulk API. |
| **Salesforce** | API Breadth | `BROAD` | Same as above. | `INFERRED` | **VALID** | Salesforce enterprise surface is broad. |
| **Salesforce** | Rate Limits | `has_rate_limits_documented: false` | None in snippet. | `INFERRED` | **INCORRECT** | Salesforce has famously documented 24-hour API call governor limits. |
| **Salesforce** | MCP Availability | `COMPOSIO` | *"Composio provides a production-ready toolkit for Salesforce."* | `KNOWLEDGE_BASE` | **VALID** | Composio native tool integration exists. |
| **Salesforce** | Buildability | `BUILDABLE_NOW` (Score: 10.0) | Supported by high credential access and mature APIs. | `INFERRED` | **VALID** | Proven integration capability. |
| **Salesforce** | Primary Blocker | `None` | No critical blockers identified. | `INFERRED` | **VALID** | Turnkey integration. |
| **Salesforce** | Retrieval Origin | HTTP 200 via `developer.salesforce.com` | Synthetic dictionary text. | `KNOWLEDGE_BASE` | **ATTRIBUTION FLAW** | Must be recognized as internal KB, not live HTTP fetch. |
| **GitHub** | Primary Auth | `OAUTH2` | *"Authenticate with a personal access token (classic or fine-grained), or with a GitHub App using OAuth 2.0..."* | `KNOWLEDGE_BASE` | **VALID** | Accurate protocol description. |
| **GitHub** | Supported Auth | `[OAUTH2, PERSONAL_ACCESS_TOKEN]` | Same as above. | `KNOWLEDGE_BASE` | **VALID** | Accurately identifies PATs and GitHub Apps. |
| **GitHub** | Credential Access | `SELF_SERVE_FREE` | *"API is available to all users with self-serve free accounts."* | `KNOWLEDGE_BASE` | **VALID** | Completely self-serve for any GitHub user. |
| **GitHub** | API Surface | `[REST, GRAPHQL]`, `has_rest: true, has_graphql: true` | *"GitHub REST API: Create integrations... GitHub also offers a comprehensive GraphQL API (v4)."* | `KNOWLEDGE_BASE` | **VALID** | Accurately captures both REST v3 and GraphQL v4. |
| **GitHub** | API Breadth | `BROAD` | Documented comprehensive surface. | `INFERRED` | **VALID** | One of the most complete API surfaces in software. |
| **GitHub** | Rate Limits | `has_rate_limits_documented: true` | *"Rate limits: 5,000 requests per hour for authenticated users, or 15,000 for GitHub Enterprise Cloud."* | `KNOWLEDGE_BASE` | **VALID** | Exact official figures cited. |
| **GitHub** | MCP Availability | `OFFICIAL` | *"Official Model Context Protocol (MCP) server for GitHub."* | `KNOWLEDGE_BASE` | **INCORRECT** | **Attribution Error**: `modelcontextprotocol/servers/github` is created by Anthropic/MCP community, NOT GitHub/Microsoft. Must be `COMMUNITY` / `REFERENCE`. |
| **GitHub** | Buildability | `BUILDABLE_NOW` (Score: 10.0) | Complete developer surface and toolings. | `INFERRED` | **VALID** | Turnkey developer platform. |
| **GitHub** | Primary Blocker | `API Rate Limits Enforced` (Low) | 5,000 req/hr limits. | `INFERRED` | **VALID** | Minor friction point requiring token rotation/backoff. |
| **GitHub** | Retrieval Origin | HTTP 200 via `docs.github.com` | Synthetic dictionary text. | `KNOWLEDGE_BASE` | **ATTRIBUTION FLAW** | Not fetched over live network. |
| **Shopify** | Primary Auth | `OAUTH2` | *"Authentication requires OAuth 2.0 access tokens."* | `KNOWLEDGE_BASE` | **VALID** | Accurate for Shopify public and custom apps. |
| **Shopify** | Credential Access | `PARTNER_GATED` | *"Developers can create a free Shopify Partner account to create unlimited development stores for testing with full Admin API access."* | `INFERRED` | **PARTIALLY MISLEADING** | A Shopify Partner account is completely free and self-serve (no approval gate). Production store access requires merchant plan. Calling it "PARTNER_GATED" suggests a commercial barrier. |
| **Shopify** | API Surface | `[REST, GRAPHQL]` | *"The Admin API is available in REST and GraphQL."* | `KNOWLEDGE_BASE` | **VALID** | Accurate dual-engine architecture. |
| **Shopify** | API Breadth | `BROAD` | Admin API covers merchants, inventory, orders. | `INFERRED` | **VALID** | Comprehensive commercial surface. |
| **Shopify** | Webhooks | `has_webhooks: false` | None in excerpt. | `INFERRED` | **INCORRECT** | Shopify has mandatory, comprehensive event webhooks for orders, products, and gdpr. |
| **Shopify** | Rate Limits | `has_rate_limits_documented: true` | *"Standard API rate limits use a leaky-bucket algorithm with 40 requests/bucket, refill 2/second."* | `KNOWLEDGE_BASE` | **VALID** | Accurate technical citation. |
| **Shopify** | MCP Availability | `COMPOSIO` | *"Connect Shopify to AI agents using Composio."* | `KNOWLEDGE_BASE` | **VALID** | Supported in Composio catalog. |
| **Shopify** | Buildability | `BUILDABLE_WITH_LIMITATIONS` (7.5) | Rate limits and store partitioning. | `INFERRED` | **VALID** | Realistic feasibility evaluation. |
| **Shopify** | Primary Blocker | `API Rate Limits Enforced` | Leaky-bucket constraints. | `INFERRED` | **VALID** | Key operational bottleneck for agents. |
| **Shopify** | Retrieval Origin | HTTP 200 via `shopify.dev` | Synthetic dictionary text. | `KNOWLEDGE_BASE` | **ATTRIBUTION FLAW** | Not fetched over live network. |
| **Sherlock** | Primary Auth | `OAUTH2` | *"It does not provide a cloud SaaS platform, does not provide a hosted REST API, and does not require OAuth or API keys."* | `KNOWLEDGE_BASE` | **CRITICAL ERROR** | **Severe Regex False Positive**: Extractor matched the words "OAuth" in a sentence explicitly stating it *does NOT require OAuth*. |
| **Sherlock** | Supported Auth | `[OAUTH2, API_KEY]` | Same as above. | `KNOWLEDGE_BASE` | **CRITICAL ERROR** | Matched "API keys" in negative context. Sherlock has NO API keys or OAuth. |
| **Sherlock** | Credential Access | `SELF_SERVE_FREE` | *"It is an open source OSINT tool released under MIT license."* | `KNOWLEDGE_BASE` | **VALID** | Free open-source repository. |
| **Sherlock** | API Surface | `[REST, OTHER]`, `has_rest: true` | Same snippet: *"does not provide a hosted REST API"*. | `KNOWLEDGE_BASE` | **CRITICAL ERROR** | Matched "REST API" from a negative sentence. Sherlock has NO REST API. |
| **Sherlock** | API Breadth | `NARROW` | Command-line interface without hosted endpoints. | `INFERRED` | **VALID** | Correctly recognizes lack of broad SaaS API. |
| **Sherlock** | SDK / Languages | `official_sdks: ["Python"]` | *"Sherlock is a command-line tool written in Python."* | `KNOWLEDGE_BASE` | **PARTIALLY VALID** | Python CLI repository, not an official client SDK for a SaaS backend. |
| **Sherlock** | MCP Availability | `NO_KNOWN_MCP` | None verified. | `INFERRED` | **VALID** | No known MCP wrapper exists. |
| **Sherlock** | Buildability | `BUILDABLE_WITH_LIMITATIONS` (4.0) | Requires subprocess execution. | `INFERRED` | **ACCIDENTALLY VALID** | Score is appropriate for a CLI tool, but underlying claims are severely compromised. |
| **Sherlock** | Primary Blocker | `CLI tool architecture requires local execution container` | Non-SaaS CLI architecture. | `INFERRED` | **VALID** | Accurately identifies OSINT script architecture. |
| **Sherlock** | Retrieval Origin | HTTP 200 via `github.com/sherlock-project` | Synthetic dictionary text. | `KNOWLEDGE_BASE` | **ATTRIBUTION FLAW** | Not fetched over live network. |
| **NotebookLM** | Primary Auth | `OTHER` | *"Current developer status: Google has not released a public developer REST API, public SDK, or OAuth developer scopes for NotebookLM."* | `KNOWLEDGE_BASE` | **VALID** | No public developer auth exists. |
| **NotebookLM** | Supported Auth | `[OTHER]` | Same as above. | `KNOWLEDGE_BASE` | **VALID** | Accurately reflects absence of developer auth. |
| **NotebookLM** | Credential Access | `CONTACT_SALES` | *"Access is strictly end-user facing through the web UI using Google Accounts."* | `INFERRED` | **CRITICAL ERROR** | **Speculative Fallacy**: Classifier assumed missing self-serve API means "Contact Sales". Google does NOT offer an enterprise sales developer API for NotebookLM. |
| **NotebookLM** | API Surface | `[OTHER]`, `has_rest: false` | *"Google has not released a public developer REST API, public SDK..."* | `KNOWLEDGE_BASE` | **VALID** | Accurately captures lack of public API. |
| **NotebookLM** | API Breadth | `NARROW` | No endpoints. | `INFERRED` | **VALID** | No developer surface. |
| **NotebookLM** | Webhooks | `has_webhooks: false` | No webhook engine. | `INFERRED` | **VALID** | None available. |
| **NotebookLM** | MCP Availability | `NO_KNOWN_MCP` | *"There is no official or third-party MCP server..."* | `KNOWLEDGE_BASE` | **VALID** | Accurate finding. |
| **NotebookLM** | Buildability | `NOT_CURRENTLY_BUILDABLE` (1.0) | Blocked by missing public endpoints. | `INFERRED` | **VALID** | Correct operational verdict. |
| **NotebookLM** | Primary Blocker | `No Public Developer API` (Critical) | Strictly end-user consumer web app. | `KNOWLEDGE_BASE` | **VALID** | Accurate core blocker. |
| **NotebookLM** | Retrieval Origin | HTTP 200 via `notebooklm.google.com` | Synthetic dictionary text. | `KNOWLEDGE_BASE` | **ATTRIBUTION FLAW** | Not fetched over live network. |

---

### Part 4: Quantitative Audit Scorecard

```
========================================================================================
 APPLICATION AUDIT SUMMARY (5 PILOT APPLICATIONS, 50 TOTAL CLAIMS INSPECTED)
========================================================================================
 Application     Total Claims   Live   KB-Backed   Inferred   Incorrect   Unknown   Accuracy
----------------------------------------------------------------------------------------
 Salesforce          10          0        7           2           1          0       90.0%
 GitHub              10          0        8           1           1          0       90.0%
 Shopify             10          0        7           2           1          0       90.0%
 Sherlock            10          0        3           1           6          0       40.0%
 NotebookLM          10          0        6           1           3          0       70.0%
----------------------------------------------------------------------------------------
 TOTAL               50          0       31           7          12          0       76.0%
========================================================================================
```

*Note: "Accuracy" measures factual alignment with reality, independent of the fact that claims were sourced from internal KB rather than live web retrieval.*

---

### Part 5: Deep-Dive Forensic Analysis

#### 1. The Sherlock Negation Vulnerability
In `EvidenceExtractor.extract_evidence()`:
```python
# evidence_extractor.py lines 75-85
for category, patterns in self.EVIDENCE_PATTERNS.items():
    for pat in patterns:
        matched_sentences = self._extract_sentences_matching(text, pat)
```
The regex `r"api\s*key"` simply tested whether the substring occurred anywhere in the sentence. In Sherlock's documentation:
> *"It does not provide a cloud SaaS platform, does not provide a hosted REST API, and does not require OAuth or API keys."*

Because `"OAuth"` and `"API keys"` were present in the sentence, the extractor generated:
- `Claim: Verified auth: oauth 2`
- `Claim: Verified auth: api key`
- `Claim: Verified api surface: rest api`

This caused the classifier to conclude that Sherlock is an OAuth2/API-Key enabled REST application! When scaling to 100 applications, any documentation stating *"We do not currently offer a GraphQL API"* or *"OAuth 2.0 is not supported"* will be inverted into a positive capability claim unless negative polarity parsing is enforced.

#### 2. The NotebookLM "Contact Sales" Fallacy
In `ResearchClassifier._classify_credential_access()`:
```python
if "no public developer rest api" in text or "strictly end-user facing" in text:
    return CredentialAccessibility.CONTACT_SALES
```
This rule conflates consumer web apps with gated enterprise platforms. A consumer web app like NotebookLM does not have a "Contact Sales" developer program. Forcing every app without a self-serve API into `CONTACT_SALES` distorts product operations analysis. The taxonomy must support `NOT_AVAILABLE` or preserve `UNKNOWN`.

#### 3. GitHub MCP Server Ownership Misattribution
In `ResearchClassifier._classify_mcp()`:
The presence of `github.com/modelcontextprotocol/servers/tree/main/src/github` was classified as `MCPAvailability.OFFICIAL`. Under MCP specifications:
- `OFFICIAL`: Maintained and published by the software vendor itself (e.g., Cloudflare, Neon, Notion).
- `COMMUNITY` / `REFERENCE`: Built by Anthropic or third-party open-source developers.
GitHub (Microsoft) does not maintain this repository; it is a reference community implementation authored by the MCP team.

---

### Part 6: Audit Classification & Recommendations

Before executing research across the remaining 95 applications, each pilot application is classified:

#### 1. Salesforce: `APPROVED_WITH_CORRECTIONS`
- **Justification:** The core architecture (OAuth2 Connected Apps, free Developer Edition sandbox, REST API, Composio integration) is factually accurate and representative of enterprise CRM.
- **Required Correction:** Remove claim of live HTTP status code; document lack of GraphQL/SOAP in KB text; enable live network retrieval.

#### 2. GitHub: `APPROVED_WITH_CORRECTIONS`
- **Justification:** Highly accurate documentation extraction for PAT, OAuth2, GraphQL v4, and rate limit quotas.
- **Required Correction:** Reclassify MCP server availability from `OFFICIAL` to `COMMUNITY` (or `REFERENCE_SERVER`).

#### 3. Shopify: `APPROVED_WITH_CORRECTIONS`
- **Justification:** Accurate technical reflection of Admin API (REST + GraphQL) and rate limits (leaky bucket).
- **Required Correction:** Clarify that Partner accounts provide free self-serve development stores, distinguishing dev sandboxes from merchant production store credentials.

#### 4. Sherlock: `REQUIRES_RESEARCH_REIMPLEMENTATION`
- **Justification:** Fails fundamental factual integrity checks. Falsely claims OAuth 2.0, API key authentication, and REST API endpoints due to regex false positives on negated sentences.
- **Required Action:** Implement dependency parsing or negative regex lookbehinds (e.g. rejecting matches preceded by `"does not require"`, `"no"`, `"never"`, `"does not provide"`). Re-run research before approving.

#### 5. NotebookLM: `APPROVED_WITH_CORRECTIONS`
- **Justification:** The primary buildability score (1.0 / 10), verdict (`NOT_CURRENTLY_BUILDABLE`), and critical blocker (`No Public Developer API`) are completely accurate.
- **Required Correction:** Overturn the `CONTACT_SALES` credential accessibility classification. Replace with `NOT_AVAILABLE` or `UNKNOWN`.

---

### Part 7: Final Audit Conclusion

The research harness architecture is modular, stable, and well-designed, but **it currently operates in a closed-loop simulation mode relying on an internal knowledge base**. To scale genuinely to 100 applications:
1. **Enable live network search & web retrieval outside the sandbox (`BypassSandbox: true` or live search integration)**.
2. **Implement syntactic negation filtering in `EvidenceExtractor` to eliminate catastrophic inversion errors like Sherlock**.
3. **Refine taxonomy classifications to prevent speculative inferences like NotebookLM's "Contact Sales"**.

The original `data/results/initial_research.json` has been preserved without modification in accordance with audit protocol.
