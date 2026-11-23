import json
from collections import Counter

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]
print("All current primary_methods:")
counts = Counter(a["auth"]["primary_method"] for a in apps)
for m, c in counts.most_common():
    print(f"  {m}: {c}")

print("\nApps with OAUTH2:")
print([a["app_id"] for a in apps if a["auth"]["primary_method"] == "OAUTH2"])

print("\nApps with API_KEY:")
print([a["app_id"] for a in apps if a["auth"]["primary_method"] == "API_KEY"])

print("\nApps with PERSONAL_ACCESS_TOKEN / TOKEN:")
print([a["app_id"] for a in apps if a["auth"]["primary_method"] in ["PERSONAL_ACCESS_TOKEN", "BEARER_TOKEN", "TOKEN"]])
