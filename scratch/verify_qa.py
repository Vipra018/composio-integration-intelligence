"""Quality assurance verification script for Stage 5 compliance."""

import json
from pathlib import Path

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]
assert len(apps) == 100, f"Expected 100 apps, got {len(apps)}"

# Check unique IDs
app_ids = [a["app_id"] for a in apps]
assert len(set(app_ids)) == 100, "Duplicate app IDs detected!"

# Check categories
from collections import Counter
cats = Counter(a["category"] for a in apps)
assert len(cats) == 10, f"Expected 10 categories, got {len(cats)}"
for c, cnt in cats.items():
    assert cnt == 10, f"Category {c} has {cnt} apps (expected 10)"

# Check canonical dataset alignment
with open("data/apps.json", "r", encoding="utf-8") as f:
    canonical = json.load(f)
canonical_ids = set(a["id"] for a in canonical)
res_ids = set(app_ids)
assert res_ids == canonical_ids, f"Mismatch with canonical dataset! Diff: {res_ids ^ canonical_ids}"

# Check evidence & claim integrity
live_evidence_count = 0
inferred_claims = 0
live_claims = 0
unknown_claims = 0
kb_claims = 0

for a in apps:
    for e in a.get("evidence", []):
        assert e["http_status"] in (200, 403, 404, 429, 500), f"Invalid HTTP status {e['http_status']}"
        assert e["provenance"] in ("LIVE_FETCHED", "LIVE_SEARCHED", "CACHED"), f"Invalid evidence provenance {e['provenance']}"
        if e["provenance"] == "LIVE_FETCHED":
            live_evidence_count += 1
            assert e["http_status"] == 200, "LIVE_FETCHED evidence must have HTTP 200 status"

    for c in a.get("claims", []):
        prov = c["provenance"]
        if prov == "LIVE_FETCHED":
            live_claims += 1
            assert c["source_url"] is not None, f"LIVE_FETCHED claim missing source_url in {a['app_id']}"
            assert c["supporting_excerpt"] is not None, f"LIVE_FETCHED claim missing excerpt in {a['app_id']}"
        elif prov == "INFERRED":
            inferred_claims += 1
        elif prov == "UNKNOWN":
            unknown_claims += 1
        elif prov == "KNOWLEDGE_BASE":
            kb_claims += 1

assert kb_claims == 0, f"CRITICAL: Found {kb_claims} KNOWLEDGE_BASE claims in production results!"

# Check specific application safety rules
nb = next(a for a in apps if a["app_id"] == "notebooklm")
assert nb["auth"]["credential_accessibility"] != "CONTACT_SALES", "NotebookLM must NOT be CONTACT_SALES!"
assert nb["api_surface"]["has_rest"] is False, "NotebookLM has_rest must be False"

sherlock = next(a for a in apps if a["app_id"] == "sherlock")
assert sherlock["api_surface"]["has_rest"] is False, "Sherlock has_rest must be False"
assert sherlock["auth"]["primary_method"] == "OTHER", "Sherlock primary auth must be OTHER"

gh = next(a for a in apps if a["app_id"] == "github")
assert gh["api_surface"]["has_rest"] is True, "GitHub has_rest must be True"
assert gh["auth"]["credential_accessibility"] == "SELF_SERVE_FREE", "GitHub credentials must be SELF_SERVE_FREE"

print("ALL QA INTEGRITY CHECKS PASSED SUCCESSFULLY!")
print(f"Total Apps: {len(apps)}")
print(f"Live Evidence URLs: {live_evidence_count}")
print(f"Live Fetched Claims: {live_claims}")
print(f"Inferred Claims: {inferred_claims}")
print(f"Unknown Claims: {unknown_claims}")
print(f"Knowledge Base Claims: {kb_claims}")
