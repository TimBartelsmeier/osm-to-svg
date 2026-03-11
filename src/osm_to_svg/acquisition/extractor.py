"""PBF file extraction tools using osmium-tool."""

import subprocess
from pathlib import Path

from osm_to_svg.validation import validate_bbox


def extract_from_pbf(
    source_pbf_path: str,
    bbox: tuple[float, float, float, float],
    output_path: str,
) -> None:
    """Extract a bounding-box region from a PBF file using osmium-tool.

    Args:
        source_pbf_path: Path to the source OSM PBF file.
        bbox: Bounding box to extract as ``(south_lat, west_lon, north_lat, east_lon)``.
        output_path: Destination path for the extracted PBF file.

    Raises:
        FileNotFoundError: If the source PBF file does not exist.
        ValueError: If the bounding box is invalid.
        RuntimeError: If osmium-tool is not installed or the extraction fails.
    """
    south_lat, west_lon, north_lat, east_lon = validate_bbox(bbox)

    source_path = Path(source_pbf_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source PBF file not found: {source_pbf_path}")

    bbox_str = f"{west_lon},{south_lat},{east_lon},{north_lat}"
    cmd = [
        "osmium",
        "extract",
        "-b",
        bbox_str,
        str(source_path),
        "-o",
        output_path,
        "--overwrite",
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"osmium extraction failed: {e.stderr}\nCommand: {' '.join(cmd)}"
        ) from e
    except FileNotFoundError:
        raise RuntimeError(
            "osmium-tool not found (in a conda or pixi project, you can install it directly from conda-forge)"
        )
