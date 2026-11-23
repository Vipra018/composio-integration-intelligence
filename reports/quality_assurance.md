# Integration Intelligence: Quality Assurance & Provenance Audit Report

**Auditor / Quality Assurance**: Integration Intelligence Verification Engine  
**Target Artifact**: `data/results/final_research_100.json`  
**Evaluation Scope**: 100 Canonical Applications across 10 Categories  
**Execution Timestamp**: 2026-11-23  

---

## 1. Quality Assurance Verification Matrix

| Verification Requirement | Target Condition | Audited Status | Verification Proof |
| :--- | :---: | :---: | :--- |
| **Total Record Count** | Exactly 100 applications | **PASS (100/100)** | Verified in `scratch/audit_integrity.py` |
| **Category Distribution** | Exactly 10 categories, 10 apps each | **PASS (10/10/10)** | All 10 original assignment categories hold exactly 10 apps |
| **Canonical App Matching** | 100% ID and name equality | **PASS (100/100)** | Exact match with `data/canonical_apps.json` |
| **No Duplicate Records** | 0 duplicated app IDs | **PASS (0 duplicates)** | `len(set(app_ids)) == 100` |
| **HTTP Status Authenticity** | Real HTTP status codes recorded | **PASS (100% Real)** | Actual status codes captured (200, 403, 404, 429, DNS errors); zero synthetic 200s |
| **Production Mock Search Isolation** | 0 mock search results in prod | **PASS (0 mock calls)** | `UnavailableSearchProvider` returned `SEARCH_UNAVAILABLE` when API keys absent |
| **Knowledge Base Exclusion** | 0 production claims from mock KB | **PASS (0 KB claims)** | Hardcoded test dictionary strictly gated behind `allow_mock_kb=False` |
| **Claim Citation Integrity** | Confirmed claims cite excerpt | **PASS (100% cited)** | All 121 `LIVE_FETCHED` claims reference valid URLs and non-empty DOM excerpts |
| **Negation Safety** | Negative evidence != positive capability | **PASS (Enforced)** | Sentences with negation cues (`no`, `never`, `does not provide`) yield `NEGATIVE` polarity |
| **Unknown Value Preservation** | Missing facts remain `UNKNOWN` | **PASS (Enforced)** | 117 claims preserved as `UNKNOWN` rather than guessed |
| **NotebookLM Safety Guard** | No speculative `CONTACT_SALES` | **PASS (Guard Verified)** | Credential accessibility marked `UNKNOWN`; `has_rest=False`; integration mode: `WEB_ONLY` |
| **Sherlock & CLI Guard** | CLI != hosted SaaS REST API | **PASS (Guard Verified)** | Integration mode: `CLI / LOCAL_PROCESS`; auth applicability: `NOT_APPLICABLE`; `has_rest=False` |
| **Taxonomy Orthogonality** | Integration mode separated from auth | **PASS (Separated)** | 94 API, 4 Web-only, 2 CLI; auth evaluated only where applicable |
| **Composio Catalog Attribution** | No guessed tool slugs | **PASS (Verified Slugs)** | 66 apps matched against authoritative Composio registry with real tool slugs |
| **Independent MCP Separation** | Independent MCPs != Composio bridge | **PASS (Separated)** | 5 official vendor MCPs, 7 community/reference MCPs, 54 Composio bridge, 34 no known MCP |

---

## 2. Evidence Citations vs. Claims Breakdown

Across the 100 evaluated applications, the audit strictly separates **raw documentation citations** from **structured field-level claims**:

```
Total Applications Audited:        100
Total Evidence Citations:          395 (across 82 distinct documentation endpoints)
Total Structured Claims:           541
```

### Claim Distribution by Provenance

| Claim Provenance | Count | Percentage | Description |
| :--- | :---: | :---: | :--- |
| **`LIVE_FETCHED`** | **121** | **22.4%** | Factual assertions directly corroborated by live HTTP 200 DOM snippets from official developer documentation. |
| **`INFERRED`** | **303** | **56.0%** | Deterministic classifications derived from algorithmic heuristics (e.g. multi-engine REST+GraphQL indicating broad breadth, CLI tools requiring local execution, Composio tool mappings). |
| **`UNKNOWN`** | **117** | **21.6%** | Preserved markers where developer portals were protected by WAFs/logins or lacked public developer documentation. Never counted as negative findings. |
| **`KNOWLEDGE_BASE`** | **0** | **0.0%** | Zero reliance on synthetic test fixtures in production mode. |

---

## 3. Composio & Independent MCP Taxonomy Audit

| MCP Classification Category | App Count | Percentage | Description & Examples |
| :--- | :---: | :---: | :--- |
| **Native Composio Toolkits** | **66** | **66.0%** | Platforms with native actions/triggers in Composio catalog (e.g. `github`, `slack`, `salesforce`, `hubspot`, `stripe`). |
| **Official 1st-Party MCP Servers** | **5** | **5.0%** | Vendor-authored and maintained MCP repositories: **Cloudflare**, **Netlify**, **Sentry**, **Apify**, **Firecrawl**. |
| **Community / Reference MCP Servers** | **7** | **7.0%** | Open-source reference implementations: **GitHub** (Anthropic reference), **Slack** (Anthropic reference), **Shopify** (Dev AI Toolkit), **Supabase**, **Linear**, **Notion**, **Stripe**. |
| **Composio MCP Bridge Only** | **54** | **54.0%** | Supported natively via Composio toolkits (accessible to MCP clients via Composio's bridge), but no separate independent vendor/community repository verified. |
| **No Known MCP Server** | **34** | **34.0%** | Platforms with neither an independent MCP server nor a native Composio toolkit. |

---

## 4. Authentication Taxonomy & Applicability Audit

A critical quality audit was conducted to resolve a taxonomy conflation where CLI/local execution was previously lumped under authentication method `OTHER`. CLI and Web-only tools are execution interfaces and integration types, not SaaS authentication protocols.

The corrected taxonomy strictly separates three orthogonal dimensions:

### A. Integration Mode vs. Authentication Applicability (N=100)

| Integration Mode | Auth Applicability | App Count | Percentage | Exemplar Applications |
| :--- | :--- | :---: | :---: | :--- |
| **API** | **APPLICABLE** | **94** | **94.0%** | Salesforce, Slack, HubSpot, Stripe, Twilio, GitHub, Shopify, Attio, Twenty |
| **WEB_ONLY** | **NOT_APPLICABLE** | **4** | **4.0%** | NotebookLM, Consensus, Devin, Fanbasis (consumer platforms without developer APIs) |
| **CLI / LOCAL_PROCESS** | **NOT_APPLICABLE** | **2** | **2.0%** | Sherlock (Python OSINT scraper), Mermaid CLI (Node.js diagram compiler) |

### B. Authentication Status for Applicable SaaS APIs (N=94)

| Authentication Status | App Count | Percentage of Applicable | Description |
| :--- | :---: | :---: | :--- |
| **Known Applicable Records** | **60** | **63.8%** (60/94) | Verified developer authentication documentation. |
| **Unknown / Gated Records** | **34** | **36.2%** (34/94) | Developer documentation protected by enterprise logins, partner gating, or WAFs. Preserved as `UNKNOWN`. |

### C. Distribution of Known Authentication Methods (N=60 Known Applicable Records)

| Primary Authentication Method | App Count | Percentage | Verified Protocol Details |
| :--- | :---: | :---: | :--- |
| **API_KEY** | **27** | **45.0%** (27/60) | Static API Keys, Token Secrets, or Basic Key Pairs (e.g. Twilio, Zendesk, Stripe, Cloudflare, Apify, Attio, Twenty). |
| **OAUTH2** | **24** | **40.0%** (24/60) | OAuth 2.0 Authorization Code or Client Credentials grant flows (e.g. Salesforce, Slack, HubSpot, Google Ads, Shopify, Linear). |
| **TOKEN / PAT** | **7** | **11.7%** (7/60) | Personal Access Tokens or Bearer JWTs (e.g. GitHub, Coda, Front, Harvest, Sentry, Snowflake, Telegram). |
| **BASIC** | **2** | **3.3%** (2/60) | HTTP Basic Authentication with username/password credentials (DataForSEO, Neo4j). |
| **Total Known Applicable** | **60** | **100.0%** (60/60) | Denominator strictly isolates the 60 known applicable records. |

---

## 5. Network Retrieval Health & Error Auditing

During the full 100-app crawl:
- **Total Successful Live Fetches**: 395 successful HTTP 200 responses were captured across documentation anchors.
- **Handled Network Anomalies**:
  - **HTTP 403 Forbidden**: Encountered on enterprise developer portals protected by Cloudflare/Akamai bot management (e.g. Salesforce Developer Portal, Pinterest Dev). Honestly recorded as unauthenticated HTTP 403 blocks rather than synthesizing success.
  - **Redirect Loops / Single Page App Shells**: Handled on consumer web applications (e.g. NotebookLM, Otter AI, Consensus) where client-side JavaScript rendering returned minimal static DOM.
  - **DNS Resolution / Connection Timeouts**: Gated domains with 6.0-second timeouts, preventing pipeline hanging while logging failure reasons.

---

## 6. Automated Test Suite Execution Results

All 44 automated tests in the test suite pass with zero failures:

```
Platform: Windows (Python 3.14.7, pytest-8.4.2)
Total Tests Collected: 44
Passed: 44 (100%)
Failed: 0 (0%)
Warnings: 1 (asyncio deprecation warning in dependency)
Duration: 1.50s
```

### Regression & Safety Proofs Passed
- `tests/test_stage3a_integrity.py::test_mock_search_cannot_be_used_in_production_mode` (PASSED)
- `tests/test_stage3a_integrity.py::test_failed_http_request_never_synthetic_200` (PASSED)
- `tests/test_stage3a_integrity.py::test_knowledge_base_never_used_in_production` (PASSED)
- `tests/test_stage3a_integrity.py::test_negative_sentences_never_produce_positive_capability_claims` (PASSED)
- `tests/test_stage3a_integrity.py::test_polarity_analyzer_variations` (PASSED)
- `tests/test_stage3a_integrity.py::test_unknown_fields_remain_unknown` (PASSED)
- `tests/test_stage3a_integrity.py::test_every_confirmed_claim_has_valid_evidence_reference` (PASSED)
- `tests/test_stage3a_integrity.py::test_five_pilot_records_save_and_load` (PASSED)

---

## 7. Audit Statement on Verification Metrics

**Research Quality Statement**:
This study does not assert generalized human ground-truth accuracy. Instead, it provides **verifiable programmatic audit metrics**:
- **65 applications passed automated corroboration checks** (`AUTOMATED_PASS`) where live documentation was successfully fetched, parsed, and corroborated without contradictory evidence.
- **35 applications are flagged for human review** (`REQUIRES_HUMAN_REVIEW`) due to bot protection, login requirements, or unreleased developer APIs.
- 100% of claims are traceable to their exact origin (`LIVE_FETCHED`, `INFERRED`, or `UNKNOWN`).
