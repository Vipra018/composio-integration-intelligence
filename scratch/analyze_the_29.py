import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

others = [a for a in data["applications"] if a["auth"]["primary_method"] == "OTHER"]

print(f"Total OTHER apps: {len(others)}")
for a in others:
    meta = a.get("app_metadata", {})
    print("=" * 80)
    print(f"ID: {a['app_id']} | Name: {meta.get('name')} | Category: {meta.get('category')}")
    print(f"Desc: {meta.get('description', '')[:70]}")
    print(f"Api types: {a['api_surface']['api_types']}")
    print(f"Supported methods: {a['auth']['supported_methods']}")
    print(f"Notes: {a['auth'].get('accessibility_notes')}")
    print("Claims:")
    for c in a.get("claims", []):
        if any(k in c.get("field_name", "").lower() for k in ["auth", "api", "integration"]):
            print(f"  - {c.get('field_name')}: {c.get('extracted_value')} (prov: {c.get('provenance')})")
            if c.get("supporting_excerpt"):
                print(f"    Excerpt: {c.get('supporting_excerpt')[:120]}...")
