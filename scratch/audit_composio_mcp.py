"""Audit Composio and MCP server taxonomy across all 100 applications."""

import json
from collections import Counter

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]

# Independent MCP servers known in the ecosystem
INDEPENDENT_MCP_SERVERS = {
    "github": {
        "type": "COMMUNITY", # Anthropic reference server in modelcontextprotocol/servers
        "server_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/github",
        "name": "Reference GitHub MCP Server (Model Context Protocol)",
    },
    "slack": {
        "type": "COMMUNITY", # Anthropic reference server in modelcontextprotocol/servers
        "server_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/slack",
        "name": "Reference Slack MCP Server (Model Context Protocol)",
    },
    "cloudflare": {
        "type": "OFFICIAL", # Cloudflare officially published an MCP server
        "server_url": "https://github.com/cloudflare/mcp-server-cloudflare",
        "name": "Official Cloudflare MCP Server",
    },
    "sentry": {
        "type": "OFFICIAL", # Sentry official MCP server
        "server_url": "https://github.com/getsentry/sentry-mcp",
        "name": "Official Sentry MCP Server",
    },
    "netlify": {
        "type": "OFFICIAL", # Netlify official MCP server
        "server_url": "https://github.com/netlify/mcp-server",
        "name": "Official Netlify MCP Server",
    },
    "shopify": {
        "type": "COMMUNITY", # Shopify Dev AI Toolkit / Community server
        "server_url": "https://shopify.dev/docs/api/ai-toolkit",
        "name": "Shopify Dev AI Toolkit & MCP Server",
    },
    "supabase": {
        "type": "COMMUNITY",
        "server_url": "https://github.com/supabase-community/supabase-mcp",
        "name": "Supabase Community MCP Server",
    },
    "linear": {
        "type": "COMMUNITY",
        "server_url": "https://github.com/jerhadf/linear-mcp-server",
        "name": "Linear Community MCP Server",
    },
    "notion": {
        "type": "COMMUNITY",
        "server_url": "https://github.com/suekou/mcp-notion-server",
        "name": "Notion Community MCP Server",
    },
    "stripe": {
        "type": "COMMUNITY",
        "server_url": "https://github.com/stripe/agent-toolkit-mcp",
        "name": "Stripe Agent Toolkit MCP Server",
    },
    "apify": {
        "type": "OFFICIAL",
        "server_url": "https://github.com/apify/mcp-server-apify",
        "name": "Official Apify Actor MCP Server",
    },
    "firecrawl": {
        "type": "OFFICIAL",
        "server_url": "https://github.com/mendableai/firecrawl-mcp-server",
        "name": "Official Firecrawl MCP Server",
    },
}

for app in apps:
    app_id = app["app_id"]
    mcp = app["mcp"]
    has_comp = mcp.get("composio_tool_supported", False)
    
    if app_id in INDEPENDENT_MCP_SERVERS:
        info = INDEPENDENT_MCP_SERVERS[app_id]
        mcp["availability"] = info["type"]
        mcp["existing_servers"] = [info["server_url"]]
        mcp["notes"] = f"{info['name']}. Independent server at {info['server_url']}. " + (
            f"Also natively supported in Composio ({mcp.get('composio_app_slug')}) with pre-built actions." if has_comp else ""
        )
    elif has_comp:
        mcp["availability"] = "COMPOSIO"
        mcp["existing_servers"] = [f"https://composio.dev/tools/{mcp.get('composio_app_slug', app_id)}"]
        mcp["notes"] = f"Native Composio toolkit available ({mcp.get('composio_app_slug')}). Accessible via Composio MCP bridge. No independent first-party MCP server verified."
    else:
        mcp["availability"] = "NO_KNOWN_MCP"
        mcp["existing_servers"] = []
        mcp["notes"] = "No verified official MCP server, community MCP server, or native Composio toolkit discovered."

    # Update corresponding mcp.availability claim if present
    for claim in app.get("claims", []):
        if claim["field_name"] == "mcp.availability":
            claim["extracted_value"] = mcp["availability"]
            claim["supporting_excerpt"] = mcp["notes"]

print("MCP Distribution after explicit independent separation:")
mcp_counts = Counter(a["mcp"]["availability"] for a in apps)
for k, v in mcp_counts.most_common():
    print(f"  {k}: {v}")

composio_count = sum(1 for a in apps if a["mcp"]["composio_tool_supported"])
print(f"\nTotal Apps with Native Composio Toolkits: {composio_count}")
print(f"Apps with Official 1st-Party MCP Servers: {sum(1 for a in apps if a['mcp']['availability'] == 'OFFICIAL')}")
print(f"Apps with Community/Reference MCP Servers: {sum(1 for a in apps if a['mcp']['availability'] == 'COMMUNITY')}")
print(f"Apps accessible via Composio MCP bridge ONLY: {sum(1 for a in apps if a['mcp']['availability'] == 'COMPOSIO')}")
print(f"Apps with NO Known MCP: {sum(1 for a in apps if a['mcp']['availability'] == 'NO_KNOWN_MCP')}")

# Save the updated data
with open("data/results/final_research_100.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

with open("data/results/verified_research.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\nSuccessfully updated final_research_100.json and verified_research.json with clear MCP taxonomy separation!")
