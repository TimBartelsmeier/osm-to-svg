# osm-to-svg

A Python library for generating SVG maps from OpenStreetMap data. It reads PBF files, projects geographic coordinates, and renders styled layers for roads, waterways, railways, buildings, green spaces, and POI markers.

## Installation

The library is not published to PyPI. To use it, install [pixi](https://prefix.dev/), clone the repository, and run:

```bash
git clone <repo-url>
cd city-map-svg
pixi install
```

## Data acquisition

### Recommended: Geofabrik + extraction

The recommended approach is to download a pre-built PBF file (for example, from [Geofabrik](https://download.geofabrik.de/)) and extract the region of interest using `extract_from_pbf`. This is more reliable than Overpass and supports any bounding box size.

```python
from osm_to_svg import download_from_url, extract_from_pbf

download_from_url(
    url="https://download.geofabrik.de/europe/germany/niedersachsen-latest.osm.pbf",
    output_path="niedersachsen.osm.pbf",
)

extract_from_pbf(
    source_pbf_path="niedersachsen.osm.pbf",
    bbox=(9.68, 52.34, 9.79, 52.41),  # (min_lon, min_lat, max_lon, max_lat)
    output_path="hannover.osm.pbf",
)
```

See [examples/example_2_download_extract_pbf.py](examples/example_2_download_extract_pbf.py) for the full script.

### Alternative: Overpass API

Data can also be downloaded directly from the Overpass API:

```python
from osm_to_svg import download_from_overpass

download_from_overpass(bbox=(9.735, 52.372, 9.745, 52.378), output_path="area.osm.pbf")
```

Note that the Overpass API is often overloaded, may time out, applies rate limiting, and only supports small bounding boxes.

## Bounding box considerations and querying place names

The PBF file should cover only the region of interest. Everything contained in the file is rendered into the SVG, so a smaller file produces a smaller SVG and faster rendering times. It is recommended to pass the bounding box explicitly to `SvgMapper`, even if the PBF file is already cropped to the region of interest, because some features (such as long roads) can extend beyond the selected region. Specifying the bounding box ensures the SVG is sized correctly and clips to the region of interest.

You can obtain a bounding box for a named place using `get_bbox_from_place`:

```python
from osm_to_svg import get_bbox_from_place

bbox = get_bbox_from_place("Hannover, Germany", width_km=7.5, height_km=7.5)
# returns (min_lon, min_lat, max_lon, max_lat)
```

See [examples/example_1_geocode_bbox.py](examples/example_1_geocode_bbox.py) for details.

## Basic usage

`SvgMapper` is the main class. It is used as a context manager and renders one or more feature layers that are combined into a final SVG.

```python
from osm_to_svg import MAJOR_ROADS, RoadType, Style, SvgMapper

bbox = (9.68, 52.34, 9.79, 52.41)

with SvgMapper("hannover.osm.pbf", bounds=bbox) as mapper:
    mapper.render_features(
        feature_type=RoadType,
        subtypes=MAJOR_ROADS,
        style=Style(stroke="#000000", stroke_width=2.0),
        output_path="roads.svg",
    )
```

See [examples/example_3_basic_usage.py](examples/example_3_basic_usage.py) for the full script.

## Multiple layers

Multiple feature types can be rendered as separate layers and combined into a single SVG. Supported feature types are `RoadType`, `RailwayType`, `WaterwayType`, `BuildingType`, and `GreenSpaceType`. Each type comes with predefined shorthand groups (e.g. `MAJOR_ROADS`, `WATER_BODIES`, `FORESTS`).

```python
from osm_to_svg import (
    FORESTS, MAJOR_ROADS, WATER_BODIES,
    GreenSpaceType, RoadType, Style, SvgMapper, WaterwayType,
)

bbox = (9.68, 52.34, 9.79, 52.41)

with SvgMapper("hannover.osm.pbf", bounds=bbox) as mapper:
    mapper.render_features(WaterwayType, WATER_BODIES, Style(fill="#4A90E2"))
    mapper.render_features(GreenSpaceType, FORESTS, Style(fill="#046A04"))
    mapper.render_features(RoadType, MAJOR_ROADS, Style(stroke="#000000", stroke_width=2.0))
    mapper.save("map.svg")
```

See [examples/example_4_multiple_layers.py](examples/example_4_multiple_layers.py) for the full script including POI markers.

## SvgMapper options

`SvgMapper` accepts the following constructor arguments:

- `pbf_path` — path to the `.osm.pbf` file to read.
- `scale` — map scale denominator (default: `100000` for 1:100,000). At this scale, 1 km in reality equals 1 cm in the output. The scale is accurate at the centre latitude of the map bounds.
- `dpi` — dots per inch for the output SVG (default: `96`). Common values: `96` (screen), `72` (print), `300` (high-res print).
- `bounds` — optional bounding box as `(min_lon, min_lat, max_lon, max_lat)`. If omitted, bounds are derived from the PBF file by scanning all nodes.
- `background_color` — optional background fill for the SVG (e.g. `"#FFFFFF"`, `"white"`). Defaults to `None` (transparent).

```python
from osm_to_svg import Style, SvgMapper, RoadType, MAJOR_ROADS

with SvgMapper(
    "hannover.osm.pbf",
    scale=75000,
    dpi=300,
    bounds=(9.68, 52.34, 9.79, 52.41),
    background_color="#F5F5F5",
) as mapper:
    mapper.render_features(RoadType, MAJOR_ROADS, Style(stroke="#000000"))
    mapper.save_combined("map.svg")
```

Layers can either be written to individual files by passing `output_path` to `render_features`, or accumulated in memory (omit `output_path`) and flushed to a single file with `save_combined`. When saving individual files use `combine` to merge them:

```python
with SvgMapper("hannover.osm.pbf", bounds=bbox) as mapper:
    mapper.render_features(WaterwayType, WATER_BODIES, Style(fill="#4A90E2"), "water.svg")
    mapper.render_features(RoadType, MAJOR_ROADS, Style(stroke="#000000"), "roads.svg")
    mapper.combine(["water.svg", "roads.svg"], "map.svg")
```

## Styling

Feature layers are styled with the `Style` class. All attributes are optional and default to no stroke and no fill (i.e. invisible).

- `stroke` — stroke colour as a CSS colour string (e.g. `"#000000"`, `"red"`). Use `"none"` for no stroke (default: `"none"`).
- `stroke_width` — stroke width in points (1 pt = 1/72 inch) (default: `1.0`).
- `fill` — fill colour. Use `"none"` for no fill (default: `"none"`).
- `opacity` — overall opacity, `0.0`–`1.0` (default: `1.0`).
- `stroke_opacity` — stroke-only opacity, `0.0`–`1.0` (default: `None`, inherits `opacity`).
- `fill_opacity` — fill-only opacity, `0.0`–`1.0` (default: `None`, inherits `opacity`).

```python
from osm_to_svg import Style

# Solid filled polygon (e.g. water body)
water_style = Style(fill="#4A90E2")

# Stroked line with no fill (e.g. road)
road_style = Style(stroke="#333333", stroke_width=1.5)

# Semi-transparent overlay
overlay_style = Style(fill="#1FC21F", fill_opacity=0.6)

# Combined stroke and fill with separate opacities
combined_style = Style(
    stroke="#000000",
    stroke_width=0.5,
    stroke_opacity=0.8,
    fill="#FFD700",
    fill_opacity=0.4,
)
```

## POI markers

`place_poi_markers` places an SVG icon at one or more geographic coordinates. The output layer has the same dimensions as feature layers, so it can be combined directly.

```python
mapper.place_poi_markers(
    marker_svg_path="pin.svg",
    coords=[(52.3731, 9.7372), (52.3665, 9.7353)],  # (lat, lon)
    scale=1.5,          # relative to the marker's original size
    anchor="bottom",    # which point of the icon aligns to the coordinate
)
```

**Sizing** — exactly one of the following must be provided:

- `scale` — scale factor relative to the marker's original size (`1.0` = original, `2.0` = double).
- `width_meters` — desired marker width in metres on the map.
- `height_meters` — desired marker height in metres on the map.

**Anchor** — the `anchor` parameter controls which point of the icon is pinned to the coordinate. Accepted values: `"center"` (default), `"top"`, `"top-right"`, `"right"`, `"bottom-right"`, `"bottom"`, `"bottom-left"`, `"left"`, `"top-left"`.

```python
# Absolute sizing — marker is always 200 m wide regardless of scale
mapper.place_poi_markers("pin.svg", [(52.37, 9.74)], width_meters=200.0)

# In-memory workflow — layer is combined with render_features layers
with SvgMapper("hannover.osm.pbf", bounds=bbox) as mapper:
    mapper.render_features(RoadType, MAJOR_ROADS, Style(stroke="#000000"))
    mapper.place_poi_markers("pin.svg", [(52.3731, 9.7372)], scale=1.0, anchor="bottom")
    mapper.save_combined("map.svg")
```

## Running the examples

All examples can be run via pixi:

| Command | Description |
|---|---|
| `pixi run example-1` | Geocode a place name and print its bounding box |
| `pixi run example-2` | Download a Geofabrik PBF and extract a region |
| `pixi run example-3` | Render major roads as a basic SVG |
| `pixi run example-4` | Multi-layer map with water, green spaces, roads, railways, and POIs |
| `pixi run example-5` | Render all buildings and roads |
| `pixi run example-overpass` | Download data via Overpass API (may fail due to API limitations) |

## Available features

### RoadType

OSM tag: `highway`

- `MOTORWAY` (`motorway`)
- `MOTORWAY_LINK` (`motorway_link`)
- `TRUNK` (`trunk`)
- `TRUNK_LINK` (`trunk_link`)
- `PRIMARY` (`primary`)
- `PRIMARY_LINK` (`primary_link`)
- `SECONDARY` (`secondary`)
- `SECONDARY_LINK` (`secondary_link`)
- `TERTIARY` (`tertiary`)
- `TERTIARY_LINK` (`tertiary_link`)
- `RESIDENTIAL` (`residential`)
- `UNCLASSIFIED` (`unclassified`)
- `SERVICE` (`service`)
- `LIVING_STREET` (`living_street`)
- `CYCLEWAY` (`cycleway`)
- `FOOTWAY` (`footway`)
- `PATH` (`path`)
- `PEDESTRIAN` (`pedestrian`)
- `STEPS` (`steps`)
- `TRACK` (`track`)
- `ROAD` (`road`)

Shorthands:

| Shorthand | Subtypes included |
|---|---|
| `MAJOR_ROADS` | MOTORWAY, MOTORWAY_LINK, TRUNK, TRUNK_LINK, PRIMARY, PRIMARY_LINK, SECONDARY, SECONDARY_LINK, TERTIARY, TERTIARY_LINK |
| `ARTERIAL_ROADS` | MOTORWAY, MOTORWAY_LINK, TRUNK, TRUNK_LINK, PRIMARY, PRIMARY_LINK |
| `LOCAL_ROADS` | RESIDENTIAL, UNCLASSIFIED, SERVICE, LIVING_STREET |
| `PEDESTRIAN_PATHS` | FOOTWAY, PATH, PEDESTRIAN, STEPS |

### RailwayType

OSM tag: `railway`

- `RAIL` (`rail`)
- `LIGHT_RAIL` (`light_rail`)
- `SUBWAY` (`subway`)
- `TRAM` (`tram`)
- `MONORAIL` (`monorail`)
- `FUNICULAR` (`funicular`)
- `NARROW_GAUGE` (`narrow_gauge`)
- `ABANDONED` (`abandoned`)
- `DISUSED` (`disused`)
- `PRESERVED` (`preserved`)

Shorthands:

| Shorthand | Subtypes included |
|---|---|
| `ACTIVE_RAILWAYS` | RAIL, LIGHT_RAIL, SUBWAY, TRAM, MONORAIL, FUNICULAR, NARROW_GAUGE |
| `URBAN_TRANSIT` | LIGHT_RAIL, SUBWAY, TRAM, MONORAIL |
| `INACTIVE_RAILWAYS` | ABANDONED, DISUSED, PRESERVED |

### WaterwayType

OSM tags: `waterway`, `natural`

- `RIVER` (`river`)
- `STREAM` (`stream`)
- `CANAL` (`canal`)
- `DRAIN` (`drain`)
- `DITCH` (`ditch`)
- `WATER` (`water`)
- `LAKE` (`lake`)
- `RESERVOIR` (`reservoir`)
- `POND` (`pond`)
- `COASTLINE` (`coastline`)

Shorthands:

| Shorthand | Subtypes included |
|---|---|
| `LINEAR_WATERWAYS` | RIVER, STREAM, CANAL, DRAIN, DITCH |
| `WATER_BODIES` | WATER, LAKE, RESERVOIR, POND |
| `NATURAL_WATERWAYS` | RIVER, STREAM, LAKE, POND |
| `ARTIFICIAL_WATERWAYS` | CANAL, DRAIN, DITCH, RESERVOIR |
| `MAJOR_WATERWAYS` | RIVER, CANAL |

### BuildingType

OSM tag: `building`

- `YES` (`yes`)
- `BUILDING` (`building`)
- `RESIDENTIAL` (`residential`)
- `HOUSE` (`house`)
- `DETACHED` (`detached`)
- `SEMIDETACHED_HOUSE` (`semidetached_house`)
- `APARTMENTS` (`apartments`)
- `TERRACE` (`terrace`)
- `BUNGALOW` (`bungalow`)
- `COMMERCIAL` (`commercial`)
- `RETAIL` (`retail`)
- `OFFICE` (`office`)
- `SUPERMARKET` (`supermarket`)
- `HOTEL` (`hotel`)
- `INDUSTRIAL` (`industrial`)
- `WAREHOUSE` (`warehouse`)
- `MANUFACTURE` (`manufacture`)
- `HOSPITAL` (`hospital`)
- `SCHOOL` (`school`)
- `UNIVERSITY` (`university`)
- `CHURCH` (`church`)
- `CATHEDRAL` (`cathedral`)
- `MOSQUE` (`mosque`)
- `TEMPLE` (`temple`)
- `SYNAGOGUE` (`synagogue`)
- `GOVERNMENT` (`government`)
- `CIVIC` (`civic`)
- `PUBLIC` (`public`)
- `GARAGE` (`garage`)
- `GARAGES` (`garages`)
- `PARKING` (`parking`)
- `SHED` (`shed`)
- `ROOF` (`roof`)
- `CONSTRUCTION` (`construction`)

Shorthands:

| Shorthand | Subtypes included |
|---|---|
| `RESIDENTIAL_BUILDINGS` | RESIDENTIAL, HOUSE, DETACHED, SEMIDETACHED_HOUSE, APARTMENTS, TERRACE, BUNGALOW |
| `COMMERCIAL_BUILDINGS` | COMMERCIAL, RETAIL, OFFICE, SUPERMARKET, HOTEL |
| `INDUSTRIAL_BUILDINGS` | INDUSTRIAL, WAREHOUSE, MANUFACTURE |
| `RELIGIOUS_BUILDINGS` | CHURCH, CATHEDRAL, MOSQUE, TEMPLE, SYNAGOGUE |
| `INSTITUTIONAL_BUILDINGS` | HOSPITAL, SCHOOL, UNIVERSITY, GOVERNMENT, CIVIC, PUBLIC |
| `SINGLE_FAMILY_HOMES` | HOUSE, DETACHED, SEMIDETACHED_HOUSE, BUNGALOW |
| `MULTI_FAMILY_HOMES` | APARTMENTS, TERRACE |

### GreenSpaceType

OSM tags: `leisure`, `natural`, `landuse`

- `PARK` (`park`) — `leisure`
- `GARDEN` (`garden`) — `leisure`
- `NATURE_RESERVE` (`nature_reserve`) — `leisure`
- `RECREATION_GROUND` (`recreation_ground`) — `leisure`
- `COMMON` (`common`) — `leisure`
- `GOLF_COURSE` (`golf_course`) — `leisure`
- `WOOD` (`wood`) — `natural`
- `SCRUB` (`scrub`) — `natural`
- `GRASSLAND` (`grassland`) — `natural`
- `HEATH` (`heath`) — `natural`
- `WETLAND` (`wetland`) — `natural`
- `FOREST` (`forest`) — `landuse`
- `MEADOW` (`meadow`) — `landuse`
- `GRASS` (`grass`) — `landuse`
- `ORCHARD` (`orchard`) — `landuse`
- `VINEYARD` (`vineyard`) — `landuse`
- `CEMETERY` (`cemetery`) — `landuse`
- `ALLOTMENTS` (`allotments`) — `landuse`

Shorthands:

| Shorthand | Subtypes included |
|---|---|
| `PARKS_AND_GARDENS` | PARK, GARDEN, RECREATION_GROUND, COMMON |
| `FORESTS` | WOOD, FOREST |
| `NATURAL_VEGETATION` | WOOD, SCRUB, GRASSLAND, HEATH, WETLAND |
| `PROTECTED_AREAS` | NATURE_RESERVE, WETLAND |
| `AGRICULTURAL_LAND` | MEADOW, GRASS, ORCHARD, VINEYARD, ALLOTMENTS |
| `ALL_GREEN_SPACES` | PARK, GARDEN, NATURE_RESERVE, RECREATION_GROUND, COMMON, WOOD, SCRUB, GRASSLAND, HEATH, WETLAND, FOREST, MEADOW, GRASS |
