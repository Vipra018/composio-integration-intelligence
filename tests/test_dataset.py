"""
Tests for Benchmark Applications Dataset (data/apps.json).

Verifies strict dataset integrity:
- Exactly 100 applications are present.
- Exactly 10 categories are represented.
- Exactly 10 applications per category (balanced 10x10 benchmark).
- Explicit 1-to-1 matching against the canonical reference application list.
- Every application occurs exactly once (no duplicate IDs or names).
- All IDs follow canonical lowercase kebab-case naming.
- All URLs are valid HTTP/HTTPS endpoints.
- All fields adhere strictly to the AppMetadata Pydantic schema.
"""

from collections import Counter
import re
from typing import Any, Dict, List
import pytest
from pydantic import ValidationError

from src.models.app_metadata import AppMetadata

# The 10 canonical categories defined in the assignment
EXPECTED_CATEGORIES = [
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

# The complete 100-application canonical reference mapping (Name -> Category)
CANONICAL_APPLICATION_MAP: Dict[str, str] = {
    # 1. CRM and Sales (10)
    "Salesforce": "CRM and Sales",
    "HubSpot": "CRM and Sales",
    "Pipedrive": "CRM and Sales",
    "Close": "CRM and Sales",
    "Zoho CRM": "CRM and Sales",
    "Copper": "CRM and Sales",
    "Outreach": "CRM and Sales",
    "Salesloft": "CRM and Sales",
    "Apollo.io": "CRM and Sales",
    "Gong": "CRM and Sales",

    # 2. Support and Helpdesk (10)
    "Zendesk": "Support and Helpdesk",
    "Freshdesk": "Support and Helpdesk",
    "Help Scout": "Support and Helpdesk",
    "Gorgias": "Support and Helpdesk",
    "Kustomer": "Support and Helpdesk",
    "Front": "Support and Helpdesk",
    "PagerDuty": "Support and Helpdesk",
    "Vanta": "Support and Helpdesk",
    "Greenhouse": "Support and Helpdesk",
    "Lever": "Support and Helpdesk",

    # 3. Communications and Messaging (10)
    "Slack": "Communications and Messaging",
    "Discord": "Communications and Messaging",
    "Twilio": "Communications and Messaging",
    "SendGrid": "Communications and Messaging",
    "Zoom": "Communications and Messaging",
    "Intercom": "Communications and Messaging",
    "Crisp": "Communications and Messaging",
    "Basecamp": "Communications and Messaging",
    "Ashby": "Communications and Messaging",
    "HiBob": "Communications and Messaging",

    # 4. Marketing, Ads, Email and Social (10)
    "Mailchimp": "Marketing, Ads, Email and Social",
    "Klaviyo": "Marketing, Ads, Email and Social",
    "ActiveCampaign": "Marketing, Ads, Email and Social",
    "Customer.io": "Marketing, Ads, Email and Social",
    "Braze": "Marketing, Ads, Email and Social",
    "Kit": "Marketing, Ads, Email and Social",
    "Brevo": "Marketing, Ads, Email and Social",
    "Buffer": "Marketing, Ads, Email and Social",
    "Hootsuite": "Marketing, Ads, Email and Social",
    "Webflow": "Marketing, Ads, Email and Social",

    # 5. Ecommerce (10)
    "Shopify": "Ecommerce",
    "WooCommerce": "Ecommerce",
    "BigCommerce": "Ecommerce",
    "Shippo": "Ecommerce",
    "ShipStation": "Ecommerce",
    "Stripe": "Ecommerce",
    "Chargebee": "Ecommerce",
    "Recurly": "Ecommerce",
    "Bill.com": "Ecommerce",
    "Wave Accounting": "Ecommerce",

    # 6. Data, SEO and Scraping (10)
    "Snowflake": "Data, SEO and Scraping",
    "Datadog": "Data, SEO and Scraping",
    "New Relic": "Data, SEO and Scraping",
    "Sentry": "Data, SEO and Scraping",
    "Postman": "Data, SEO and Scraping",
    "Airtable": "Data, SEO and Scraping",
    "Typeform": "Data, SEO and Scraping",
    "SurveyMonkey": "Data, SEO and Scraping",
    "Okta": "Data, SEO and Scraping",
    "1Password": "Data, SEO and Scraping",

    # 7. Developer, Infra and Data platforms (10)
    "GitHub": "Developer, Infra and Data platforms",
    "GitLab": "Developer, Infra and Data platforms",
    "Bitbucket": "Developer, Infra and Data platforms",
    "Vercel": "Developer, Infra and Data platforms",
    "Supabase": "Developer, Infra and Data platforms",
    "Neon": "Developer, Infra and Data platforms",
    "Render": "Developer, Infra and Data platforms",
    "CircleCI": "Developer, Infra and Data platforms",
    "Docker Hub": "Developer, Infra and Data platforms",
    "Terraform Cloud": "Developer, Infra and Data platforms",

    # 8. Productivity and Project Management (10)
    "Notion": "Productivity and Project Management",
    "Linear": "Productivity and Project Management",
    "Asana": "Productivity and Project Management",
    "Monday.com": "Productivity and Project Management",
    "ClickUp": "Productivity and Project Management",
    "Jira": "Productivity and Project Management",
    "Confluence": "Productivity and Project Management",
    "Trello": "Productivity and Project Management",
    "Todoist": "Productivity and Project Management",
    "LaunchDarkly": "Productivity and Project Management",

    # 9. Finance and Fintech (10)
    "QuickBooks Online": "Finance and Fintech",
    "Xero": "Finance and Fintech",
    "Brex": "Finance and Fintech",
    "Ramp": "Finance and Fintech",
    "Gusto": "Finance and Fintech",
    "BambooHR": "Finance and Fintech",
    "Rippling": "Finance and Fintech",
    "Deel": "Finance and Fintech",
    "Workday": "Finance and Fintech",
    "Remote": "Finance and Fintech",

    # 10. AI, Research and Media-native (10)
    "Pinecone": "AI, Research and Media-native",
    "Canva": "AI, Research and Media-native",
    "Figma": "AI, Research and Media-native",
    "Miro": "AI, Research and Media-native",
    "Coda": "AI, Research and Media-native",
    "Google Drive": "AI, Research and Media-native",
    "Box": "AI, Research and Media-native",
    "Dropbox": "AI, Research and Media-native",
    "DocuSign": "AI, Research and Media-native",
    "PandaDoc": "AI, Research and Media-native",
}


def test_dataset_exact_count(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify that exactly 100 applications are present in the dataset."""
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


def test_dataset_matches_canonical_reference(raw_dataset: List[Dict[str, Any]]) -> None:
    """
    Explicit test comparing every application name and its category assignment
    against the canonical 100-app reference list.
    """
    dataset_apps = {app["name"]: app.get("category") for app in raw_dataset}

    missing_apps = set(CANONICAL_APPLICATION_MAP.keys()) - set(dataset_apps.keys())
    assert not missing_apps, f"Missing applications from canonical list: {missing_apps}"

    extra_apps = set(dataset_apps.keys()) - set(CANONICAL_APPLICATION_MAP.keys())
    assert not extra_apps, f"Unexpected extra applications present: {extra_apps}"

    category_mismatches = []
    for app_name, expected_cat in CANONICAL_APPLICATION_MAP.items():
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
    required_keys = ["id", "name", "category", "website", "documentation_url", "description"]
    for idx, app in enumerate(raw_dataset):
        for key in required_keys:
            val = app.get(key)
            assert val is not None and str(val).strip() != "", (
                f"Missing or empty required field '{key}' in app at index {idx} ({app.get('name', 'UNKNOWN')})"
            )


def test_dataset_url_schemes(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify all website and documentation URLs start with https:// or http://."""
    for app in raw_dataset:
        website = str(app.get("website", ""))
        doc_url = str(app.get("documentation_url", ""))
        assert website.startswith("http://") or website.startswith("https://"), (
            f"Invalid website URL for {app.get('name')}: {website}"
        )
        assert doc_url.startswith("http://") or doc_url.startswith("https://"), (
            f"Invalid doc URL for {app.get('name')}: {doc_url}"
        )


def test_dataset_descriptions_quality(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify descriptions are concise, meaningful and informative."""
    for app in raw_dataset:
        desc = app.get("description", "")
        assert len(desc) >= 20, f"Description too short (<20 chars) for {app.get('name')}: '{desc}'"
        assert len(desc) <= 500, f"Description too long (>500 chars) for {app.get('name')}"


def test_dataset_pydantic_validation(raw_dataset: List[Dict[str, Any]]) -> None:
    """Verify that every application passes Pydantic schema validation."""
    for app in raw_dataset:
        try:
            validated = AppMetadata.model_validate(app)
            assert validated.id == app["id"]
        except ValidationError as err:
            pytest.fail(f"Validation failed for app '{app.get('name', 'UNKNOWN')}': {err}")
