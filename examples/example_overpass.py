"""Alternative Example: Download a small region centered on Hannover from Overpass API."""

from pathlib import Path

import httpx

from osm_to_svg import download_from_overpass

# Set up directories relative to this script
script_dir = Path(__file__).parent
osmdata_dir = script_dir / "osmdata"
osmdata_dir.mkdir(exist_ok=True)

# File path
hannover_center_pbf = osmdata_dir / "hannover_center_overpass.osm.pbf"

# Small bounding box centered on Hannover center
# Overpass API has limitations - keep the area small
# Using a smaller area than the standard bbox from example_1_geocode_bbox.py
hannover_center_bbox = (52.372, 9.735, 52.378, 9.745)

# Download from Overpass API
print("Downloading hannover_center_overpass.osm.pbf from Overpass API...")
print("Note: Overpass API is often overloaded and may timeout.")

try:
    download_from_overpass(
        bbox=hannover_center_bbox,
        output_path=str(hannover_center_pbf),
        timeout=180,
    )
    print(f"Downloaded: {hannover_center_pbf}")
except httpx.HTTPStatusError as e:
    print(f"\nError: Overpass API failed with status {e.response.status_code}")
    if e.response.status_code == 504:
        print("The server timed out - Overpass API is overloaded.")
    elif e.response.status_code == 429:
        print("Too many requests - you've been rate limited.")
    print(
        "Recommendation: Use example_2_download_extract_pbf.py instead (Geofabrik method)."
    )
    print("It's much more reliable and works for any area size.")
    exit(1)
except Exception as e:
    print(f"\nError: {e}")
    print(
        "Recommendation: Use example_2_download_extract_pbf.py instead (Geofabrik method)."
    )
    exit(1)
