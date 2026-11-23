"""Audit all 100 apps to establish integration mode, auth applicability, and true auth method."""

import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]

print("Current distribution of primary_method:")
from collections import Counter
counts = Counter(a["auth"]["primary_method"] for a in apps)
for k, v in counts.most_common():
    print(f"  {k}: {v}")
