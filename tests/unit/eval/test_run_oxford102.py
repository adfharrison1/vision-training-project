from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest
from eval.run_oxford102 import parse_duration_budget, run_eval

from plant_id.domain.models import ObservationResult, Prediction


def _mock_settings() -> object:
    return type(
        "Settings",
        (),
        {
            "vision_model": "qwen3-vl:2b",
            "species_catalog_path": Path("resources/species_catalog/default.txt"),
        },
    )()


def _sample_args(**overrides) -> Namespace:
    defaults = {
        "profile": "smoke",
        "eval_run_id": "unit-test",
        "backend": "vlm",
        "split": "test",
        "limit": None,
        "max_duration": None,
        "quiet": True,
        "dataset_root": None,
        "output": None,
        "plantnet_baseline": False,
    }
    defaults.update(overrides)
    return Namespace(**defaults)


def test_parse_duration_budget_minutes() -> None:
    assert parse_duration_budget("30m") == 30 * 60 * 1000


def test_parse_duration_budget_compound() -> None:
    assert parse_duration_budget("1h30m") == 90 * 60 * 1000


def test_parse_duration_budget_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid duration"):
        parse_duration_budget("not-a-duration")


def test_run_eval_writes_report_when_plantnet_disabled(tmp_path: Path) -> None:
    output_path = tmp_path / "report.json"
    fake_result = ObservationResult(
        observation_id="eval-unit-test-image_00001",
        predictions=(
            Prediction(
                rank=1,
                species_label="tiger lily",
                evidence="test",
                confidence=0.9,
            ),
        ),
        model_tag="qwen3-vl:2b",
        prompt_version="closed-set-v1",
    )

    with (
        patch(
            "eval.run_oxford102.list_eval_images",
            return_value=[
                type(
                    "EvalImage",
                    (),
                    {
                        "image_path": Path("data/flowers/jpg/image_00001.jpg"),
                        "ground_truth": "tiger lily",
                    },
                )()
            ],
        ),
        patch(
            "eval.run_oxford102.execute_identify",
            return_value=type(
                "Outcome",
                (),
                {"exit_code": 0, "error_message": None, "result": fake_result},
            )(),
        ),
        patch("eval.run_oxford102.load_settings", return_value=_mock_settings()),
        patch(
            "eval.run_oxford102.FileSpeciesCatalog",
            return_value=type("Catalog", (), {"list_class_names": lambda self: ["tiger lily"]})(),
        ),
    ):
        exit_code = run_eval(_sample_args(output=output_path, plantnet_baseline=False))

    assert exit_code == 0
    assert output_path.is_file()


def test_run_eval_local_metrics_survive_plantnet_failure(tmp_path: Path) -> None:
    output_path = tmp_path / "report-with-plantnet.json"
    fake_result = ObservationResult(
        observation_id="eval-unit-test-image_00001",
        predictions=(
            Prediction(
                rank=1,
                species_label="tiger lily",
                evidence="test",
                confidence=0.9,
            ),
        ),
        model_tag="qwen3-vl:2b",
        prompt_version="closed-set-v1",
    )
    plantnet_failure = type(
        "PlantNetResult",
        (),
        {"labels": (), "raw_best_match": None, "error": "HTTP 500"},
    )()

    with (
        patch(
            "eval.run_oxford102.list_eval_images",
            return_value=[
                type(
                    "EvalImage",
                    (),
                    {
                        "image_path": Path("data/flowers/jpg/image_00001.jpg"),
                        "ground_truth": "tiger lily",
                    },
                )()
            ],
        ),
        patch(
            "eval.run_oxford102.execute_identify",
            return_value=type(
                "Outcome",
                (),
                {"exit_code": 0, "error_message": None, "result": fake_result},
            )(),
        ),
        patch("eval.run_oxford102.load_settings", return_value=_mock_settings()),
        patch(
            "eval.run_oxford102.FileSpeciesCatalog",
            return_value=type("Catalog", (), {"list_class_names": lambda self: ["tiger lily"]})(),
        ),
        patch("eval.run_oxford102.plantnet_api_key", return_value="test-key"),
        patch("eval.run_oxford102.identify_image", return_value=plantnet_failure),
    ):
        exit_code = run_eval(_sample_args(output=output_path, plantnet_baseline=True))

    assert exit_code == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"top1_accuracy": 1.0' in payload
    assert '"plantnet"' in payload
