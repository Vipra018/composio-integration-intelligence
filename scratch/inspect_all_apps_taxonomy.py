import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]

print(f"Total apps: {len(apps)}")

for a in apps:
    aid = a["app_id"]
    name = a.get("name", aid)
    cat = a.get("category", "")
    types = a["api_surface"]["api_types"]
    breadth = a["api_surface"]["breadth"]
    build = a["feasibility"]["buildability"]
    auth_m = a["auth"]["primary_method"]
    notes = a["auth"].get("accessibility_notes", "") or ""
    
    # Check if CLI / Web-only or interesting
    is_cli = aid in ["sherlock", "mermaid-cli"]
    is_web = breadth == "NONE" or "No public" in notes or build == "NOT_CURRENTLY_BUILDABLE"
    
    if is_cli or is_web or auth_m in ["OTHER", "UNKNOWN"]:
        print(f"{aid:<18} | cat: {cat:<24} | types: {str(types):<24} | breadth: {breadth:<8} | build: {build:<24} | auth: {auth_m}")
