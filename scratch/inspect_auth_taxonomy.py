import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for a in data["applications"]:
    p = a["auth"]["primary_method"]
    if p == "OTHER":
        notes = (a["auth"].get("accessibility_notes") or "")[:50]
        types = a["api_surface"]["api_types"]
        desc = a.get("one_line_description", "")[:50]
        print(f"{a['app_id']:<22} | types: {str(types):<25} | notes: {notes:<40} | desc: {desc}")
