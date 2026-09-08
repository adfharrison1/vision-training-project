from plant_id.infrastructure.config.settings import Settings
from plant_id.interfaces.cli.progress import identification_progress


def test_identification_progress_plain_mode_writes_stages(capsys) -> None:
    settings = Settings()

    with identification_progress("vlm", 1, settings, quiet=False):
        pass

    stderr = capsys.readouterr().err
    assert "Identifying with vlm backend" in stderr
    assert "Identification complete" in stderr


def test_identification_progress_quiet_is_silent(capsys) -> None:
    settings = Settings()

    with identification_progress("vlm", 1, settings, quiet=True):
        pass

    assert capsys.readouterr().err == ""
