"""
Tests verifying the final data quality, MCP classification, and provenance audit corrections.
"""

import json
from collections import Counter
from pathlib import Path

import pytest

from src.models.enums import MCPAvailability, Provenance
from src.models.research import AppResearchResult


@pytest.fixture(scope="module")
def research_data() -> dict:
    data_path = Path("data/results/final_research_100.json")
    assert data_path.exists(), "final_research_100.json must exist"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_target_mcp_classifications(research_data: dict) -> None:
    """Verify specific investigated applications have accurate MCP classifications."""
    apps_by_id = {a["app_id"]: a for a in research_data["applications"]}

    # 1. Ahrefs: Official remote streamable MCP server
    assert apps_by_id["ahrefs"]["mcp"]["availability"] == MCPAvailability.OFFICIAL
    assert any("ahrefs.com" in s for s in apps_by_id["ahrefs"]["mcp"]["existing_servers"])

    # 2. Reducto: Official document parsing MCP server
    assert apps_by_id["reducto"]["mcp"]["availability"] == MCPAvailability.OFFICIAL
    assert any("reducto.ai" in s for s in apps_by_id["reducto"]["mcp"]["existing_servers"])

    # 3. SE Ranking: Official remote streamable MCP server
    assert apps_by_id["se-ranking"]["mcp"]["availability"] == MCPAvailability.OFFICIAL
    assert any("seranking.com" in s for s in apps_by_id["se-ranking"]["mcp"]["existing_servers"])

    # 4. Aircall: Official first-party remote MCP server AND native Composio toolkit
    assert apps_by_id["aircall"]["mcp"]["availability"] == MCPAvailability.OFFICIAL
    assert apps_by_id["aircall"]["mcp"]["composio_tool_supported"] is True
    assert apps_by_id["aircall"]["mcp"]["composio_app_slug"] == "aircall"

    # 5. Neo4j: Official vendor-maintained MCP server
    assert apps_by_id["neo4j"]["mcp"]["availability"] == MCPAvailability.OFFICIAL

    # 6. Otter AI: Community open-source MCP server (otter-mcp)
    assert apps_by_id["otter-ai"]["mcp"]["availability"] == MCPAvailability.COMMUNITY

    # 7. YouTube Transcript: Community open-source MCP server
    assert apps_by_id["youtube-transcript"]["mcp"]["availability"] == MCPAvailability.COMMUNITY

    # 8. Fathom: Community open-source MCP server
    assert apps_by_id["fathom"]["mcp"]["availability"] == MCPAvailability.COMMUNITY


def test_mcp_counts_reconcile_to_100(research_data: dict) -> None:
    """Verify all 100 applications reconcile across MCP categories."""
    apps = research_data["applications"]
    assert len(apps) == 100

    counts = Counter(a["mcp"]["availability"] for a in apps)
    assert counts[MCPAvailability.OFFICIAL] == 10
    assert counts[MCPAvailability.COMMUNITY] == 10
    assert counts[MCPAvailability.COMPOSIO] == 53
    assert counts[MCPAvailability.NO_KNOWN_MCP] == 27
    assert sum(counts.values()) == 100

    # Independent MCP servers = 10 official + 10 community = 20
    independent_mcp = [a for a in apps if a["mcp"]["availability"] in (MCPAvailability.OFFICIAL, MCPAvailability.COMMUNITY)]
    assert len(independent_mcp) == 20

    # Composio native toolkits = 66 (independent of MCP server status)
    composio_toolkits = [a for a in apps if a["mcp"]["composio_tool_supported"]]
    assert len(composio_toolkits) == 66


def test_provenance_integrity_no_generated_live_claims(research_data: dict) -> None:
    """Verify that LIVE_FETCHED claims never present generated conclusions as source quotes."""
    apps = research_data["applications"]

    generated_phrases = [
        "native composio",
        "no verified official mcp",
        "no server discovered",
        "application does not expose api authentication",
        "open source codebase available without credential gating",
        "open source cli codebase available without credential gating",
        "primary authentication method is oauth",
        "reference slack mcp",
        "official apify actor",
        "official firecrawl",
        "local cli utility",
        "consumer web interface",
    ]

    live_count = 0
    for a in apps:
        for c in a.get("claims", []):
            if c.get("provenance") == Provenance.LIVE_FETCHED:
                live_count += 1
                excerpt = (c.get("supporting_excerpt") or "").lower()
                # Must have source URL
                assert c.get("source_url") is not None, f"LIVE_FETCHED claim missing source_url in {a['app_id']}"
                # Must not contain generated summary phrases
                for phrase in generated_phrases:
                    assert phrase not in excerpt, (
                        f"Found generated phrase '{phrase}' in LIVE_FETCHED claim: {c['field_name']} for {a['app_id']}"
                    )

    assert live_count == 92, f"Expected exactly 92 genuine LIVE_FETCHED claims, found {live_count}"


def test_negative_findings_not_marked_live_fetched(research_data: dict) -> None:
    """Verify negative findings (like NO_KNOWN_MCP) are INFERRED or UNKNOWN, not LIVE_FETCHED."""
    apps = research_data["applications"]

    for a in apps:
        for c in a.get("claims", []):
            if c.get("field_name") == "mcp.availability" and c.get("extracted_value") == "NO_KNOWN_MCP":
                assert c.get("provenance") != Provenance.LIVE_FETCHED, (
                    f"NO_KNOWN_MCP claim in {a['app_id']} must not be marked LIVE_FETCHED"
                )
                assert c.get("polarity") in ("NEGATIVE", "ABSENT")


def test_orthogonality_and_denominators(research_data: dict) -> None:
    """Verify taxonomy orthogonality: mode, applicability, auth method."""
    apps = research_data["applications"]

    # 1. Integration Mode
    modes = Counter(a["auth"]["integration_mode"] for a in apps)
    assert modes["API"] == 94
    assert modes["WEB_ONLY"] == 4
    assert modes["CLI / LOCAL_PROCESS"] == 2
    assert sum(modes.values()) == 100

    # 2. Auth Applicability
    apps_app = Counter(a["auth"]["auth_applicability"] for a in apps)
    assert apps_app["APPLICABLE"] == 94
    assert apps_app["NOT_APPLICABLE"] == 6

    # 3. Known Auth Methods (denominator N=60)
    applicable = [a for a in apps if a["auth"]["auth_applicability"] == "APPLICABLE"]
    known_auth = [a for a in applicable if a["auth"]["primary_method"] != "UNKNOWN"]
    unknown_auth = [a for a in applicable if a["auth"]["primary_method"] == "UNKNOWN"]
    assert len(known_auth) == 60
    assert len(unknown_auth) == 34

    methods = Counter(a["auth"]["primary_method"] for a in known_auth)
    assert methods["API_KEY"] == 27
    assert methods["OAUTH2"] == 24
    assert methods["TOKEN / PAT"] == 7
    assert methods["BASIC"] == 2
    assert sum(methods.values()) == 60

    # 4. Credential Access (16 free, 84 unknown)
    creds = Counter(a["auth"]["credential_accessibility"] for a in apps)
    assert creds["SELF_SERVE_FREE"] == 16
    assert creds["UNKNOWN"] == 84
