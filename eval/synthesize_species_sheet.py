"""Synthesise species sheet YAML from multiple reference photos via cloud VLM."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from openai import OpenAI

from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.vlm_cloud import _image_data_uri
from plant_id.infrastructure.species_sheets.loader import validate_retrieval_text

SHEET_SYNTH_PROMPT = """You are drafting a species knowledge sheet for plant retrieval.

Given photographs of ONE flowering plant species, output ONLY valid JSON:
{{
  "retrieval_text": "<multi-sentence morphology and habit; species-centric>",
  "context_block": "<short disambiguation vs similar catalog species>"
}}

Rules:
- Describe typical plant morphology and visible traits, NOT a specific photograph.
- Do NOT mention photos, frames, datasets, Oxford, or image file names.
- Do NOT name the species in retrieval_text if the cultivar name would leak the answer;
  focus on traits. context_block MAY name confusers from this hint list when useful:
  {neighbor_hint}
- retrieval_text and context_block must be plain English prose strings.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synthesise a species sheet YAML draft.")
    parser.add_argument("--species", required=True, help="catalog_label (exact catalog string)")
    parser.add_argument(
        "--images",
        nargs="+",
        required=True,
        help="Two or more image paths for the same species",
    )
    parser.add_argument("--out", type=Path, required=True, help="Output YAML path")
    parser.add_argument(
        "--neighbors",
        nargs="*",
        default=[],
        help="Optional catalog labels to mention in context_block disambiguation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompt parts and exit without calling the cloud VLM",
    )
    return parser


def _validate_configuration(settings: Settings) -> None:
    if not settings.vlm_cloud_api_key:
        raise SystemExit("Set PLANT_ID_VLM_CLOUD_API_KEY for synthesis (or use --dry-run).")
    if not settings.vlm_cloud_base_url.strip():
        raise SystemExit("Set PLANT_ID_VLM_CLOUD_BASE_URL.")
    if not settings.vlm_cloud_model.strip():
        raise SystemExit("Set PLANT_ID_VLM_CLOUD_MODEL.")


def _build_messages(
    settings: Settings,
    *,
    species: str,
    image_paths: list[Path],
    neighbors: list[str],
) -> list[dict]:
    neighbor_hint = ", ".join(neighbors) if neighbors else "(none provided)"
    prompt = SHEET_SYNTH_PROMPT.format(neighbor_hint=neighbor_hint)
    intro = f"Target catalog_label (for your reference only): {species}\n\n{prompt}"
    content: list[dict] = [{"type": "text", "text": intro}]
    for path in image_paths:
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {path}")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": _image_data_uri(str(path.resolve()))},
            }
        )
    return [{"role": "user", "content": content}]


def _parse_sheet_json(text: str) -> dict[str, str]:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Model output must be a JSON object.")
    retrieval_text = payload.get("retrieval_text")
    context_block = payload.get("context_block")
    if not isinstance(retrieval_text, str) or not retrieval_text.strip():
        raise ValueError("Missing retrieval_text string in model JSON.")
    if not isinstance(context_block, str) or not context_block.strip():
        raise ValueError("Missing context_block string in model JSON.")
    return {"retrieval_text": retrieval_text.strip(), "context_block": context_block.strip()}


def synthesise_sheet(
    settings: Settings,
    *,
    species: str,
    image_paths: list[Path],
    neighbors: list[str],
    client: OpenAI | None = None,
) -> dict[str, object]:
    messages = _build_messages(
        settings,
        species=species,
        image_paths=image_paths,
        neighbors=neighbors,
    )
    openai_client = client or OpenAI(
        base_url=settings.vlm_cloud_base_url,
        api_key=settings.vlm_cloud_api_key,
        timeout=settings.vlm_cloud_timeout_seconds,
    )
    response = openai_client.chat.completions.create(
        model=settings.vlm_cloud_model,
        messages=messages,
        temperature=0,
    )
    choice = response.choices[0].message
    content = choice.content or ""
    if not content.strip():
        raise RuntimeError("Cloud VLM returned empty content for sheet synthesis.")
    fields = _parse_sheet_json(content)
    issues = validate_retrieval_text(fields["retrieval_text"])
    if issues:
        raise RuntimeError("Synthesised retrieval_text failed validation: " + "; ".join(issues))
    return {
        "catalog_label": species,
        **fields,
        "provenance": {
            "authored_by": "vlm-synth",
            "source_images": [str(path.resolve()) for path in image_paths],
            "prompt_version": "sheet-synth-v1",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    image_paths = [Path(path) for path in args.images]
    if len(image_paths) < 2 and not args.dry_run:
        print("Provide at least two --images unless using --dry-run.", file=sys.stderr)
        return 1

    settings = Settings()
    if args.dry_run:
        for path in image_paths:
            if not path.is_file():
                print(f"Image not found (dry-run): {path}", file=sys.stderr)
                return 1
        print("Dry-run OK: image paths exist; synthesis would call cloud VLM.")
        return 0

    _validate_configuration(settings)
    payload = synthesise_sheet(
        settings,
        species=args.species,
        image_paths=image_paths,
        neighbors=list(args.neighbors),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    yaml_text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    args.out.write_text(yaml_text, encoding="utf-8")
    print(f"Wrote draft sheet to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
