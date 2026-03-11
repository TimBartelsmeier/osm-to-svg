"""Example 3: Render the road network using ROADS.MAJOR shorthand (black lines)."""

from pathlib import Path

from osm_to_svg import Style, create_map, features

# Set up directories relative to this script
script_dir = Path(__file__).parent
osmdata_dir = script_dir / "osmdata"
output_dir = script_dir / "output"
output_dir.mkdir(exist_ok=True)

# File paths
hannover_pbf = osmdata_dir / "hannover.osm.pbf"
output_svg = output_dir / "basic.svg"

# Bounding box for Hannover obtained from example_1_geocode_bbox.py
hannover_bbox = (52.34, 9.68, 52.41, 9.79)

# Render the road network
print("Rendering major roads...")
create_map(
    pbf_path=str(hannover_pbf),
    bounds=hannover_bbox,
    feature_layers=[
        (
            features.ROADS.MAJOR,
            Style(stroke="#000000", stroke_width=2.0),
        )
    ],
    output_path=str(output_svg),
    show_progress=True,
)
print(f"Saved: {output_svg}")
