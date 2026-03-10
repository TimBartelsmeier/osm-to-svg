"""PBF file downloader tools."""

import os
import tempfile
from pathlib import Path

import httpx
from tqdm import tqdm

from osm_to_svg.validation import validate_bbox


def download_from_overpass(
    bbox: tuple[float, float, float, float],
    output_path: str,
    timeout: int = 300,
) -> None:
    """Download raw OSM data for a bounding box from the Overpass API.

    Streams the response to a temporary file and atomically moves it to
    ``output_path`` on success, so the destination is never left in a
    partially written state.

    Args:
        bbox: Bounding box as ``(min_lon, min_lat, max_lon, max_lat)``.
        output_path: Destination file path for the downloaded PBF data.
        timeout: HTTP request timeout in seconds (default: 300).

    Raises:
        ValueError: If the bounding box is invalid or the API returns
            HTML/XML instead of PBF data.
        httpx.HTTPError: If the download fails or times out.
    """
    min_lon, min_lat, max_lon, max_lat = validate_bbox(bbox)
    url = (
        f"https://overpass-api.de/api/map?bbox={min_lon},{min_lat},{max_lon},{max_lat}"
    )

    temp_fd, temp_path = tempfile.mkstemp(suffix=".osm.pbf", prefix="overpass_")

    try:
        os.close(temp_fd)

        with httpx.stream(
            "GET", url, timeout=timeout, follow_redirects=True
        ) as response:
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                error_content = response.read().decode("utf-8", errors="ignore")
                raise ValueError(
                    f"Overpass API returned HTML instead of PBF data.\n"
                    f"Response: {error_content[:500]}"
                )

            total_size = int(response.headers.get("content-length", 0))
            progress = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc="Downloading",
                disable=total_size == 0,
            )

            first_chunk = True
            with open(temp_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    if first_chunk and len(chunk) > 0:
                        if chunk[0:1] == b"<" or chunk[0:5] == b"<?xml":
                            progress.close()
                            raise ValueError(
                                "Downloaded file appears to be HTML/XML, not a PBF file. "
                                "The Overpass API may have returned an error page."
                            )
                        first_chunk = False
                    f.write(chunk)
                    progress.update(len(chunk))

            progress.close()

        Path(temp_path).replace(output_path)

    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

        if isinstance(e, httpx.TimeoutException):
            raise httpx.HTTPError(
                f"Download timed out after {timeout} seconds. "
                "Try a smaller bounding box or increase timeout."
            ) from e
        elif isinstance(e, httpx.HTTPError):
            raise httpx.HTTPError(
                f"Failed to download PBF file from Overpass API: {e}"
            ) from e
        else:
            raise


def download_from_url(
    url: str,
    output_path: str,
    timeout: int = 600,
) -> None:
    """Download a file from an arbitrary URL to the given output path.

    Intended for downloading PBF extracts from providers such as Geofabrik.
    Streams the response to a temporary file and atomically moves it to
    ``output_path`` on success.

    Args:
        url: Direct download URL.
        output_path: Destination file path for the downloaded data.
        timeout: HTTP request timeout in seconds (default: 600).

    Raises:
        httpx.HTTPError: If the download fails or times out.
    """
    temp_fd, temp_path = tempfile.mkstemp(suffix=".osm.pbf", prefix="download_")

    try:
        os.close(temp_fd)

        with httpx.stream(
            "GET", url, timeout=timeout, follow_redirects=True
        ) as response:
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            progress = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc="Downloading",
                disable=total_size == 0,
            )

            with open(temp_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                    f.write(chunk)
                    progress.update(len(chunk))

            progress.close()

        Path(temp_path).replace(output_path)

    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

        if isinstance(e, httpx.TimeoutException):
            raise httpx.HTTPError(
                f"Download timed out after {timeout} seconds. "
                "Large files may need a longer timeout."
            ) from e
        elif isinstance(e, httpx.HTTPError):
            raise httpx.HTTPError(f"Failed to download file: {e}") from e
        else:
            raise
