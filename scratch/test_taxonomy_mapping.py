import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]

cli_apps = ["sherlock", "mermaid-cli"]
web_only_apps = ["notebooklm", "consensus", "devin", "fanbasis"]

for a in apps:
    aid = a["app_id"]
    if aid in cli_apps:
        mode = "CLI / LOCAL_PROCESS"
        applicability = "NOT_APPLICABLE"
        auth_method = "NOT_APPLICABLE"
    elif aid in web_only_apps:
        mode = "WEB_ONLY"
        applicability = "NOT_APPLICABLE"
        auth_method = "NOT_APPLICABLE"
    else:
        mode = "API"
        applicability = "APPLICABLE"
        auth_method = a["auth"]["primary_method"]
    
    # Check if this was one of the 22 falsely marked OTHER
    # If it was OTHER and mode == API:
    if a["auth"]["primary_method"] == "OTHER" and mode == "API":
        print(f"Fixing {aid}: currently OTHER")
