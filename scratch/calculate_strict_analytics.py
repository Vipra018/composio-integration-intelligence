import json
from collections import Counter

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]
total = len(apps)

# 1. Integration Mode
mode_counts = Counter(a["auth"]["integration_mode"] for a in apps)

# 2. Auth Applicability
applicability_counts = Counter(a["auth"]["auth_applicability"] for a in apps)

# 3. Applicable apps
applicable_apps = [a for a in apps if a["auth"]["auth_applicability"] == "APPLICABLE"]
known_auth = [a for a in applicable_apps if a["auth"]["primary_method"] not in ["UNKNOWN", "NOT_APPLICABLE"]]
unknown_auth = [a for a in applicable_apps if a["auth"]["primary_method"] == "UNKNOWN"]
not_applicable = [a for a in apps if a["auth"]["auth_applicability"] == "NOT_APPLICABLE"]

# 4. Known Auth Methods
known_methods = Counter(a["auth"]["primary_method"] for a in known_auth)

# 5. Feasibility / Buildability
build_counts = Counter(a["feasibility"]["buildability"] for a in apps)

# 6. Composio & MCP
mcp_avail = Counter(a["mcp"]["availability"] for a in apps)
composio_ready = [a for a in apps if a["mcp"].get("composio_tool_count", 0) > 0]

print("=" * 60)
print("AUDITED TAXONOMY & ANALYTICS BREAKDOWN")
print("=" * 60)
print(f"Total applications investigated: {total}")
print(f"\n1. INTEGRATION MODE (Denominator = {total}):")
for m, c in mode_counts.most_common():
    print(f"   - {m}: {c} ({c/total*100:.1f}%, {c}/{total})")

print(f"\n2. AUTHENTICATION APPLICABILITY (Denominator = {total}):")
for a, c in applicability_counts.most_common():
    print(f"   - {a}: {c} ({c/total*100:.1f}%, {c}/{total})")

print(f"\n3. AUTHENTICATION STATUS (Denominator = {len(applicable_apps)} applicable apps):")
print(f"   - Known Authentication Records: {len(known_auth)} ({len(known_auth)/len(applicable_apps)*100:.1f}%, {len(known_auth)}/{len(applicable_apps)})")
print(f"   - Unknown Authentication Records: {len(unknown_auth)} ({len(unknown_auth)/len(applicable_apps)*100:.1f}%, {len(unknown_auth)}/{len(applicable_apps)})")
print(f"   - Not-Applicable Records: {len(not_applicable)} ({len(not_applicable)/total*100:.1f}% of total, {len(not_applicable)}/{total})")

print(f"\n4. DISTRIBUTION OF KNOWN AUTH METHODS (Denominator = {len(known_auth)} known applicable records):")
for m, c in known_methods.most_common():
    print(f"   - {m}: {c} ({c/len(known_auth)*100:.1f}%, {c}/{len(known_auth)})")

print(f"\n5. BUILDABILITY SCORES (Denominator = {total}):")
for b, c in build_counts.most_common():
    print(f"   - {b}: {c} ({c/total*100:.1f}%, {c}/{total})")

print(f"\n6. MCP TAXONOMY (Denominator = {total}):")
for m, c in mcp_avail.most_common():
    print(f"   - {m}: {c} ({c/total*100:.1f}%, {c}/{total})")
print(f"   - Composio Integrated Applications: {len(composio_ready)} ({len(composio_ready)/total*100:.1f}%, {len(composio_ready)}/{total})")
