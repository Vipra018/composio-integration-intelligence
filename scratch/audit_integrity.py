"""Audit dataset integrity, schema validation, and canonical matching."""

import json
from collections import Counter
from src.models.research import AppResearchResult

with open("data/canonical_apps.json", "r", encoding="utf-8") as f:
    canonical = json.load(f)

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    results_data = json.load(f)

apps = results_data["applications"]

print(f"Canonical apps count: {len(canonical)}")
print(f"Results apps count: {len(apps)}")
assert len(apps) == 100, f"Expected 100, got {len(apps)}"

# 1. Check ID and name matching
canon_map = {a["id"]: a for a in canonical}
result_map = {a["app_id"]: a for a in apps}

assert set(canon_map.keys()) == set(result_map.keys()), "ID mismatch between canonical and results!"

# 2. Check category matching
for app_id, c_app in canon_map.items():
    r_app = result_map[app_id]
    assert c_app["name"] == r_app["name"], f"Name mismatch for {app_id}: {c_app['name']} vs {r_app['name']}"
    assert c_app["category"] == r_app["category"], f"Category mismatch for {app_id}: {c_app['category']} vs {r_app['category']}"

# 3. Check categories count
cats = Counter(a["category"] for a in apps)
print("\nCategories:")
for c, cnt in cats.items():
    print(f"  {c}: {cnt}")
    assert cnt == 10, f"Category {c} count is {cnt}, expected 10"

# 4. Schema validation using Pydantic AppResearchResult
schema_errors = 0
for app in apps:
    try:
        AppResearchResult.model_validate(app)
    except Exception as e:
        print(f"Schema validation error in {app.get('app_id')}: {e}")
        schema_errors += 1

print(f"\nSchema validation errors: {schema_errors}")
assert schema_errors == 0, "Schema validation failed on some records!"
print("DATASET INTEGRITY AUDIT PASSED 100%!")
