"""Example 4: Comprehensive map with water, roads, railways, green spaces, and POI markers."""

from pathlib import Path

from osm_to_svg import (
    FeatureLayer,
    PoiStyle,
    Style,
    create_map,
    features,
    geocode_place,
)

# Set up directories relative to this script
script_dir = Path(__file__).parent
osmdata_dir = script_dir / "osmdata"
output_dir = script_dir / "output"
output_dir.mkdir(exist_ok=True)

# File paths
hannover_pbf = osmdata_dir / "hannover.osm.pbf"
marker_svg = script_dir / "poi marker.svg"
output_svg = output_dir / "advanced.svg"

# Bounding box for Hannover obtained from example_1_geocode_bbox.py
hannover_bbox = (52.34, 9.68, 52.41, 9.79)

# POI names geocoded to (latitude, longitude)
poi_places = [
    "Kröpcke, Hannover, Germany",
    "Landtag Niedersachsen, Hannover, Germany",
    "Leibniz University Hannover, Germany",
]

print("Geocoding POIs...")
pois = [geocode_place(place) for place in poi_places]

# Render multiple layers
print("Rendering comprehensive map:")
print("  - Water bodies")
print("  - Forests")
print("  - Parks and gardens")
print("  - Major roads")
print("  - Local roads")
print("  - Railways")
print("  - POI markers")
print("This may take some time...")
print()
create_map(
    pbf_path=str(hannover_pbf),
    bounds=hannover_bbox,
    background_color="#FFFFFF",
    feature_layers=[
        FeatureLayer(features.WATER_POLYGONS.OPEN_WATER, Style(fill="#4A90E2")),
        FeatureLayer(features.GREEN_SPACES.FORESTS, Style(fill="#046A04")),
        FeatureLayer(features.GREEN_SPACES.PARKS, Style(fill="#1FC21F")),
        FeatureLayer(features.ROADS.MAJOR, Style(stroke="#000000", stroke_width=1)),
        FeatureLayer(features.ROADS.LOCAL, Style(stroke="#5E5E5E", stroke_width=0.5)),
        FeatureLayer(
            features.RAILWAYS.ACTIVE, Style(stroke="#FF8C00", stroke_width=0.2)
        ),
    ],
    poi_layers=[
        (
            pois,
            PoiStyle(
                marker_svg_path=str(marker_svg),
                width_meters=500,
            ),
        )
    ],
    output_path=str(output_svg),
    show_progress=True,
)

print()
print(f"Saved: {output_svg}")
