import subprocess
from pathlib import Path

import pytest

from osm_to_svg.extractor import extract_from_pbf


def test_extract_from_pbf_rejects_missing_source_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Source PBF file not found"):
        extract_from_pbf(
            str(tmp_path / "missing.osm.pbf"),
            (8.0, 52.0, 8.2, 52.2),
            str(tmp_path / "out.osm.pbf"),
        )


def test_extract_from_pbf_invokes_osmium_with_expected_args(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.osm.pbf"
    source.write_bytes(b"dummy")

    called: dict[str, object] = {}

    def fake_run(cmd, check, capture_output, text):  # noqa: ANN001, ANN202
        called["cmd"] = cmd
        called["check"] = check
        called["capture_output"] = capture_output
        called["text"] = text
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    extract_from_pbf(
        str(source),
        (8.0, 52.0, 8.2, 52.2),
        str(tmp_path / "clip.osm.pbf"),
    )

    cmd = called["cmd"]
    assert cmd[0:3] == ["osmium", "extract", "-b"]
    assert cmd[3] == "8.0,52.0,8.2,52.2"
    assert called["check"] is True


def test_extract_from_pbf_wraps_called_process_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.osm.pbf"
    source.write_bytes(b"dummy")

    def fake_run(cmd, check, capture_output, text):  # noqa: ANN001, ANN202
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd, stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="osmium extraction failed"):
        extract_from_pbf(
            str(source),
            (8.0, 52.0, 8.2, 52.2),
            str(tmp_path / "clip.osm.pbf"),
        )


def test_extract_from_pbf_wraps_missing_osmium_binary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.osm.pbf"
    source.write_bytes(b"dummy")

    def fake_run(cmd, check, capture_output, text):  # noqa: ANN001, ANN202
        raise FileNotFoundError("osmium not found")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="osmium-tool not found"):
        extract_from_pbf(
            str(source),
            (8.0, 52.0, 8.2, 52.2),
            str(tmp_path / "clip.osm.pbf"),
        )
