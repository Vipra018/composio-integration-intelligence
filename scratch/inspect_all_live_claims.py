import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for a in data["applications"]:
    for c in a.get("claims", []):
        if c.get("provenance") == "LIVE_FETCHED":
            fn = c.get("field_name")
            val = c.get("extracted_value")
            exc = c.get("supporting_excerpt", "") or ""
            url = c.get("source_url")
            # Print field_name and excerpt summary
            print(f"[{a['app_id']:<15}] {fn:<30} = {val:<20} | Exc: {exc[:60]}... | URL: {str(url)[:40]}")
