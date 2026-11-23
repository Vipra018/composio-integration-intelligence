import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for a in data["applications"]:
    aid = a["app_id"]
    breadth = a["api_surface"]["breadth"]
    build = a["feasibility"]["buildability"]
    auth = a["auth"]["primary_method"]
    notes = a["auth"].get("accessibility_notes") or ""
    if breadth in ["NONE", "NARROW"] or build == "NOT_CURRENTLY_BUILDABLE" or "no public api" in notes.lower():
        print(f"{aid:<20} | breadth: {breadth:<8} | build: {build:<25} | auth: {auth} | notes: {notes[:50]}")
