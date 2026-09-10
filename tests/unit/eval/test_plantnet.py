from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
from eval.baselines.plantnet import identify_image


def test_identify_image_without_api_key() -> None:
    result = identify_image(Path("image.jpg"), class_names=["tiger lily"], api_key=None)
    assert result.error == "PLANTNET_API_KEY is not configured."


def test_identify_image_maps_catalog_labels(tmp_path: Path) -> None:
    image_path = tmp_path / "image_00001.jpg"
    image_path.write_bytes(b"fake-image")

    response_payload = {
        "bestMatch": "Ajuga genevensis L.",
        "results": [
            {
                "score": 0.9,
                "species": {
                    "scientificNameWithoutAuthor": "Ajuga genevensis",
                    "commonNames": ["tiger lily", "Blue bugle"],
                },
            }
        ],
    }
    response = httpx.Response(200, json=response_payload)
    client = MagicMock(spec=httpx.Client)
    client.post.return_value = response

    result = identify_image(
        image_path,
        class_names=["tiger lily", "english marigold"],
        api_key="test-key",
        client=client,
    )

    assert result.error is None
    assert result.labels[0] == "tiger lily"


def test_identify_image_retries_transient_errors(tmp_path: Path) -> None:
    image_path = tmp_path / "image_00001.jpg"
    image_path.write_bytes(b"fake-image")

    client = MagicMock(spec=httpx.Client)
    client.post.side_effect = [
        httpx.Response(429, json={"error": "rate limit"}),
        httpx.Response(
            200,
            json={
                "bestMatch": "x",
                "results": [{"species": {"commonNames": ["sweet pea"]}}],
            },
        ),
    ]

    with patch("eval.baselines.plantnet.time.sleep"):
        result = identify_image(
            image_path,
            class_names=["sweet pea"],
            api_key="test-key",
            client=client,
            max_retries=2,
        )

    assert result.error is None
    assert result.labels == ("sweet pea",)
    assert client.post.call_count == 2
