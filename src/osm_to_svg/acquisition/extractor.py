"""PBF file extraction tools using osmium-tool."""

import subprocess
from pathlib import Path

from osm_to_svg.validation import validate_bbox


def extract_from_pbf(
    source_pbf_path: str,
    bbox: tuple[float, float, float, float],
    output_path: str,
) -> None:
    min_lon, min_lat, max_lon, max_lat = validate_bbox(bbox)

    source_path = Path(source_pbf_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source PBF file not found: {source_pbf_path}")

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
