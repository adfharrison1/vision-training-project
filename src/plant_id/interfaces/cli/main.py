"""CLI entrypoint for plant-id."""

from __future__ import annotations

import argparse
import sys

from plant_id.infrastructure.composition.container import Backend
from plant_id.interfaces.cli.commands.demo import run_demo
from plant_id.interfaces.cli.commands.identify import run_identify
from plant_id.interfaces.cli.commands.verify_env import run_verify_env


def _add_backend_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--backend",
        choices=("vlm", "classical"),
        default="vlm",
        help="Identification backend (default: vlm).",
    )


def _add_quiet_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stage progress messages on stderr.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plant-id",
        description="Local UK plant identification from photographs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "verify-env",
        help="Verify Ollama is running and the configured vision model is installed.",
    )

    identify_parser = subparsers.add_parser(
        "identify",
        help="Identify a plant from 1–3 photograph paths.",
    )
    _add_backend_argument(identify_parser)
    identify_parser.add_argument(
        "--photos",
        required=True,
        help="Comma-separated paths to 1–3 photographs of the same plant.",
    )
    identify_parser.add_argument(
        "--observation-id",
        help="Optional observation identifier (defaults to a random UUID).",
    )
    _add_quiet_argument(identify_parser)

    demo_parser = subparsers.add_parser(
        "demo",
        help="Identify the default demo sample image (requires data/flowers/).",
    )
    _add_backend_argument(demo_parser)
    _add_quiet_argument(demo_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify-env":
        return run_verify_env()

    backend: Backend = args.backend

    if args.command == "identify":
        return run_identify(
            backend=backend,
            photos=args.photos,
            observation_id=args.observation_id,
            quiet=args.quiet,
        )

    if args.command == "demo":
        return run_demo(backend=backend, quiet=args.quiet)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
