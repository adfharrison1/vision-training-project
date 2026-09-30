"""Probe Fireworks /embeddings — exploratory; not runtime unless OpenRouter fails eval."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

import httpx

from plant_id.infrastructure.config.settings import Settings


def _auth_headers(settings: Settings) -> dict[str, str]:
    key = settings.vlm_cloud_api_key
    if not key:
        raise SystemExit("Set PLANT_ID_VLM_CLOUD_API_KEY (or FIREWORKS mapped in .env).")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _post_embeddings(settings: Settings, payload: dict) -> tuple[int, dict | str]:
    url = f"{settings.vlm_cloud_base_url.rstrip('/')}/embeddings"
    with httpx.Client(timeout=120.0) as client:
        response = client.post(url, headers=_auth_headers(settings), json=payload)
    try:
        body: dict | str = response.json()
    except json.JSONDecodeError:
        body = response.text
    return response.status_code, body


def probe_qwen3_text(settings: Settings, text: str) -> None:
    payload = {
        "model": "fireworks/qwen3-embedding-8b",
        "input": text,
        "dimensions": 256,
    }
    status, body = _post_embeddings(settings, payload)
    print("=== fireworks/qwen3-embedding-8b (serverless text) ===")
    print(f"HTTP {status}")
    if isinstance(body, dict) and body.get("data"):
        dim = len(body["data"][0].get("embedding", []))
        usage = body.get("usage", {})
        print(f"vector_dim={dim} usage={usage}")
    else:
        print(json.dumps(body, indent=2)[:2000])


def probe_voyage_text(settings: Settings, text: str, *, model: str) -> None:
    payload = {
        "model": model,
        "input": text,
        "input_type": "document",
        "dimensions": 512,
    }
    status, body = _post_embeddings(settings, payload)
    print(f"=== {model} (text, input_type=document) ===")
    print(f"HTTP {status}")
    if isinstance(body, dict) and body.get("data"):
        dim = len(body["data"][0].get("embedding", []))
        print(f"vector_dim={dim}")
    else:
        print(json.dumps(body, indent=2)[:2000])


def _image_data_uri(path: Path) -> str:
    encoded = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def probe_multimodal_attempts(settings: Settings, image_path: Path, text: str) -> None:
    """Try likely Fireworks/Voyage multimodal payload shapes on /embeddings."""
    data_uri = _image_data_uri(image_path)
    models = [
        "fireworks/voyage-multimodal-3-5",
        "accounts/fireworks/models/voyage-multimodal-3-5",
    ]
    payloads = [
        {
            "label": "openai-style string input (sanity)",
            "payload": {
                "model": models[0],
                "input": text,
                "input_type": "document",
            },
        },
        {
            "label": "voyage-style inputs[] with image_base64",
            "payload": {
                "model": models[0],
                "inputs": [
                    {
                        "content": [
                            {"type": "text", "text": text},
                            {"type": "image_base64", "image_base64": data_uri},
                        ]
                    }
                ],
                "input_type": "document",
            },
        },
    ]
    for model in models:
        for attempt in payloads:
            payload = dict(attempt["payload"])
            payload["model"] = model
            status, body = _post_embeddings(settings, payload)
            print(f"=== multimodal try: model={model} | {attempt['label']} ===")
            print(f"HTTP {status}")
            if isinstance(body, dict) and body.get("data"):
                row = body["data"][0]
                emb = row.get("embedding")
                if isinstance(emb, list):
                    print(f"vector_dim={len(emb)}")
                else:
                    print(f"embedding type={type(emb).__name__}")
            else:
                snippet = json.dumps(body, indent=2) if isinstance(body, dict) else str(body)
                print(snippet[:1500])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe Fireworks embedding endpoints.")
    parser.add_argument(
        "--image",
        type=Path,
        default=None,
        help="Optional Oxford jpg for multimodal probes",
    )
    args = parser.parse_args(argv)
    settings = Settings()
    sample_text = (
        "Compact campanula with deep violet-blue bell-shaped flowers on stiff stems."
    )
    probe_qwen3_text(settings, sample_text)
    print()
    probe_voyage_text(settings, sample_text, model="fireworks/voyage-4-lite")
    print()
    image = args.image
    if image is None:
        candidate = Path("data/flowers/jpg/image_00001.jpg")
        if candidate.is_file():
            image = candidate
    if image and image.is_file():
        probe_multimodal_attempts(settings, image, sample_text)
    else:
        print("=== multimodal probes skipped (no --image and no data/flowers sample) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
