import sys
sys.path.insert(0, ".")
import json
from src.models.research import AppResearchResult

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for a in data["applications"]:
    obj = AppResearchResult.model_validate(a)

print(f"Successfully validated all {len(data['applications'])} records with AppResearchResult!")
