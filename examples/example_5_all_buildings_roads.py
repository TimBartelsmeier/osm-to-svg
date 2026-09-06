"""Example 5: Render all buildings and all roads.

Note: This example renders ALL building and road types in the bounding box,
which can result in very large SVG files (potentially 10+ MB) depending on
the area size and density of features. Processing time may also be significant.
Consider using a smaller bounding box or specific subtypes for production use.
"""

from pathlib import Path

from osm_to_svg import FeatureLayer, Style, create_map, features

# Set up directories relative to this script
script_dir = Path(__file__).parent
osmdata_dir = script_dir / "osmdata"
output_dir = script_dir / "output"
output_dir.mkdir(exist_ok=True)

# File paths
hannover_pbf = osmdata_dir / "hannover.osm.pbf"
output_svg = output_dir / "all_buildings_roads.svg"

# Bounding box for Hannover obtained from example_1_geocode_bbox.py
hannover_bbox = (52.34, 9.68, 52.41, 9.79)

# Render all buildings and roads
print("Rendering all buildings and roads.")
print("This may take a while...")
print()

# All building types via dedicated shorthand
all_buildings = features.BUILDINGS.ALL

# All road types combined into one spec via |
all_roads = features.ROADS.MAJOR | features.ROADS.LOCAL | features.ROADS.PEDESTRIAN

create_map(
    pbf_path=str(hannover_pbf),
    bounds=hannover_bbox,
    background_color="#FFFFFF",
    feature_layers=[
        FeatureLayer(all_buildings, Style(fill="#925000")),
        FeatureLayer(all_roads, Style(stroke="#000000", stroke_width=0.25)),
    ],
    output_path=str(output_svg),
    show_progress=True,
)

print()
print(f"Saved: {output_svg}")
