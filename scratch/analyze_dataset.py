"""Analyze the 100-app research dataset and compute exact audited metrics."""

import json
from collections import Counter, defaultdict

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]
total_apps = len(apps)

print(f"Total Applications: {total_apps}")

# 1. Auth Methods
auth_methods = Counter()
primary_auth_methods = Counter()
auth_by_category = defaultdict(Counter)

for app in apps:
    auth = app["auth"]
    for m in auth.get("supported_methods", []):
        auth_methods[m] += 1
    p = auth.get("primary_method", "UNKNOWN")
    primary_auth_methods[p] += 1
    auth_by_category[app["category"]][p] += 1

print("\n--- AUTH METHODS (Supported) ---")
for m, cnt in auth_methods.most_common():
    print(f"  {m}: {cnt} ({cnt/total_apps*100:.1f}%)")

print("\n--- PRIMARY AUTH METHODS ---")
for m, cnt in primary_auth_methods.most_common():
    print(f"  {m}: {cnt} ({cnt/total_apps*100:.1f}%)")

# 2. Credential Accessibility
cred_access = Counter()
for app in apps:
    c = app["auth"].get("credential_accessibility", "UNKNOWN")
    cred_access[c] += 1

print("\n--- CREDENTIAL ACCESSIBILITY ---")
for c, cnt in cred_access.most_common():
    print(f"  {c}: {cnt} ({cnt/total_apps*100:.1f}%)")

# 3. API Surfaces
has_rest = sum(1 for a in apps if a["api_surface"].get("has_rest"))
has_graphql = sum(1 for a in apps if a["api_surface"].get("has_graphql"))
has_webhooks = sum(1 for a in apps if a["api_surface"].get("has_webhooks"))
breadth_counts = Counter(a["api_surface"].get("breadth", "UNKNOWN") for a in apps)

print("\n--- API SURFACES ---")
print(f"  Has REST: {has_rest} ({has_rest/total_apps*100:.1f}%)")
print(f"  Has GraphQL: {has_graphql} ({has_graphql/total_apps*100:.1f}%)")
print(f"  Has Webhooks: {has_webhooks} ({has_webhooks/total_apps*100:.1f}%)")
print("  Breadth:")
for b, cnt in breadth_counts.most_common():
    print(f"    {b}: {cnt} ({cnt/total_apps*100:.1f}%)")

# 4. MCP & Composio
mcp_avail = Counter(a["mcp"].get("availability", "UNKNOWN") for a in apps)
composio_supported = sum(1 for a in apps if a["mcp"].get("composio_tool_supported"))

print("\n--- MCP & COMPOSIO ---")
for m, cnt in mcp_avail.most_common():
    print(f"  {m}: {cnt} ({cnt/total_apps*100:.1f}%)")
print(f"  Composio Supported: {composio_supported} ({composio_supported/total_apps*100:.1f}%)")

# 5. Feasibility & Buildability
buildability = Counter(a["feasibility"].get("buildability", "UNKNOWN") for a in apps)
avg_score = sum(a["feasibility"].get("feasibility_score", 0.0) for a in apps) / total_apps

print("\n--- FEASIBILITY & BUILDABILITY ---")
print(f"  Average Feasibility Score: {avg_score:.2f} / 10.0")
for b, cnt in buildability.most_common():
    print(f"  {b}: {cnt} ({cnt/total_apps*100:.1f}%)")

# 6. Verification Status & Confidence
verif_status = Counter(a.get("verification_status", "UNKNOWN") for a in apps)
conf_levels = Counter(a.get("confidence", "UNKNOWN") for a in apps)

print("\n--- VERIFICATION & CONFIDENCE ---")
for v, cnt in verif_status.most_common():
    print(f"  {v}: {cnt} ({cnt/total_apps*100:.1f}%)")
for c, cnt in conf_levels.most_common():
    print(f"  {c}: {cnt} ({cnt/total_apps*100:.1f}%)")

# 7. Evidence & Claims Provenance Breakdown
total_evidence = sum(len(a.get("evidence", [])) for a in apps)
total_claims = sum(len(a.get("claims", [])) for a in apps)
claim_prov = Counter()
evidence_prov = Counter()
evidence_status = Counter()

for a in apps:
    for e in a.get("evidence", []):
        evidence_prov[e.get("provenance", "UNKNOWN")] += 1
        evidence_status[e.get("http_status", 0)] += 1
    for c in a.get("claims", []):
        claim_prov[c.get("provenance", "UNKNOWN")] += 1

print("\n--- EVIDENCE & CLAIMS PROVENANCE ---")
print(f"  Total Evidence URLs: {total_evidence}")
for p, cnt in evidence_prov.most_common():
    print(f"    Evidence Provenance {p}: {cnt}")
print("  Evidence HTTP Status Codes:")
for s, cnt in evidence_status.most_common():
    print(f"    HTTP {s}: {cnt}")

print(f"\n  Total Claims: {total_claims}")
for p, cnt in claim_prov.most_common():
    print(f"    Claim Provenance {p}: {cnt} ({cnt/total_claims*100:.1f}%)")

# 8. Category Breakdown
print("\n--- CATEGORY FEASIBILITY & COMPOSIO COVERAGE ---")
cat_stats = defaultdict(lambda: {"total": 0, "composio": 0, "rest": 0, "score": 0.0, "buildable_now": 0})
for a in apps:
    cat = a["category"]
    cat_stats[cat]["total"] += 1
    if a["mcp"].get("composio_tool_supported"):
        cat_stats[cat]["composio"] += 1
    if a["api_surface"].get("has_rest"):
        cat_stats[cat]["rest"] += 1
    if a["feasibility"].get("buildability") == "BUILDABLE_NOW":
        cat_stats[cat]["buildable_now"] += 1
    cat_stats[cat]["score"] += a["feasibility"].get("feasibility_score", 0.0)

for cat, stats in sorted(cat_stats.items(), key=lambda x: x[1]["score"]/x[1]["total"], reverse=True):
    avg = stats["score"] / stats["total"]
    print(f"  {cat:<38}: Avg Score: {avg:.1f}/10 | Composio: {stats['composio']}/{stats['total']} | REST: {stats['rest']}/{stats['total']} | Turnkey: {stats['buildable_now']}/{stats['total']}")

# 9. Top Integration Blockers
blockers_count = Counter()
for a in apps:
    for b in a["feasibility"].get("primary_blockers", []):
        blockers_count[b.get("title", "Unknown Blocker")] += 1

print("\n--- TOP INTEGRATION BLOCKERS ---")
for b, cnt in blockers_count.most_common(10):
    print(f"  {b}: {cnt}")
