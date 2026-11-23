"""
Tests for Benchmark Applications Dataset (data/apps.json).

Verifies strict dataset integrity:
- Exactly 100 applications are present.
- Exactly 10 categories are represented.
- Exactly 10 applications per category (balanced 10x10 benchmark).
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

EXPECTED_CATEGORIES = [
    "CRM and Sales",
    "Support and Helpdesk",
    "Communications and Messaging",
    "Marketing, Ads, Email and Social",
    "Ecommerce",
    "Data, SEO and Scraping",
    "Developer, Infra and Data Platforms",
    "Productivity and Project Management",
    "Finance and Fintech",
    "AI, Research and Media-native",
]


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
