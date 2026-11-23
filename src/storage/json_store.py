"""Thread-safe, atomic JSON storage for application research results."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set

from src.config import get_settings
from src.exceptions import StorageError
from src.logging_utils import get_logger
from src.models.research import AppResearchResult

logger = get_logger("storage.json_store")


class JSONStore:
    """Manages persistence of AppResearchResult objects to JSON files."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        """Initialize the storage manager with a target directory.

        Args:
            base_dir: Base directory for storing results. Defaults to settings.results_dir.
        """
        settings = get_settings()
        self.base_dir = Path(base_dir) if base_dir else settings.results_dir
        self.individual_dir = self.base_dir / "individual"
        self.initial_research_file = self.base_dir / "initial_research.json"
        self.verified_research_file = self.base_dir / "verified_research.json"

        # Ensure directories exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.individual_dir.mkdir(parents=True, exist_ok=True)

    def _atomic_write_text(self, target_path: Path, content: str) -> None:
        """Atomically write text to target file using a temporary file."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # Create temp file in the same directory to ensure same filesystem for atomic rename
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=target_path.parent,
                delete=False,
                suffix=".tmp",
            ) as f:
                temp_file = Path(f.name)
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            # Atomic replace (Windows supports os.replace atomically on same volume)
            os.replace(temp_file, target_path)
        except Exception as e:
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            logger.error("Failed to write atomically to %s: %s", target_path, e)
            raise StorageError(f"Failed to write to {target_path}: {e}") from e

    def save_app_result(self, result: AppResearchResult) -> Path:
        """Save a single application research result.

        Args:
            result: The AppResearchResult to persist.

        Returns:
            The Path to the saved individual JSON file.
        """
        target_path = self.individual_dir / f"{result.app_id}.json"
        try:
            json_str = result.model_dump_json(indent=2)
            self._atomic_write_text(target_path, json_str)
            logger.debug("Successfully saved research result for %s to %s", result.app_id, target_path)
            return target_path
        except Exception as e:
            raise StorageError(f"Could not save result for app {result.app_id}: {e}") from e

    def load_app_result(self, app_id: str) -> Optional[AppResearchResult]:
        """Load a single application research result if it exists.

        Args:
            app_id: The ID of the application.

        Returns:
            The AppResearchResult, or None if not found.
        """
        target_path = self.individual_dir / f"{app_id}.json"
        if not target_path.exists():
            return None

        try:
            content = target_path.read_text(encoding="utf-8")
            return AppResearchResult.model_validate_json(content)
        except Exception as e:
            logger.error("Error reading result for %s: %s", app_id, e)
            raise StorageError(f"Failed to load result for app {app_id}: {e}") from e

    def has_checkpoint(self, app_id: str) -> bool:
        """Check whether a checkpoint exists for the given app_id."""
        return (self.individual_dir / f"{app_id}.json").exists()

    def get_completed_app_ids(self) -> Set[str]:
        """Return the set of all completed app IDs saved in individual storage."""
        if not self.individual_dir.exists():
            return set()
        return {p.stem for p in self.individual_dir.glob("*.json")}

    def list_results(self) -> List[AppResearchResult]:
        """Return a list of all currently saved AppResearchResult objects."""
        results = []
        for app_id in sorted(self.get_completed_app_ids()):
            res = self.load_app_result(app_id)
            if res:
                results.append(res)
        return results

    def save_all_results(
        self,
        results: Dict[str, AppResearchResult] | List[AppResearchResult],
        filepath: Optional[Path] = None,
    ) -> Path:
        """Save a collection of AppResearchResults into an aggregated JSON file.

        Args:
            results: List or mapping of AppResearchResult objects.
            filepath: Optional destination path (defaults to initial_research_file).

        Returns:
            The destination Path.
        """
        target_path = Path(filepath) if filepath else self.initial_research_file

        if isinstance(results, dict):
            item_list = list(results.values())
        else:
            item_list = list(results)

        # Sort predictably by app_id
        item_list.sort(key=lambda r: r.app_id)

        try:
            # We serialize as a top-level dictionary or list; a list of dicts is standard
            # We also include metadata header if desired, or a plain list
            # Let's save as structured dict: {"count": len, "applications": [ ... ]}
            # and also support direct list representation or dict keyed by app_id.
            data = {
                "count": len(item_list),
                "generated_at": None,
                "applications": [r.model_dump(mode="json") for r in item_list],
            }
            if item_list:
                data["generated_at"] = item_list[0].researched_at.isoformat()

            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            self._atomic_write_text(target_path, json_str)
            logger.info("Saved %d application results to %s", len(item_list), target_path)

            # Also ensure individual files are saved
            for r in item_list:
                self.save_app_result(r)

            return target_path
        except Exception as e:
            raise StorageError(f"Failed to save aggregated results to {target_path}: {e}") from e

    def load_all_results(
        self, filepath: Optional[Path] = None
    ) -> Dict[str, AppResearchResult]:
        """Load aggregated results from a file.

        Args:
            filepath: Optional path to read from (defaults to initial_research_file).

        Returns:
            Dictionary mapping app_id -> AppResearchResult.
        """
        target_path = Path(filepath) if filepath else self.initial_research_file
        if not target_path.exists():
            return {}

        try:
            content = target_path.read_text(encoding="utf-8")
            raw_data = json.loads(content)

            apps_data = []
            if isinstance(raw_data, list):
                apps_data = raw_data
            elif isinstance(raw_data, dict) and "applications" in raw_data:
                apps_data = raw_data["applications"]
            elif isinstance(raw_data, dict):
                apps_data = list(raw_data.values())

            results: Dict[str, AppResearchResult] = {}
            for item in apps_data:
                res = AppResearchResult.model_validate(item)
                results[res.app_id] = res
            return results
        except Exception as e:
            raise StorageError(f"Failed to load aggregated results from {target_path}: {e}") from e
