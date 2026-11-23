# Integration Intelligence: Autonomous Research Methodology

**Author**: Senior AI Product Operations Architecture  
**System Version**: Integration Intelligence 3.0.0  
**Target Domain**: SaaS Integration Feasibility for Autonomous Agent Toolkits  

---

## 1. System Architecture Overview

The Integration Intelligence research pipeline operates as a modular, evidence-backed evaluation engine designed to investigate web applications without hallucination or data fabrication.

```
+-----------------------------------------------------------------------------------+
|                           CANONICAL DATASET (100 Apps)                             |
|               (10 Categories, 10 Apps each, Original Source Hints)                |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        1. DOCUMENTATION DISCOVERY SERVICE                         |
|   - Evaluates explicit developer_documentation_url                               |
|   - Prioritizes canonical repository hints & developer subdomains                 |
|   - Transparent fallback to SEARCH_UNAVAILABLE when search API keys unconfigured  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                          2. LIVE HTTP RETRIEVAL ENGINE                            |
|   - httpx client with standard browser User-Agent headers                        |
|   - Captures genuine HTTP status codes (200, 403, 404, 429)                      |
|   - Enforces allow_mock_kb=False in production (zero fixture contamination)      |
|   - Strips non-substantive DOM (scripts, navigation, CSS, SVG)                   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                     3. EVIDENCE EXTRACTION & POLARITY ENGINE                      |
|   - Sentence tokenizer identifying capability and restriction patterns            |
|   - Negation Detection: flags sentences containing negative operators ("no",      |
|     "never", "without", "does not provide") as NEGATIVE polarity                 |
|   - Strictly prevents negative sentences from producing positive capability claims|
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                      4. COMPOSIO CATALOG & MCP BRIDGE                             |
|   - Cross-references verified Composio toolkit registry (66 apps supported)       |
|   - Identifies verified Composio tool slugs & representative action schemas       |
|   - Distinguishes vendor official, open-source community, and Composio MCPs      |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                      5. SAFETY CLASSIFIER & PROVENANCE AUDIT                      |
|   - Generates granular ResearchClaim records with explicit Provenance tags:       |
|     [LIVE_FETCHED, INFERRED, UNKNOWN]                                            |
|   - Safety Guard: CLI tools (Sherlock) classified as APIType.OTHER (no REST API)  |
|   - Safety Guard: Unreleased APIs (NotebookLM) marked UNKNOWN (no CONTACT_SALES)  |
|   - Safety Guard: Distinguishes Developer Edition vs Enterprise Paid Access       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        6. ATOMIC STORAGE & CHECKPOINTING                          |
|   - Atomic disk writes via tempfile replacement                                  |
|   - Granular individual checkpoints (data/results/individual/{id}.json)           |
|   - Aggregated master dataset (data/results/final_research_100.json)              |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Methodological Principles

### 2.1 Zero-Fabrication Rule
If external search API credentials (`TAVILY_API_KEY`, `SERPER_API_KEY`) are not present in the environment, the system records `SEARCH_UNAVAILABLE` rather than silently substituting synthetic mock search results. When a developer portal is protected by a WAF or returns HTTP 403/404, the actual status code is recorded. The system never fabricates HTTP 200 or invents non-existent API documentation.

### 2.2 Strict Provenance Classification
Every extracted claim is tagged with an immutable provenance classification:
1. **`LIVE_FETCHED`**: Supported by an exact sentence excerpt retrieved over live HTTP 200 from official documentation.
2. **`INFERRED`**: Algorithmic architectural conclusion derived from documented rules (e.g. multi-engine REST+GraphQL implying broad breadth).
3. **`UNKNOWN`**: Explicit marker for unverified or unavailable information.
4. **`KNOWLEDGE_BASE`**: Strictly prohibited in production execution; isolated to offline unit tests.

### 2.3 Semantic Polarity & Negation Safety
Naive keyword extraction frequently turns negative warnings into false positive claims. For example, a search snippet reading *"Sherlock does not provide a hosted REST API"* previously caused naive regexes to claim REST API support. 

Our semantic polarity analyzer inspects each sentence for negation cues:
```python
NEGATION_PATTERNS = [
    r"\bnot\b", r"\bnever\b", r"\bno\b", r"\bwithout\b",
    r"\bdoes not provide\b", r"\bdoes not require\b",
    r"\bno hosted\b", r"\bnot support\b", r"\bhas not released\b"
]
```
Sentences matching these patterns are assigned `EvidencePolarity.NEGATIVE` and strictly prevented from populating positive capabilities.

### 2.4 Classification Safety Guards
- **The NotebookLM Guard**: Consumer AI applications without published APIs must NOT be labeled `CONTACT_SALES`. The absence of developer documentation simply means the API is currently unreleased, requiring `CredentialAccessibility.UNKNOWN` and `APIBreadth.NONE`.
- **The Sherlock Guard**: Open-source Python CLI tools must NOT be classified as SaaS APIs. Primary authentication is set to `OTHER` and `has_rest=False`.
- **Developer vs. Production Separation**: For platforms like GitHub (Free PATs vs. Enterprise SAML), Shopify (Free Partner stores vs. paid merchant plans), and Salesforce (Free Developer Edition orgs vs. paid enterprise contracts), free developer onboarding is documented separately from production licensing.

---

## 3. Composio Integration Methodology

Composio's platform offers pre-built toolkits containing hundreds of actions and triggers. In Phase 3, we integrated `src/integrations/composio_client.py` which inspects Composio's verified catalog:
1. Matches canonical app IDs against Composio's verified toolkit registry.
2. Captures verified Composio slugs (e.g. `github`, `slack`, `salesforce`, `hubspot`, `zendesk`).
3. Captures real tool action names (e.g. `GITHUB_CREATE_AN_ISSUE`, `SLACK_SEND_MESSAGE`, `STRIPE_CREATE_CUSTOMER`).
4. If an app lacks a standalone MCP server but is supported in Composio, its MCP availability is designated as `MCPAvailability.COMPOSIO`.
5. Operates non-blockingly: if the optional `COMPOSIO_API_KEY` is absent, the system logs the status and uses the verified catalog without interrupting the research pipeline.
