"""Example 2: Download niedersachsen.osm.pbf from Geofabrik and extract Hannover region."""

from pathlib import Path

from osm_to_svg import download_from_url, extract_from_pbf

# Set up directories relative to this script
script_dir = Path(__file__).parent
osmdata_dir = script_dir / "osmdata"
osmdata_dir.mkdir(exist_ok=True)

# File paths
niedersachsen_pbf = osmdata_dir / "niedersachsen.osm.pbf"
hannover_pbf = osmdata_dir / "hannover.osm.pbf"

# Bounding box for Hannover obtained from example_1_geocode_bbox.py
hannover_bbox = (52.34, 9.68, 52.41, 9.79)

# Download Niedersachsen from Geofabrik
if not niedersachsen_pbf.exists():
    print("Downloading niedersachsen.osm.pbf from Geofabrik...")
    download_from_url(
        url="https://download.geofabrik.de/europe/germany/niedersachsen-latest.osm.pbf",
        output_path=str(niedersachsen_pbf),
        timeout=1200,
    )
    print(f"Downloaded: {niedersachsen_pbf}")
else:
    print(f"Already exists: {niedersachsen_pbf}")

# Extract Hannover region
print("Extracting Hannover region...")
extract_from_pbf(
    source_pbf_path=str(niedersachsen_pbf),
    bbox=hannover_bbox,
    output_path=str(hannover_pbf),
)
print(f"Extracted: {hannover_pbf}")
