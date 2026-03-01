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
    """Download OSM PBF file from Overpass API for a bounding box.

    Args:
        bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)
        output_path: Path where the PBF file will be saved
        timeout: Request timeout in seconds (default: 300)

    Raises:
        httpx.HTTPError: If the download fails
        ValueError: If the bounding box is invalid or response is not a valid PBF file

    Example:
        >>> download_from_overpass((11.54, 48.14, 11.55, 48.15), "munich.osm.pbf")
    """
    min_lon, min_lat, max_lon, max_lat = validate_bbox(bbox)

    # Overpass API map call with bounding box
    # Format: /api/map?bbox=left,bottom,right,top
    url = (
        f"https://overpass-api.de/api/map?bbox={min_lon},{min_lat},{max_lon},{max_lat}"
    )

    # Use a temporary file to avoid creating empty output files on failure
    temp_fd, temp_path = tempfile.mkstemp(suffix=".osm.pbf", prefix="overpass_")

    try:
        os.close(temp_fd)  # Close the file descriptor, we'll use the path

        with httpx.stream(
            "GET", url, timeout=timeout, follow_redirects=True
        ) as response:
            response.raise_for_status()

            # Check content type to detect HTML error pages
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                # Read the response to see the actual error
                error_content = response.read().decode("utf-8", errors="ignore")
                raise ValueError(
                    f"Overpass API returned HTML instead of PBF data.\n"
                    f"Response: {error_content[:500]}"
                )

            # Get total size if available
            total_size = int(response.headers.get("content-length", 0))

            # Setup progress bar
            progress = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc="Downloading",
                disable=total_size == 0,  # Disable if size unknown
            )

            first_chunk = True
            with open(temp_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    # Validate first chunk contains PBF magic bytes
                    if first_chunk and len(chunk) > 0:
                        # PBF files should not start with '<' (HTML) or other text
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

        # Download successful - move temp file to final location
        Path(temp_path).replace(output_path)

    except Exception as e:
        # Clean up temp file on any error
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
    """Download a PBF file from a direct URL.

    Works with Geofabrik, BBBike, or any other PBF download service.
    Geofabrik provides daily updated regional extracts that are more reliable
    than the Overpass API for larger areas.

    Args:
        url: Direct URL to the PBF file
        output_path: Path where the PBF file will be saved
        timeout: Request timeout in seconds (default: 600 for large files)

    Raises:
        httpx.HTTPError: If the download fails

    Example:
        >>> download_from_url(
        ...     "https://download.geofabrik.de/europe/germany/niedersachsen-latest.osm.pbf",
        ...     "niedersachsen.osm.pbf"
        ... )

    Popular sources:
        - Geofabrik: https://download.geofabrik.de/
        - BBBike: https://download.bbbike.org/
    """
    # Use a temporary file to avoid creating empty output files on failure
    temp_fd, temp_path = tempfile.mkstemp(suffix=".osm.pbf", prefix="download_")

    try:
        os.close(temp_fd)  # Close the file descriptor, we'll use the path

        with httpx.stream(
            "GET", url, timeout=timeout, follow_redirects=True
        ) as response:
            response.raise_for_status()

            # Get total size if available
            total_size = int(response.headers.get("content-length", 0))

            # Setup progress bar
            progress = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc="Downloading",
                disable=total_size == 0,  # Disable if size unknown
            )

            # Stream download to handle large files efficiently
            with open(temp_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                    f.write(chunk)
                    progress.update(len(chunk))

            progress.close()

        # Download successful - move temp file to final location
        Path(temp_path).replace(output_path)

    except Exception as e:
        # Clean up temp file on any error
        if os.path.exists(temp_path):
            os.unlink(temp_path)

        if isinstance(e, httpx.TimeoutException):
            raise httpx.HTTPError(
                f"Download timed out after {timeout} seconds. "
                f"Large files may need a longer timeout."
            ) from e
        elif isinstance(e, httpx.HTTPError):
            raise httpx.HTTPError(f"Failed to download file: {e}") from e
        else:
            raise
