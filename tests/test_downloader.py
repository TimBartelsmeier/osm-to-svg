from pathlib import Path

import httpx
import pytest

from osm_to_svg.downloader import download_from_overpass, download_from_url


class DummyStreamResponse:
    def __init__(
        self,
        *,
        chunks: list[bytes],
        headers: dict[str, str] | None = None,
        raise_error: Exception | None = None,
    ):
        self._chunks = chunks
        self.headers = headers or {}
        self._raise_error = raise_error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001, ANN201
        return False

    def raise_for_status(self) -> None:
        if self._raise_error:
            raise self._raise_error

    def iter_bytes(self, chunk_size: int = 8192):  # noqa: ARG002
        for chunk in self._chunks:
            yield chunk

    def read(self) -> bytes:
        return b"".join(self._chunks)


def test_download_from_url_writes_streamed_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "region.osm.pbf"

    def fake_stream(method, url, timeout, follow_redirects):  # noqa: ANN001, ANN202
        assert method == "GET"
        assert follow_redirects is True
        return DummyStreamResponse(
            chunks=[b"abc", b"def"],
            headers={"content-length": "6"},
        )

    monkeypatch.setattr(httpx, "stream", fake_stream)

    download_from_url("https://example.org/region.osm.pbf", str(output))

    assert output.exists()
    assert output.read_bytes() == b"abcdef"


def test_download_from_overpass_writes_streamed_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "bbox.osm.pbf"

    def fake_stream(method, url, timeout, follow_redirects):  # noqa: ANN001, ANN202
        assert "overpass-api.de" in url
        return DummyStreamResponse(
            chunks=[b"\x00\x11\x22", b"\x33\x44"],
            headers={"content-type": "application/octet-stream", "content-length": "5"},
        )

    monkeypatch.setattr(httpx, "stream", fake_stream)

    download_from_overpass((8.0, 52.0, 8.1, 52.1), str(output))

    assert output.exists()
    assert output.read_bytes() == b"\x00\x11\x22\x33\x44"


def test_download_from_overpass_rejects_html_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "bbox.osm.pbf"

    def fake_stream(method, url, timeout, follow_redirects):  # noqa: ANN001, ANN202
        return DummyStreamResponse(
            chunks=[b"<html>error</html>"],
            headers={"content-type": "text/html", "content-length": "18"},
        )

    monkeypatch.setattr(httpx, "stream", fake_stream)

    with pytest.raises(ValueError, match="returned HTML"):
        download_from_overpass((8.0, 52.0, 8.1, 52.1), str(output))

    assert not output.exists()


def test_download_from_overpass_wraps_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "bbox.osm.pbf"

    def fake_stream(method, url, timeout, follow_redirects):  # noqa: ANN001, ANN202
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx, "stream", fake_stream)

    with pytest.raises(httpx.HTTPError, match="timed out"):
        download_from_overpass((8.0, 52.0, 8.1, 52.1), str(output), timeout=1)


def test_download_from_overpass_rejects_html_in_first_chunk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "bbox.osm.pbf"

    def fake_stream(method, url, timeout, follow_redirects):  # noqa: ANN001, ANN202
        return DummyStreamResponse(
            chunks=[b"<?xml version='1.0'?>oops"],
            headers={"content-length": "24"},
        )

    monkeypatch.setattr(httpx, "stream", fake_stream)

    with pytest.raises(ValueError, match="appears to be HTML/XML"):
        download_from_overpass((8.0, 52.0, 8.1, 52.1), str(output))

    assert not output.exists()


def test_download_from_overpass_wraps_http_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "bbox.osm.pbf"

    def fake_stream(method, url, timeout, follow_redirects):  # noqa: ANN001, ANN202
        return DummyStreamResponse(
            chunks=[],
            headers={"content-length": "0"},
            raise_error=httpx.HTTPStatusError(
                "bad status",
                request=httpx.Request("GET", url),
                response=httpx.Response(500),
            ),
        )

    monkeypatch.setattr(httpx, "stream", fake_stream)

    with pytest.raises(httpx.HTTPError, match="Failed to download PBF file"):
        download_from_overpass((8.0, 52.0, 8.1, 52.1), str(output))


def test_download_from_url_wraps_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "region.osm.pbf"

    def fake_stream(method, url, timeout, follow_redirects):  # noqa: ANN001, ANN202
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx, "stream", fake_stream)

    with pytest.raises(httpx.HTTPError, match="Download timed out"):
        download_from_url("https://example.org/region.osm.pbf", str(output), timeout=1)


def test_download_from_url_wraps_http_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "region.osm.pbf"

    def fake_stream(method, url, timeout, follow_redirects):  # noqa: ANN001, ANN202
        return DummyStreamResponse(
            chunks=[],
            headers={"content-length": "0"},
            raise_error=httpx.HTTPStatusError(
                "bad status",
                request=httpx.Request("GET", url),
                response=httpx.Response(500),
            ),
        )

    monkeypatch.setattr(httpx, "stream", fake_stream)

    with pytest.raises(httpx.HTTPError, match="Failed to download file"):
        download_from_url("https://example.org/region.osm.pbf", str(output))


def test_download_from_overpass_reraises_generic_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "bbox.osm.pbf"

    def fake_stream(method, url, timeout, follow_redirects):  # noqa: ANN001, ANN202
        return DummyStreamResponse(
            chunks=[b"binary"],
            headers={"content-length": "6"},
        )

    def broken_open(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        raise RuntimeError("disk write failed")

    monkeypatch.setattr(httpx, "stream", fake_stream)
    monkeypatch.setattr("builtins.open", broken_open)

    with pytest.raises(RuntimeError, match="disk write failed"):
        download_from_overpass((8.0, 52.0, 8.1, 52.1), str(output))


def test_download_from_url_reraises_generic_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "region.osm.pbf"

    def fake_stream(method, url, timeout, follow_redirects):  # noqa: ANN001, ANN202
        return DummyStreamResponse(
            chunks=[b"abc"],
            headers={"content-length": "3"},
        )

    def broken_open(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        raise RuntimeError("disk write failed")

    monkeypatch.setattr(httpx, "stream", fake_stream)
    monkeypatch.setattr("builtins.open", broken_open)

    with pytest.raises(RuntimeError, match="disk write failed"):
        download_from_url("https://example.org/region.osm.pbf", str(output))
