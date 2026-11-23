"""Compute strict audited metrics with explicit denominators."""

import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]
total = len(apps)

# Auth
primary_counts = {}
for a in apps:
    p = a["auth"]["primary_method"]
    primary_counts[p] = primary_counts.get(p, 0) + 1

known_auth_total = total - primary_counts.get("UNKNOWN", 0)
print(f"Total Apps: {total}, Known Auth Apps: {known_auth_total}")
for k, v in primary_counts.items():
    pct_total = v / total * 100
    pct_known = (v / known_auth_total * 100) if k != "UNKNOWN" else 0.0
    print(f"  {k}: {v} (Total: {pct_total:.1f}%, Known Denominator: {pct_known:.1f}%)")

# Breadth
breadth_counts = {}
for a in apps:
    b = a["api_surface"]["breadth"]
    breadth_counts[b] = breadth_counts.get(b, 0) + 1

known_breadth_total = total - breadth_counts.get("UNKNOWN", 0)
print(f"\nKnown Breadth Apps: {known_breadth_total}")
for k, v in breadth_counts.items():
    pct_total = v / total * 100
    pct_known = (v / known_breadth_total * 100) if k != "UNKNOWN" else 0.0
    print(f"  {b}: {v} (Total: {pct_total:.1f}%, Known Denominator: {pct_known:.1f}%)")

# MCP
mcp_counts = {}
for a in apps:
    m = a["mcp"]["availability"]
    mcp_counts[m] = mcp_counts.get(m, 0) + 1

print("\nMCP Availability:")
for k, v in mcp_counts.items():
    print(f"  {k}: {v} ({v/total*100:.1f}%)")

comp_tools = sum(1 for a in apps if a["mcp"]["composio_tool_supported"])
print(f"Native Composio Toolkits: {comp_tools} ({comp_tools/total*100:.1f}%)")
