"""Research orchestrator for managing single, batch, pilot, and full dataset research."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Set
import time

from src.agents.researcher import AppResearcher
from src.config import get_settings
from src.exceptions import DatasetError, ResearchError
from src.logging_utils import get_logger
from src.models.app_metadata import AppMetadata
from src.models.research import AppResearchResult
from src.storage.json_store import JSONStore

logger = get_logger("agents.orchestrator")


class ResearchOrchestrator:
    """Coordinates multi-app research, rate-limiting, checkpointing, and persistence."""

    PILOT_APP_IDS = ["salesforce", "github", "shopify", "sherlock", "notebooklm"]

    def __init__(
        self,
        researcher: Optional[AppResearcher] = None,
        store: Optional[JSONStore] = None,
        dataset_path: Optional[Path] = None,
        mode: str = "production",
    ) -> None:
        settings = get_settings()
        self.mode = mode
        self.researcher = researcher or AppResearcher(mode=mode)
        self.store = store or JSONStore()
        self.dataset_path = Path(dataset_path) if dataset_path else settings.dataset_path
        self.stage3a_results_file = self.store.base_dir / "stage3a_verified_research.json"
        self._apps_map: Dict[str, AppMetadata] = {}
        self._load_dataset()

    def _load_dataset(self) -> None:
        """Load and index all applications from canonical dataset."""
        if not self.dataset_path.exists():
            raise DatasetError(f"Dataset file not found at {self.dataset_path}")

        try:
            content = self.dataset_path.read_text(encoding="utf-8")
            raw_apps = json.loads(content)
            for item in raw_apps:
                app = AppMetadata.model_validate(item)
                self._apps_map[app.app_id] = app
            logger.info("Loaded %d applications into research orchestrator.", len(self._apps_map))
        except Exception as e:
            raise DatasetError(f"Failed to load dataset: {e}") from e

    def get_app(self, app_id: str) -> AppMetadata:
        """Retrieve AppMetadata by app_id."""
        if app_id not in self._apps_map:
            raise DatasetError(f"Application ID '{app_id}' not found in canonical dataset.")
        return self._apps_map[app_id]

    def list_apps(self) -> List[AppMetadata]:
        """Return list of all applications in canonical dataset."""
        return list(self._apps_map.values())

    def research_app(self, app_id: str, force: bool = False) -> AppResearchResult:
        """Research a single application with checkpoint caching.

        Args:
            app_id: Target application ID.
            force: If True, bypass existing checkpoint and re-research.

        Returns:
            AppResearchResult.
        """
        app = self.get_app(app_id)

        if not force and self.store.has_checkpoint(app_id):
            logger.info("Loading existing checkpoint for %s", app_id)
            cached = self.store.load_app_result(app_id)
            if cached:
                return cached

        try:
            result = self.researcher.research(app)
            self.store.save_app_result(result)
            return result
        except Exception as e:
            logger.error("Research failed for %s: %s", app_id, e)
            raise ResearchError(f"Research failed for {app_id}: {e}") from e

    def research_batch(
        self,
        app_ids: List[str],
        force: bool = False,
        delay_seconds: float = 0.05,
        max_workers: int = 5,
    ) -> Dict[str, AppResearchResult]:
        """Execute research for a list of application IDs.

        Args:
            app_ids: List of application IDs.
            force: If True, re-research even if cached.
            delay_seconds: Throttling pause between requests (sequential mode).
            max_workers: Number of concurrent worker threads.

        Returns:
            Dictionary mapping app_id -> AppResearchResult.
        """
        results: Dict[str, AppResearchResult] = {}
        total = len(app_ids)

        if max_workers > 1 and total > 1:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            logger.info("Executing concurrent research for %d applications with %d workers.", total, max_workers)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_id = {executor.submit(self.research_app, app_id, force): app_id for app_id in app_ids}
                completed = 0
                for future in as_completed(future_to_id):
                    app_id = future_to_id[future]
                    completed += 1
                    try:
                        res = future.result()
                        results[app_id] = res
                        logger.info("[%d/%d] Completed research for %s (Score: %.1f)", completed, total, app_id, res.feasibility.feasibility_score)
                    except Exception as e:
                        logger.error("Failed researching %s: %s", app_id, e)
                        raise
            return results

        for idx, app_id in enumerate(app_ids, 1):
            logger.info("[%d/%d] Orchestrating research for %s", idx, total, app_id)
            res = self.research_app(app_id, force=force)
            results[app_id] = res
            if idx < total and delay_seconds > 0:
                time.sleep(delay_seconds)

        return results

    def research_pilot(
        self,
        force: bool = False,
        output_filepath: Optional[Path] = None,
    ) -> Dict[str, AppResearchResult]:
        """Execute pilot research on the 5 designated pilot applications and save to verified destination.

        Pilot Apps:
        - salesforce
        - github
        - shopify
        - sherlock
        - notebooklm
        """
        dest_path = Path(output_filepath) if output_filepath else self.stage3a_results_file
        logger.info(
            "Executing pilot research on 5 benchmark applications: %s (saving to %s)",
            self.PILOT_APP_IDS,
            dest_path,
        )
        results = self.research_batch(self.PILOT_APP_IDS, force=force)
        self.store.save_all_results(results, filepath=dest_path)
        return results

    def research_category(self, category_name: str, force: bool = False) -> Dict[str, AppResearchResult]:
        """Research all applications within a specific category."""
        target_ids = [
            app.app_id
            for app in self._apps_map.values()
            if app.category.lower() == category_name.lower()
        ]
        if not target_ids:
            raise DatasetError(f"No applications found for category '{category_name}'.")

        logger.info("Researching category '%s' (%d apps)", category_name, len(target_ids))
        results = self.research_batch(target_ids, force=force)
        return results

    def research_all(
        self,
        force: bool = False,
        output_filepath: Optional[Path] = None,
        delay_seconds: float = 0.02,
    ) -> Dict[str, AppResearchResult]:
        """Research all 100 applications in the canonical dataset."""
        all_ids = list(self._apps_map.keys())
        target_path = Path(output_filepath) if output_filepath else (self.store.base_dir / "final_research_100.json")
        logger.info("Initiating full research run for %d applications (saving to %s).", len(all_ids), target_path)
        results = self.research_batch(all_ids, force=force, delay_seconds=delay_seconds, max_workers=5)
        self.store.save_all_results(results, filepath=target_path)
        # Also persist to standard verified_research_file
        if target_path != self.store.verified_research_file:
            self.store.save_all_results(results, filepath=self.store.verified_research_file)
        return results

    def get_status(self) -> Dict[str, object]:
        """Return status metrics on current research progress."""
        completed_ids = self.store.get_completed_app_ids()
        total_apps = len(self._apps_map)

        category_counts: Dict[str, Dict[str, int]] = {}
        for app in self._apps_map.values():
            cat = app.category
            if cat not in category_counts:
                category_counts[cat] = {"total": 0, "completed": 0}
            category_counts[cat]["total"] += 1
            if app.app_id in completed_ids:
                category_counts[cat]["completed"] += 1

        pilot_completed = all(pid in completed_ids for pid in self.PILOT_APP_IDS)

        return {
            "total_applications": total_apps,
            "completed_count": len(completed_ids),
            "remaining_count": total_apps - len(completed_ids),
            "pilot_completed": pilot_completed,
            "pilot_completed_count": sum(1 for pid in self.PILOT_APP_IDS if pid in completed_ids),
            "categories": category_counts,
        }
