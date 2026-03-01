"""PBF file extraction tools using osmium-tool."""

import subprocess
from pathlib import Path

from osm_to_svg.validation import validate_bbox


def extract_from_pbf(
    source_pbf_path: str,
    bbox: tuple[float, float, float, float],
    output_path: str,
) -> None:
    """Extract a region from a larger PBF file using osmium-tool.

    This method is more robust than downloading from Overpass API, as it works
    with pre-downloaded regional extracts from sources like Geofabrik.

    Args:
        source_pbf_path: Path to the source PBF file (e.g., from Geofabrik)
        bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)
        output_path: Path where the extracted PBF file will be saved

    Raises:
        FileNotFoundError: If source PBF file doesn't exist
        RuntimeError: If osmium extraction fails
        ValueError: If the bounding box is invalid

    Example:
        >>> extract_from_pbf(
        ...     "niedersachsen.osm.pbf",
        ...     (9.73, 52.37, 9.75, 52.38),
        ...     "hannover.osm.pbf"
        ... )

    Note:
        Requires osmium-tool to be installed. With pixi, it's included automatically.
    """
    min_lon, min_lat, max_lon, max_lat = validate_bbox(bbox)

    # Check if source file exists
    source_path = Path(source_pbf_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source PBF file not found: {source_pbf_path}")

    # Build osmium extract command
    bbox_str = f"{min_lon},{min_lat},{max_lon},{max_lat}"
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
