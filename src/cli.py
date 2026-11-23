"""Command-line interface for the Integration Intelligence research system."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from src.agents.orchestrator import ResearchOrchestrator
from src.logging_utils import get_logger, setup_logging

logger = get_logger("cli")


def build_parser() -> argparse.ArgumentParser:
    """Construct command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="integration-intel",
        description="Integration Intelligence: AI-powered SaaS integration research platform.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: list-apps
    subparsers.add_parser("list-apps", help="List all applications in the dataset.")

    # Command: status
    subparsers.add_parser("status", help="Show research completion metrics and status.")

    # Command: research
    research_parser = subparsers.add_parser("research", help="Execute research on SaaS applications.")
    research_group = research_parser.add_mutually_exclusive_group(required=True)
    research_group.add_argument("--app", type=str, help="Research a single application by ID.")
    research_group.add_argument(
        "--batch",
        type=str,
        choices=["pilot"],
        help="Research a predefined batch (e.g., 'pilot').",
    )
    research_group.add_argument(
        "--category",
        type=str,
        help="Research all applications in a specific category.",
    )
    research_group.add_argument(
        "--all",
        action="store_true",
        help="Research all 100 applications in dataset.",
    )
    research_parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass cached checkpoints and re-run research.",
    )
    research_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom destination filepath for aggregated results.",
    )
    research_parser.add_argument(
        "--mode",
        type=str,
        default="production",
        choices=["production", "test"],
        help="Execution mode (production enforces live retrieval, test allows fixtures).",
    )

    return parser


def handle_list_apps(orchestrator: ResearchOrchestrator) -> int:
    """Print all applications formatted by category."""
    apps = orchestrator.list_apps()
    print(f"\nTotal Applications: {len(apps)}\n")
    print(f"{'ID':<25} {'Name':<25} {'Category':<35}")
    print("-" * 85)
    for app in sorted(apps, key=lambda a: (a.category, a.name)):
        print(f"{app.app_id:<25} {app.name:<25} {app.category:<35}")
    return 0


def handle_status(orchestrator: ResearchOrchestrator) -> int:
    """Display research progress and category breakdown."""
    status = orchestrator.get_status()
    print("\n" + "=" * 60)
    print(" INTEGRATION INTELLIGENCE - RESEARCH STATUS")
    print("=" * 60)
    print(f"Total Applications:   {status['total_applications']}")
    print(f"Completed Research:   {status['completed_count']}")
    print(f"Remaining Apps:       {status['remaining_count']}")
    print(f"Pilot Batch Status:   {'DONE (5/5)' if status['pilot_completed'] else f'Incomplete ({status['pilot_completed_count']}/5)'}")
    print("\nCategory Breakdown:")
    print(f"{'Category':<40} {'Done':<8} {'Total':<8} {'% Complete':<10}")
    print("-" * 66)
    categories = status["categories"]  # type: ignore
    for cat_name, counts in sorted(categories.items()):
        total = counts["total"]
        done = counts["completed"]
        pct = (done / total * 100) if total > 0 else 0
        print(f"{cat_name:<40} {done:<8} {total:<8} {pct:>8.1f}%")
    print("=" * 60 + "\n")
    return 0


def handle_research(args: argparse.Namespace, orchestrator: ResearchOrchestrator) -> int:
    """Route research commands to orchestrator."""
    if args.app:
        print(f"\nInvestigating application: {args.app} ...")
        res = orchestrator.research_app(args.app, force=args.force)
        print("\nResearch Complete:")
        print(f"  App Name:         {res.name} ({res.app_id})")
        print(f"  Feasibility:      {res.feasibility.feasibility_score:.1f}/10.0 ({res.feasibility.buildability.value})")
        print(f"  Primary Auth:     {res.auth.primary_method.value}")
        print(f"  Credential Access:{res.auth.credential_accessibility.value}")
        print(f"  API Breadth:      {res.api_surface.breadth.value}")
        print(f"  MCP Availability: {res.mcp.availability.value}")
        print(f"  Confidence:       {res.confidence.value}")
        print(f"  Evidence Items:   {len(res.evidence)}")
        if res.feasibility.primary_blockers:
            print("  Blockers:")
            for b in res.feasibility.primary_blockers:
                print(f"    - [{b.severity.value}] {b.title}: {b.description}")
        return 0

    if args.batch == "pilot":
        print("\nInitiating Pilot Research on 5 applications: salesforce, github, shopify, sherlock, notebooklm ...")
        results = orchestrator.research_pilot(force=args.force, output_filepath=args.output)
        print(f"\nPilot batch successfully completed. {len(results)} applications evaluated.")
        for app_id, r in results.items():
            print(f"  - {r.name:<15} Score: {r.feasibility.feasibility_score:.1f}/10  [{r.feasibility.buildability.value}]")
        return 0

    if args.category:
        print(f"\nResearching category: {args.category} ...")
        results = orchestrator.research_category(args.category, force=args.force)
        print(f"\nCategory research complete. {len(results)} applications evaluated.")
        return 0

    if args.all:
        print("\nInitiating FULL research run for all 100 applications ...")
        results = orchestrator.research_all(force=args.force, output_filepath=args.output)
        print(f"\nFull dataset research complete. {len(results)} applications evaluated.")
        return 0

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entrypoint."""
    setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    mode = getattr(args, "mode", "production")
    orchestrator = ResearchOrchestrator(mode=mode)

    try:
        if args.command == "list-apps":
            return handle_list_apps(orchestrator)
        elif args.command == "status":
            return handle_status(orchestrator)
        elif args.command == "research":
            return handle_research(args, orchestrator)
        else:
            parser.print_help()
            return 1
    except Exception as e:
        logger.error("CLI error: %s", e)
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
