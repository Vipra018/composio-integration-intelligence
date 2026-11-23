import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for a in data["applications"]:
    if a["auth"]["primary_method"] == "UNKNOWN":
        desc = a.get("one_line_description", "")[:45]
        print(f"{a['app_id']:<25} | {a['category']:<35} | {desc}")
