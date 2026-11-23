"""
Pytest fixtures for Integration Intelligence test suite.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
import pytest

from src.config import PROJECT_ROOT, Settings
from src.models.app_metadata import AppMetadata


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Fixture providing repository root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def raw_dataset_path(project_root: Path) -> Path:
    """Fixture providing path to apps.json."""
    return project_root / "data" / "apps.json"


@pytest.fixture(scope="session")
def raw_dataset(raw_dataset_path: Path) -> List[Dict[str, Any]]:
    """Fixture providing raw deserialized list of applications."""
    assert raw_dataset_path.exists(), f"Dataset file missing at {raw_dataset_path}"
    with open(raw_dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "Dataset must be a JSON array"
    return data


@pytest.fixture(scope="session")
def validated_apps(raw_dataset: List[Dict[str, Any]]) -> List[AppMetadata]:
    """Fixture providing Pydantic-validated AppMetadata instances."""
    return [AppMetadata.model_validate(app) for app in raw_dataset]


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Fixture providing isolated Settings with temporary directories."""
    return Settings(
        environment="testing",
        results_dir=tmp_path / "results",
        reports_dir=tmp_path / "reports",
        log_file_path=tmp_path / "logs" / "test.log",
    )
