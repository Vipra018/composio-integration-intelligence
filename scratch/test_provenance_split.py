import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

genuine_live = []
downgraded_inferred = []

for a in data["applications"]:
    # Collect all real snippets from fetched evidence
    real_snippets = [e.get("snippet", "") for e in a.get("evidence", []) if e.get("http_status") == 200 and e.get("snippet")]
    
    for c in a.get("claims", []):
        if c.get("provenance") == "LIVE_FETCHED":
            exc = c.get("supporting_excerpt", "")
            # Check if this excerpt is a real quotation from retrieved snippets
            matched = any(exc in s or s in exc for s in real_snippets)
            
            # Additional check: generated phrases
            is_generated = any(phrase in exc.lower() for phrase in [
                "native composio", "no verified official mcp", "no server discovered",
                "application does not expose", "open source codebase available",
                "primary authentication method is", "authorization framework",
                "independent server at", "reference slack mcp", "official apify actor",
                "open-source community", "local cli utility", "consumer web"
            ])
            
            if matched and not is_generated and len(exc) > 5:
                genuine_live.append((a["app_id"], c["field_name"], exc[:50]))
            else:
                downgraded_inferred.append((a["app_id"], c["field_name"], exc[:50]))

print(f"Genuine LIVE_FETCHED: {len(genuine_live)}")
print(f"To be downgraded to INFERRED: {len(downgraded_inferred)}")
print("\nSample to be downgraded:")
for aid, fn, exc in downgraded_inferred[:10]:
    print(f"  [{aid}] {fn}: {exc}")
