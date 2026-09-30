"""Unit tests for sheet synthesis CLI."""

from __future__ import annotations

from pathlib import Path

from eval import synthesize_species_sheet as synth


def test_synthesize_dry_run_requires_existing_images(tmp_path: Path) -> None:
    img = tmp_path / "a.jpg"
    img.write_bytes(b"fake")
    code = synth.main(
        [
            "--species",
            "bolero deep blue",
            "--images",
            str(img),
            str(img),
            "--out",
            str(tmp_path / "out.yaml"),
            "--dry-run",
        ]
    )
    assert code == 0


def test_synthesize_calls_client(monkeypatch, tmp_path: Path) -> None:
    img1 = tmp_path / "a.jpg"
    img2 = tmp_path / "b.jpg"
    img1.write_bytes(b"a")
    img2.write_bytes(b"b")

    class FakeCompletions:
        def create(self, **_kwargs):
            class Message:
                content = (
                    '{"retrieval_text": "Compact campanula with violet bells.", '
                    '"context_block": "Versus other campanula."}'
                )

            class Choice:
                message = Message()

            class Response:
                choices = [Choice()]

            return Response()

    class FakeClient:
        chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setenv("PLANT_ID_VLM_CLOUD_API_KEY", "test-key")
    settings = synth.Settings()
    out = tmp_path / "sheet.yaml"
    payload = synth.synthesise_sheet(
        settings,
        species="bolero deep blue",
        image_paths=[img1, img2],
        neighbors=["canterbury bells"],
        client=FakeClient(),
    )
    assert payload["catalog_label"] == "bolero deep blue"
    out.write_text("ok")
    assert "retrieval_text" in payload
