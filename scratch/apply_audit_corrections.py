import json
import sys
sys.path.insert(0, ".")
from collections import Counter
from src.models.research import AppResearchResult

FILES = [
    "data/results/final_research_100.json",
    "data/results/verified_research.json",
]

MCP_OVERRIDES = {
    "ahrefs": {
        "availability": "OFFICIAL",
        "existing_servers": ["https://api.ahrefs.com/mcp/mcp"],
        "notes": "Official vendor-maintained remote MCP server hosted at https://api.ahrefs.com/mcp/mcp.",
    },
    "reducto": {
        "availability": "OFFICIAL",
        "existing_servers": ["https://docs.reducto.ai/mcp-server"],
        "notes": "Official vendor-maintained MCP server for document parsing and extraction (docs.reducto.ai/mcp-server).",
    },
    "se-ranking": {
        "availability": "OFFICIAL",
        "existing_servers": ["https://api.seranking.com/mcp"],
        "notes": "Official vendor-maintained remote MCP server hosted at https://api.seranking.com/mcp.",
    },
    "aircall": {
        "availability": "OFFICIAL",
        "existing_servers": ["https://mcp.aircall.io/mcp", "https://composio.dev/tools/aircall"],
        "notes": "Official vendor-maintained remote MCP server in beta (https://mcp.aircall.io/mcp); also natively supported in Composio.",
    },
    "neo4j": {
        "availability": "OFFICIAL",
        "existing_servers": ["https://github.com/neo4j-contrib/mcp-neo4j"],
        "notes": "Official vendor-maintained MCP server (neo4j-mcp-server by Neo4j Labs).",
    },
    "otter-ai": {
        "availability": "COMMUNITY",
        "existing_servers": ["https://github.com/mcp-servers/otter-mcp"],
        "notes": "Verified open-source community MCP server (otter-mcp); no official first-party vendor server.",
    },
    "youtube-transcript": {
        "availability": "COMMUNITY",
        "existing_servers": ["https://github.com/kimtaeyoon83/mcp-server-youtube-transcript"],
        "notes": "Verified open-source community MCP implementations (@kimtaeyoon83/mcp-server-youtube-transcript).",
    },
    "fathom": {
        "availability": "COMMUNITY",
        "existing_servers": ["https://github.com/Dot-Fun/fathom-mcp"],
        "notes": "Verified open-source community MCP server (Dot-Fun/fathom-mcp).",
    },
}

GENERATED_CONCLUSION_PHRASES = [
    "native composio",
    "no verified official mcp",
    "no server discovered",
    "application does not expose",
    "open source codebase available",
    "open source cli codebase available",
    "primary authentication method is",
    "authorization framework",
    "independent server at",
    "reference slack mcp",
    "official apify actor",
    "official firecrawl",
    "official vendor-maintained",
    "verified open-source community",
    "open-source community",
    "local cli utility",
    "consumer web",
    "free developer access: personal access tokens",
]

def process_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    apps = data["applications"]
    print(f"\n==========================================")
    print(f"PROCESSING: {path} ({len(apps)} apps)")
    print(f"==========================================")

    total_downgraded_claims = 0
    total_corrected_mcp_records = 0
    apps_with_downgrades = set()

    for a in apps:
        aid = a["app_id"]

        # 1. Apply MCP Overrides
        if aid in MCP_OVERRIDES:
            override = MCP_OVERRIDES[aid]
            a["mcp"]["availability"] = override["availability"]
            a["mcp"]["existing_servers"] = override["existing_servers"]
            a["mcp"]["notes"] = override["notes"]
            total_corrected_mcp_records += 1

        # 2. Audit Provenance of Claims
        real_snippets = [
            e.get("snippet", "") for e in a.get("evidence", [])
            if e.get("http_status") == 200 and e.get("snippet")
        ]

        for c in a.get("claims", []):
            fn = c.get("field_name", "")
            exc = c.get("supporting_excerpt", "") or ""
            val = c.get("extracted_value", "")
            prov = c.get("provenance", "")

            # If this is an MCP claim, keep value updated with application's current mcp availability
            if fn == "mcp.availability":
                c["extracted_value"] = a["mcp"]["availability"]
                c["supporting_excerpt"] = a["mcp"]["notes"]
                # MCP availability is determined from MCP registry research, not direct DOM scrape
                if c.get("provenance") == "LIVE_FETCHED":
                    c["provenance"] = "INFERRED"
                    total_downgraded_claims += 1
                    apps_with_downgrades.add(aid)
                if a["mcp"]["availability"] == "NO_KNOWN_MCP":
                    c["polarity"] = "NEGATIVE"
                else:
                    c["polarity"] = "POSITIVE"
                continue

            # Check other LIVE_FETCHED claims
            if prov == "LIVE_FETCHED":
                # Check if excerpt contains generated conclusion phrase
                is_generated = any(phrase in exc.lower() for phrase in GENERATED_CONCLUSION_PHRASES)
                # Check if excerpt matches any real fetched snippet
                matched_snippet = any(exc in s or s in exc for s in real_snippets)

                if is_generated or not matched_snippet or len(exc.strip()) < 10:
                    c["provenance"] = "INFERRED"
                    total_downgraded_claims += 1
                    apps_with_downgrades.add(aid)
                    # Check polarity
                    if any(neg in val.upper() for neg in ["NOT_APPLICABLE", "NONE", "FALSE", "UNKNOWN"]):
                        c["polarity"] = "NEGATIVE"
                    elif "does not" in exc.lower() or "no " in exc.lower():
                        c["polarity"] = "NEGATIVE"

    # Verify Pydantic Compliance
    for a in apps:
        AppResearchResult.model_validate(a)

    # Calculate metrics
    mcp_counts = Counter(a["mcp"]["availability"] for a in apps)
    comp_toolkits = [a for a in apps if a["mcp"].get("composio_tool_supported")]
    independent_mcp = [a for a in apps if a["mcp"]["availability"] in ["OFFICIAL", "COMMUNITY"]]
    
    prov_counts = Counter(c["provenance"] for a in apps for c in a.get("claims", []))
    pol_counts = Counter(c["polarity"] for a in apps for c in a.get("claims", []))

    print(f"Total claims evaluated: {sum(prov_counts.values())}")
    print(f"Claims downgraded from LIVE_FETCHED to INFERRED: {total_downgraded_claims}")
    print(f"Applications with claim downgrades: {len(apps_with_downgrades)}")
    print(f"MCP records corrected: {total_corrected_mcp_records}")
    print(f"\nProvenance Breakdown:")
    for p, count in prov_counts.most_common():
        print(f"  - {p}: {count} ({count/sum(prov_counts.values())*100:.1f}%)")
    print(f"\nPolarity Breakdown:")
    for pol, count in pol_counts.most_common():
        print(f"  - {pol}: {count} ({count/sum(pol_counts.values())*100:.1f}%)")

    print(f"\nMCP Classification Breakdown (N={len(apps)}):")
    for m, count in mcp_counts.most_common():
        print(f"  - {m}: {count} ({count/len(apps)*100:.1f}%)")
    print(f"Composio Native Toolkits: {len(comp_toolkits)} ({len(comp_toolkits)/len(apps)*100:.1f}%)")
    print(f"Independent MCP Platforms: {len(independent_mcp)} ({len(independent_mcp)/len(apps)*100:.1f}%)")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved {path}.")

if __name__ == "__main__":
    for p in FILES:
        process_file(p)
