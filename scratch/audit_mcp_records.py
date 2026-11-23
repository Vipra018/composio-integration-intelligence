import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]
target_ids = ["ahrefs", "otter-ai", "reducto", "se-ranking", "aircall"]

print("=== SPECIFIC TARGET APPS ===")
for a in apps:
    if a["app_id"] in target_ids:
        print("="*60)
        print(f"App: {a['app_id']} ({a['name']})")
        print(f"MCP Info: {json.dumps(a['mcp'], indent=2)}")
        print(f"Evidence URLs: {[e['url'] for e in a.get('evidence', [])]}")
        print("Claims on MCP:")
        for c in a.get("claims", []):
            if "mcp" in c.get("field_name", "").lower():
                print(f"  - {c['field_name']}: {c['extracted_value']} | prov: {c['provenance']} | excerpt: {c.get('supporting_excerpt')}")

print("\n=== ALL APPS WITH NO_KNOWN_MCP ===")
no_known = [a for a in apps if a["mcp"]["availability"] == "NO_KNOWN_MCP"]
print(f"Total NO_KNOWN_MCP: {len(no_known)}")
for a in no_known:
    print(f"  {a['app_id']:<25} | cat: {a['category']:<30} | composio_tool: {a['mcp'].get('composio_tool_supported')}")
