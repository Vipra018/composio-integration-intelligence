import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for a in data["applications"]:
    desc = a.get("one_line_description", "")
    name = a.get("name", a["app_id"])
    if "cli" in desc.lower() or "cli" in name.lower() or "command" in desc.lower():
        print(f"{a['app_id']}: {name} -> {desc}")
