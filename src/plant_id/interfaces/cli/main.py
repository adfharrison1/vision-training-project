"""CLI entrypoint for plant-id."""

from __future__ import annotations

import argparse
import sys

from plant_id.interfaces.cli.commands.verify_env import run_verify_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plant-id",
        description="Local UK plant identification (Oxford 102 Flowers).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "verify-env",
        help="Verify Ollama is running and the configured vision model is installed.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify-env":
        return run_verify_env()

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
