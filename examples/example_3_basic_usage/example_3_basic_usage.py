"""Example 3: Render the road network using ROADS.MAJOR shorthand (black lines)."""

from pathlib import Path

from osm_to_svg import FeatureLayer, Style, create_map, features

# Set up directories relative to this script
script_dir = Path(__file__).parent
osmdata_dir = script_dir.parent / "osmdata"

# File paths
hannover_pbf = osmdata_dir / "hannover.osm.pbf"
output_svg = script_dir / "basic.svg"

if not hannover_pbf.is_file():
    print(
        f"Missing required data file: {hannover_pbf}. "
        "Run example 2 first: pixi run example-2"
    )
    raise SystemExit(1)

# Bounding box for Hannover obtained from example_1_geocode_bbox.py
hannover_bbox = (52.34, 9.68, 52.41, 9.79)

# Render the road network
print("Rendering major roads...")
create_map(
    pbf_path=str(hannover_pbf),
    bounds=hannover_bbox,
    background_color="#FFFFFF",
    feature_layers=[
        FeatureLayer(
            features.ROADS.MAJOR,
            Style(stroke="#000000", stroke_width=2.0),
        )
    ],
    output_path=str(output_svg),
    show_progress=True,
)
print(f"Saved: {output_svg}")
