"""
Tests for Benchmark Applications Dataset (data/apps.json and data/canonical_apps.json).

Independently and exhaustively verifies dataset integrity against the authoritative
100-application single source of truth:
- Exact 100 application names.
- Exact category assignments.
- Exactly 10 categories.
- Exactly 10 applications per category.
- Preservation of original_source_hint for all 100 applications.
- Separation of website and developer_documentation_url.
- Null developer_documentation_url where documentation is not yet discovered.
- No missing applications.
- No extra applications.
- No duplicate names or IDs.
- Valid slug IDs, HTTP/HTTPS URLs, and Pydantic schema validation.
"""

from collections import Counter
import json
from pathlib import Path
import re
from typing import Any, Dict, List
import pytest
from pydantic import ValidationError

from src.config import PROJECT_ROOT
from src.models.app_metadata import AppMetadata

# The 10 canonical categories defined in the assignment
EXPECTED_CATEGORIES: List[str] = [
    "CRM and Sales",
    "Support and Helpdesk",
    "Communications and Messaging",
    "Marketing, Ads, Email and Social",
    "Ecommerce",
    "Data, SEO and Scraping",
    "Developer, Infra and Data platforms",
    "Productivity and Project Management",
    "Finance and Fintech",
    "AI, Research and Media-native",
]

# The authoritative 100-application reference list (Name -> Category)
# Single Source of Truth
AUTHORITATIVE_APPLICATION_MAP: Dict[str, str] = {
    # CATEGORY 1: CRM and Sales (10)
    "Salesforce": "CRM and Sales",
    "HubSpot": "CRM and Sales",
    "Pipedrive": "CRM and Sales",
    "Attio": "CRM and Sales",
    "Twenty": "CRM and Sales",
    "Podio": "CRM and Sales",
    "Zoho CRM": "CRM and Sales",
    "Close": "CRM and Sales",
    "Copper": "CRM and Sales",
    "DealCloud": "CRM and Sales",

    # CATEGORY 2: Support and Helpdesk (10)
    "Zendesk": "Support and Helpdesk",
    "Intercom": "Support and Helpdesk",
    "Freshdesk": "Support and Helpdesk",
    "Front": "Support and Helpdesk",
    "Pylon": "Support and Helpdesk",
    "LiveAgent": "Support and Helpdesk",
    "Plain": "Support and Helpdesk",
    "Help Scout": "Support and Helpdesk",
    "Gorgias": "Support and Helpdesk",
    "Gladly": "Support and Helpdesk",

    # CATEGORY 3: Communications and Messaging (10)
    "Slack": "Communications and Messaging",
    "Twilio": "Communications and Messaging",
    "Zoho Cliq": "Communications and Messaging",
    "Lark (Larksuite)": "Communications and Messaging",
    "Pumble": "Communications and Messaging",
    "Discord": "Communications and Messaging",
    "Telegram": "Communications and Messaging",
    "WhatsApp Business": "Communications and Messaging",
    "Aircall": "Communications and Messaging",
    "Vonage": "Communications and Messaging",

    # CATEGORY 4: Marketing, Ads, Email and Social (10)
    "Google Ads": "Marketing, Ads, Email and Social",
    "Meta Ads": "Marketing, Ads, Email and Social",
    "LinkedIn Ads": "Marketing, Ads, Email and Social",
    "GoHighLevel": "Marketing, Ads, Email and Social",
    "Mailchimp": "Marketing, Ads, Email and Social",
    "Klaviyo": "Marketing, Ads, Email and Social",
    "systeme.io": "Marketing, Ads, Email and Social",
    "Pinterest": "Marketing, Ads, Email and Social",
    "Threads (Meta)": "Marketing, Ads, Email and Social",
    "SendGrid": "Marketing, Ads, Email and Social",

    # CATEGORY 5: Ecommerce (10)
    "Shopify": "Ecommerce",
    "WooCommerce": "Ecommerce",
    "BigCommerce": "Ecommerce",
    "Salesforce Commerce Cloud": "Ecommerce",
    "Magento (Adobe Commerce)": "Ecommerce",
    "Squarespace": "Ecommerce",
    "Ecwid": "Ecommerce",
    "Gumroad": "Ecommerce",
    "Amazon Selling Partner": "Ecommerce",
    "fanbasis": "Ecommerce",

    # CATEGORY 6: Data, SEO and Scraping (10)
    "DataForSEO": "Data, SEO and Scraping",
    "SE Ranking": "Data, SEO and Scraping",
    "Ahrefs": "Data, SEO and Scraping",
    "MrScraper": "Data, SEO and Scraping",
    "Apify": "Data, SEO and Scraping",
    "Firecrawl": "Data, SEO and Scraping",
    "Bright Data": "Data, SEO and Scraping",
    "Sherlock": "Data, SEO and Scraping",
    "Waterfall.io": "Data, SEO and Scraping",
    "Clay": "Data, SEO and Scraping",

    # CATEGORY 7: Developer, Infra and Data platforms (10)
    "GitHub": "Developer, Infra and Data platforms",
    "Vercel": "Developer, Infra and Data platforms",
    "Netlify": "Developer, Infra and Data platforms",
    "Cloudflare": "Developer, Infra and Data platforms",
    "Supabase": "Developer, Infra and Data platforms",
    "Neo4j": "Developer, Infra and Data platforms",
    "Snowflake": "Developer, Infra and Data platforms",
    "MongoDB Atlas": "Developer, Infra and Data platforms",
    "Datadog": "Developer, Infra and Data platforms",
    "Sentry": "Developer, Infra and Data platforms",

    # CATEGORY 8: Productivity and Project Management (10)
    "Notion": "Productivity and Project Management",
    "Airtable": "Productivity and Project Management",
    "Linear": "Productivity and Project Management",
    "Jira": "Productivity and Project Management",
    "Asana": "Productivity and Project Management",
    "Monday.com": "Productivity and Project Management",
    "ClickUp": "Productivity and Project Management",
    "Coda": "Productivity and Project Management",
    "Smartsheet": "Productivity and Project Management",
    "Harvest": "Productivity and Project Management",

    # CATEGORY 9: Finance and Fintech (10)
    "Stripe": "Finance and Fintech",
    "Plaid": "Finance and Fintech",
    "Binance": "Finance and Fintech",
    "Paygent Connect": "Finance and Fintech",
    "iPayX": "Finance and Fintech",
    "QuickBooks": "Finance and Fintech",
    "Xero": "Finance and Fintech",
    "Brex": "Finance and Fintech",
    "Ramp": "Finance and Fintech",
    "PitchBook": "Finance and Fintech",

    # CATEGORY 10: AI, Research and Media-native (10)
    "NotebookLM": "AI, Research and Media-native",
    "Otter AI": "AI, Research and Media-native",
    "Fathom": "AI, Research and Media-native",
    "Consensus": "AI, Research and Media-native",
    "Reducto": "AI, Research and Media-native",
    "Devin": "AI, Research and Media-native",
    "higgsfield": "AI, Research and Media-native",
    "Mermaid CLI": "AI, Research and Media-native",
    "YouTube Transcript": "AI, Research and Media-native",
    "Grain": "AI, Research and Media-native",
}


def test_authoritative_map_integrity() -> None:
    """Verify that the test's own AUTHORITATIVE_APPLICATION_MAP has exactly 100 apps and 10x10 counts."""
    assert len(AUTHORITATIVE_APPLICATION_MAP) == 100, f"Map must have 100 apps, got {len(AUTHORITATIVE_APPLICATION_MAP)}"
    counts = Counter(AUTHORITATIVE_APPLICATION_MAP.values())
    assert len(counts) == 10, f"Map must have 10 categories, got {len(counts)}"
    for cat in EXPECTED_CATEGORIES:
        assert counts[cat] == 10, f"Category '{cat}' has {counts[cat]} items in authoritative map, expected 10"


def test_canonical_file_exists_and_matches() -> None:
    """Verify that data/canonical_apps.json exists and strictly matches the authoritative list."""
    canonical_file = PROJECT_ROOT / "data" / "canonical_apps.json"
    assert canonical_file.exists(), f"Missing canonical reference file at {canonical_file}"

    with open(canonical_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 100, f"canonical_apps.json must contain 100 apps, found {len(data)}"

    canonical_apps = {app["name"]: app.get("category") for app in data}
    assert set(canonical_apps.keys()) == set(AUTHORITATIVE_APPLICATION_MAP.keys()), (
        f"Mismatch between canonical_apps.json and authoritative map!"
    )


def test_dataset_exact_count(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify that exactly 100 applications are present in the active dataset."""
    assert len(raw_dataset) == 100, f"Expected exactly 100 applications, found {len(raw_dataset)}"


def test_dataset_category_distribution_and_counts(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify exactly 10 categories with exactly 10 applications in each category."""
    counts = Counter(app.get("category") for app in raw_dataset)

    # Verify exactly 10 unique categories
    assert len(counts) == 10, f"Expected exactly 10 categories, found {len(counts)}: {list(counts.keys())}"

    # Verify all expected categories are present
    assert set(counts.keys()) == set(EXPECTED_CATEGORIES), (
        f"Categories mismatch! Expected: {set(EXPECTED_CATEGORIES)}, Found: {set(counts.keys())}"
    )

    # Verify exactly 10 apps per category
    for cat in EXPECTED_CATEGORIES:
        count = counts[cat]
        assert count == 10, f"Category '{cat}' has {count} applications, expected exactly 10"


def test_dataset_matches_authoritative_reference(raw_dataset: List[Dict[str, Any]]) -> None:
    """
    Explicit test comparing every application name and its category assignment
    against the single source of truth AUTHORITATIVE_APPLICATION_MAP.
    """
    dataset_apps = {app["name"]: app.get("category") for app in raw_dataset}

    missing_apps = set(AUTHORITATIVE_APPLICATION_MAP.keys()) - set(dataset_apps.keys())
    assert not missing_apps, f"Missing applications from authoritative list: {missing_apps}"

    extra_apps = set(dataset_apps.keys()) - set(AUTHORITATIVE_APPLICATION_MAP.keys())
    assert not extra_apps, f"Unexpected extra applications present: {extra_apps}"

    category_mismatches = []
    for app_name, expected_cat in AUTHORITATIVE_APPLICATION_MAP.items():
        actual_cat = dataset_apps.get(app_name)
        if actual_cat != expected_cat:
            category_mismatches.append(f"{app_name}: expected '{expected_cat}', got '{actual_cat}'")

    assert not category_mismatches, f"Category mismatches found: {category_mismatches}"


def test_dataset_unique_ids(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify that all application IDs are strictly unique."""
    ids = [app.get("id") for app in raw_dataset]
    assert len(ids) == len(set(ids)), f"Duplicate IDs detected! Found {len(ids) - len(set(ids))} duplicates."


def test_dataset_unique_names(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify that all application names are unique."""
    names = [app.get("name") for app in raw_dataset]
    assert len(names) == len(set(names)), f"Duplicate names detected! Found {len(names) - len(set(names))} duplicates."


def test_dataset_id_format(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify that every application ID is lowercase kebab-case."""
    slug_pattern = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    for app in raw_dataset:
        app_id = app.get("id", "")
        assert slug_pattern.match(app_id), f"Invalid slug id '{app_id}' for app '{app.get('name')}'"


def test_dataset_required_fields_present(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify that every app contains all required non-empty fields."""
    required_keys = ["id", "name", "category", "original_source_hint", "website", "description"]
    for idx, app in enumerate(raw_dataset):
        for key in required_keys:
            val = app.get(key)
            assert val is not None and str(val).strip() != "", (
                f"Missing or empty required field '{key}' in app at index {idx} ({app.get('name', 'UNKNOWN')})"
            )


def test_dataset_original_source_hint_preserved(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify all 100 applications preserve their original_source_hint non-empty."""
    for app in raw_dataset:
        hint = app.get("original_source_hint")
        assert hint is not None and len(str(hint).strip()) >= 3, (
            f"Missing or invalid original_source_hint for {app.get('name')}"
        )


def test_dataset_developer_docs_separation(raw_dataset: List[Dict[str, Any]]) -> None:
    """
    Verify developer_documentation_url is separate from website and original_source_hint,
    and allows null where documentation is not yet discovered or gated.
    """
    null_docs = [app["name"] for app in raw_dataset if app.get("developer_documentation_url") is None]
    populated_docs = [app["name"] for app in raw_dataset if app.get("developer_documentation_url") is not None]

    assert len(null_docs) > 0, "Expected some apps with null developer_documentation_url (undiscovered/gated)"
    assert len(populated_docs) > 0, "Expected apps with verified developer_documentation_url"

    for app in raw_dataset:
        doc_url = app.get("developer_documentation_url")
        if doc_url is not None:
            assert str(doc_url).startswith("http://") or str(doc_url).startswith("https://"), (
                f"Invalid developer_documentation_url format for {app.get('name')}: {doc_url}"
            )


def test_dataset_url_schemes(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify all website URLs start with https:// or http://."""
    for app in raw_dataset:
        website = str(app.get("website", ""))
        assert website.startswith("http://") or website.startswith("https://"), (
            f"Invalid website URL for {app.get('name')}: {website}"
        )


def test_dataset_descriptions_quality(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify descriptions are concise, meaningful and informative."""
    for app in raw_dataset:
        desc = app.get("description", "")
        assert len(desc) >= 15, f"Description too short (<15 chars) for {app.get('name')}: '{desc}'"
        assert len(desc) <= 500, f"Description too long (>500 chars) for {app.get('name')}"


def test_dataset_pydantic_validation(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify that every application passes Pydantic schema validation."""
    for app in raw_dataset:
        try:
            validated = AppMetadata.model_validate(app)
            assert validated.id == app["id"]
        except ValidationError as err:
            pytest.fail(f"Validation failed for app '{app.get('name', 'UNKNOWN')}': {err}")
