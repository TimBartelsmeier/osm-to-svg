"""Example 5: Render all buildings and all roads.

Note: This example renders ALL building and road types in the bounding box,
which can result in very large SVG files (potentially 10+ MB) depending on
the area size and density of features. Processing time may also be significant.
Consider using a smaller bounding box or specific subtypes for production use.
"""

from pathlib import Path

from osm_to_svg import (
    FeatureLayer,
    Style,
    create_map,
    features,
    geocode_place,
    get_bbox_around_coordinates,
)

# Set up directories relative to this script
script_dir = Path(__file__).parent
osmdata_dir = script_dir / "osmdata"
output_dir = script_dir / "output"
output_dir.mkdir(exist_ok=True)

# File paths
hannover_pbf = osmdata_dir / "hannover.osm.pbf"

# Bounding box for Hannover obtained from example_1_geocode_bbox.py
hannover_bbox = (52.34, 9.68, 52.41, 9.79)

feature_major_roads = features.ROADS.MAJOR
feature_parks = features.GREEN_SPACES.PARKS

herrenhäuser_gärten_coord = geocode_place("Großer Garten, Hannover")
herrenhäuser_gärten_bbox = get_bbox_around_coordinates(
    *herrenhäuser_gärten_coord,
    width_km=0.5,
    height_km=0.5,
)

print("Rendering parks and major roads, full bbox each ...")
create_map(
    pbf_path=str(hannover_pbf),
    bounds=hannover_bbox,
    background_color="#FFFFFF",
    feature_layers=[
        FeatureLayer(
            features=feature_major_roads,
            style=Style(stroke="#000000", stroke_width=2.0),
        ),
        FeatureLayer(
            features=feature_parks,
            style=Style(fill="#0A9C0A"),
        ),
    ],
    output_path=str(output_dir / "sub_bbox disabled.svg"),
    show_progress=True,
)

print()
print("Rendering major roads for full bbox and parks for a sub-bbox ...")
create_map(
    pbf_path=str(hannover_pbf),
    bounds=hannover_bbox,
    background_color="#FFFFFF",
    feature_layers=[
        FeatureLayer(
            features=features.ROADS.MAJOR,
            style=Style(stroke="#000000", stroke_width=2.0),
        ),
        FeatureLayer(
            features=feature_parks,
            style=Style(fill="#0A9C0A"),
            bbox=herrenhäuser_gärten_bbox,
        ),
    ],
    output_path=str(output_dir / "sub_bbox enabled.svg"),
    show_progress=True,
)
