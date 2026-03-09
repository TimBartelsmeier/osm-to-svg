# osm-to-svg

A Python library for generating SVG maps from OpenStreetMap data. It reads PBF files, projects geographic coordinates, and renders styled layers for roads, waterways, railways, buildings, green spaces, and POI markers.

> [!NOTE]
> This project was programmed entirely with AI tools (Github Copilot with Claude Sonnet 4.5 & 4.6 and GPT-5.3.-Codex). This was partly because I needed such a tool for a private project but didn't have the time to implement it myself, and partly because I wanted to try out for myself how well “vibecoding” works.
I have tested the functionality and, at least for my application, everything works as expected and without unintended side-effects. However, I have only given a cursory inspection to the generated code itself and I accept no liability for it.

## Installation

The library is currently not published to PyPI. You can install it directly from this repo with your favorite package manager that supports installing from git. I recommend and use [`pixi`](https://pixi.prefix.dev/latest/), for which you'd do something like this:

1. [Install pixi on you system](https://pixi.prefix.dev/latest/installation)
2. Create a new directory for your project.
3. Open a terminal in the directory and run `pixi init`
4. Run `pixi add python`
5. Run `pixi add --pypi "osm-to-svg @ git+https://github.com/TimBartelsmeier/osm-to-svg"` to install this repository.
6. Done! You can now use this package in python by importing `osm_to_svg`. Note that with pixi, you need to run `pixi run python <file/arguments>` instead of `python <file/arguments>`.

To play around with the styling options and see the results immediately, it is best to work in a Jupyter notebook.

## Data acquisition

### Recommended: Download large file from hoster and extract region-of-interest

The recommended approach is to download a pre-built PBF file (for example, from [Geofabrik](https://download.geofabrik.de/)) and extract the region of interest using `extract_from_pbf`. This is more reliable than Overpass and supports any bounding box size.

Extraction requires [`osmium-tool`](https://osmcode.org/osmium-tool/) to be available (via the PATH environement variable). If you manage your project with `conda` or `pixi`, the easiest way is to install it from conda-forge (i.e. `pixi add osmium-tool`).

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

The PBF file should cover only the region of interest. Everything contained in the file is rendered into the SVG, so a smaller file produces a smaller SVG and faster rendering times. It is recommended to pass the bounding box explicitly to `create_map` (or `SvgMapper`), even if the PBF file is already cropped to the region of interest, because some features (such as long roads) can extend beyond the selected region. Specifying the bounding box ensures the SVG is sized correctly and clips to the region of interest.

You can obtain a bounding box for a named place using `get_bbox_from_place`:

```python
from osm_to_svg import get_bbox_from_place

bbox = get_bbox_from_place("Hannover, Germany", width_km=7.5, height_km=7.5)
# returns (min_lon, min_lat, max_lon, max_lat)
```

See [examples/example_1_geocode_bbox.py](examples/example_1_geocode_bbox.py) for details.

## Basic usage

`create_map` is the recommended utility for one-shot rendering. It wraps `SvgMapper` internally and renders one or more layers into a final SVG.

```python
from osm_to_svg import Style, create_map, features

bbox = (9.68, 52.34, 9.79, 52.41)

create_map(
    pbf_path="hannover.osm.pbf",
    bounds=bbox,
    feature_layers=[
        (features.ROADS.MAJOR, Style(stroke="#000000", stroke_width=2.0)),
    ],
    output_path="roads.svg",
)
```

See [examples/example_3_basic_usage.py](examples/example_3_basic_usage.py) for the full script.

## Multiple layers

Multiple feature layers can be rendered and combined into a single SVG. All feature types are accessed through the `features` module as `features.ROADS`, `features.RAILWAYS`, `features.WATER`, `features.BUILDINGS`, and `features.GREEN_SPACES`. Specs can be combined with `|` to render multiple feature types in a single call.

```python
from osm_to_svg import Style, create_map, features

bbox = (9.68, 52.34, 9.79, 52.41)

create_map(
    pbf_path="hannover.osm.pbf",
    bounds=bbox,
    feature_layers=[
        (features.WATER.BODIES, Style(fill="#4A90E2")),
        (features.GREEN_SPACES.FORESTS, Style(fill="#046A04")),
        (features.ROADS.MAJOR, Style(stroke="#000000", stroke_width=2.0)),
    ],
    output_path="map.svg",
)
```

See [examples/example_4_multiple_layers.py](examples/example_4_multiple_layers.py) for the full script including POI markers.

## create_map options

`create_map` accepts the same map-configuration arguments as `SvgMapper`, plus layer lists and an output path:

- `pbf_path` — path to the `.osm.pbf` file to read.
- `scale` — map scale denominator (default: `100000` for 1:100,000). At this scale, 1 km in reality equals 1 cm in the output. The scale is accurate at the centre latitude of the map bounds.
- `dpi` — dots per inch for the output SVG (default: `96`). Common values: `96` (screen), `72` (print), `300` (high-res print).
- `bounds` — optional bounding box as `(min_lon, min_lat, max_lon, max_lat)`. If omitted, bounds are derived from the PBF file by scanning all nodes.
- `background_color` — optional background fill for the SVG (e.g. `"#FFFFFF"`, `"white"`). Defaults to `None` (transparent).
- `feature_layers` — list of `(FeatureSpec, Style)` tuples.
- `poi_layers` — list of `([(lat, lon), ...], PoiStyle)` tuples.
- `output_path` — path for the final combined SVG file.

```python
from osm_to_svg import Style, create_map, features

create_map(
    pbf_path="hannover.osm.pbf",
    scale=75000,
    dpi=300,
    bounds=(9.68, 52.34, 9.79, 52.41),
    background_color="#F5F5F5",
    feature_layers=[
        (features.ROADS.MAJOR, Style(stroke="#000000")),
    ],
    output_path="map.svg",
)
```

For advanced workflows, `SvgMapper` is still available as a context manager API.

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

POI marker layers are passed through `poi_layers` as `(coords, PoiStyle)` tuples. The output layer has the same dimensions as feature layers, so it can be combined directly.

```python
from osm_to_svg import PoiStyle, create_map

create_map(
    pbf_path="hannover.osm.pbf",
    poi_layers=[
        (
            [(52.3731, 9.7372), (52.3665, 9.7353)],  # (lat, lon)
            PoiStyle(
                marker_svg_path="pin.svg",
                scale=1.5,          # relative to the marker's original size
                anchor="bottom",   # which point aligns to the coordinate
            ),
        )
    ],
    output_path="pois.svg",
)
```

**Sizing** — exactly one of the following must be provided:

- `scale` — scale factor relative to the marker's original size (`1.0` = original, `2.0` = double).
- `width_meters` — desired marker width in metres on the map.
- `height_meters` — desired marker height in metres on the map.

**Anchor** — the `anchor` parameter controls which point of the icon is pinned to the coordinate. Accepted values: `"center"` (default), `"top"`, `"top-right"`, `"right"`, `"bottom-right"`, `"bottom"`, `"bottom-left"`, `"left"`, `"top-left"`.

```python
from osm_to_svg import PoiStyle, Style, create_map, features

# Absolute sizing — marker is always 200 m wide regardless of scale
poi_style = PoiStyle(marker_svg_path="pin.svg", width_meters=200.0)

# Combine with feature layers
create_map(
    pbf_path="hannover.osm.pbf",
    bounds=bbox,
    feature_layers=[
        (features.ROADS.MAJOR, Style(stroke="#000000")),
    ],
    poi_layers=[
        ([(52.3731, 9.7372)], poi_style),
    ],
    output_path="map.svg",
)
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

All features are accessed through the `features` module. Individual types match a single OSM tag value. Shorthands are pre-built `|` unions of individual types. Any spec can be further combined with `|`:

```python
from osm_to_svg import Style, create_map, features

style = Style(stroke="#000000")

# Individual type
create_map(
    pbf_path="hannover.osm.pbf",
    feature_layers=[(features.ROADS.MOTORWAY, style)],
    output_path="motorway.svg",
)

# Shorthand
create_map(
    pbf_path="hannover.osm.pbf",
    feature_layers=[(features.ROADS.MAJOR, style)],
    output_path="major_roads.svg",
)

# Ad-hoc combination
create_map(
    pbf_path="hannover.osm.pbf",
    feature_layers=[(features.ROADS.MAJOR | features.WATER.BODIES, style)],
    output_path="roads_and_water.svg",
)
```

### ROADS

OSM tag: `highway`

| Member | OSM value | Description |
|---|---|---|
| `features.ROADS.MOTORWAY` | `highway=motorway` | High-capacity divided motorway |
| `features.ROADS.MOTORWAY_LINK` | `highway=motorway_link` | Motorway ramp |
| `features.ROADS.TRUNK` | `highway=trunk` | High-importance road below motorway standard |
| `features.ROADS.TRUNK_LINK` | `highway=trunk_link` | Trunk road ramp |
| `features.ROADS.PRIMARY` | `highway=primary` | Major road linking large towns |
| `features.ROADS.PRIMARY_LINK` | `highway=primary_link` | Primary road slip road |
| `features.ROADS.SECONDARY` | `highway=secondary` | Road linking towns and villages |
| `features.ROADS.SECONDARY_LINK` | `highway=secondary_link` | Secondary road slip road |
| `features.ROADS.TERTIARY` | `highway=tertiary` | Road linking smaller settlements |
| `features.ROADS.TERTIARY_LINK` | `highway=tertiary_link` | Tertiary road slip road |
| `features.ROADS.RESIDENTIAL` | `highway=residential` | Road in a residential area |
| `features.ROADS.UNCLASSIFIED` | `highway=unclassified` | Minor road; lowest public road class |
| `features.ROADS.SERVICE` | `highway=service` | Access road for parking, driveways |
| `features.ROADS.LIVING_STREET` | `highway=living_street` | Pedestrian-priority street |
| `features.ROADS.CYCLEWAY` | `highway=cycleway` | Dedicated cycling path |
| `features.ROADS.FOOTWAY` | `highway=footway` | Designated footpath |
| `features.ROADS.PATH` | `highway=path` | Unpaved multi-use trail |
| `features.ROADS.PEDESTRIAN_TYPE` | `highway=pedestrian` | Pedestrianised street (single value; see `PEDESTRIAN` shorthand) |
| `features.ROADS.STEPS` | `highway=steps` | Stairway connection |
| `features.ROADS.TRACK` | `highway=track` | Agricultural or forestry track |
| `features.ROADS.ROAD` | `highway=road` | Road of unknown classification |

Shorthands:

| Shorthand | Composition |
|---|---|
| `features.ROADS.MAJOR` | `MOTORWAY` \| `MOTORWAY_LINK` \| `TRUNK` \| `TRUNK_LINK` \| `PRIMARY` \| `PRIMARY_LINK` \| `SECONDARY` \| `SECONDARY_LINK` \| `TERTIARY` \| `TERTIARY_LINK` |
| `features.ROADS.ARTERIAL` | `MOTORWAY` \| `MOTORWAY_LINK` \| `TRUNK` \| `TRUNK_LINK` \| `PRIMARY` \| `PRIMARY_LINK` |
| `features.ROADS.LOCAL` | `RESIDENTIAL` \| `UNCLASSIFIED` \| `SERVICE` \| `LIVING_STREET` |
| `features.ROADS.PEDESTRIAN` | `FOOTWAY` \| `PATH` \| `PEDESTRIAN_TYPE` \| `STEPS` |

### RAILWAYS

OSM tag: `railway`

| Member | OSM value | Description |
|---|---|---|
| `features.RAILWAYS.RAIL` | `railway=rail` | Standard-gauge heavy rail |
| `features.RAILWAYS.LIGHT_RAIL` | `railway=light_rail` | Light rail and commuter rail |
| `features.RAILWAYS.SUBWAY` | `railway=subway` | Underground metro |
| `features.RAILWAYS.TRAM` | `railway=tram` | Street-running tram |
| `features.RAILWAYS.MONORAIL` | `railway=monorail` | Single-rail guided transit |
| `features.RAILWAYS.FUNICULAR` | `railway=funicular` | Cable-driven hillside railway |
| `features.RAILWAYS.NARROW_GAUGE` | `railway=narrow_gauge` | Narrow-gauge railway |
| `features.RAILWAYS.ABANDONED` | `railway=abandoned` | Abandoned line |
| `features.RAILWAYS.DISUSED` | `railway=disused` | Disused but intact line |
| `features.RAILWAYS.PRESERVED` | `railway=preserved` | Heritage or museum railway |

Shorthands:

| Shorthand | Composition |
|---|---|
| `features.RAILWAYS.ACTIVE` | `RAIL` \| `LIGHT_RAIL` \| `SUBWAY` \| `TRAM` \| `MONORAIL` \| `FUNICULAR` \| `NARROW_GAUGE` |
| `features.RAILWAYS.URBAN_TRANSIT` | `LIGHT_RAIL` \| `SUBWAY` \| `TRAM` \| `MONORAIL` |
| `features.RAILWAYS.INACTIVE` | `ABANDONED` \| `DISUSED` \| `PRESERVED` |

### WATER

OSM tags: `waterway`, `natural`

| Member | OSM value | Description |
|---|---|---|
| `features.WATER.RIVER` | `waterway=river` | Major natural watercourse (line) |
| `features.WATER.STREAM` | `waterway=stream` | Minor watercourse (line) |
| `features.WATER.CANAL` | `waterway=canal` | Artificial navigable waterway (line) |
| `features.WATER.DRAIN` | `waterway=drain` | Drainage channel (line) |
| `features.WATER.DITCH` | `waterway=ditch` | Small drainage ditch (line) |
| `features.WATER.WATER_AREA` | `natural=water` | Generic water area polygon |
| `features.WATER.LAKE` | `natural=water` | Lake (same spec as `WATER_AREA`; OSM `water=lake` sub-type not filterable) |
| `features.WATER.RESERVOIR` | `natural=water` | Reservoir (same spec as `WATER_AREA`) |
| `features.WATER.POND` | `natural=water` | Pond (same spec as `WATER_AREA`) |
| `features.WATER.COASTLINE` | `natural=coastline` | Ocean/sea coastline area |

Shorthands:

| Shorthand | Composition |
|---|---|
| `features.WATER.LINEAR` | `RIVER` \| `STREAM` \| `CANAL` \| `DRAIN` \| `DITCH` |
| `features.WATER.BODIES` | `WATER_AREA` |
| `features.WATER.NATURAL` | `RIVER` \| `STREAM` \| `WATER_AREA` |
| `features.WATER.ARTIFICIAL` | `CANAL` \| `DRAIN` \| `DITCH` \| `WATER_AREA` |
| `features.WATER.MAJOR` | `RIVER` \| `CANAL` |

### BUILDINGS

OSM tag: `building`

| Member | OSM value | Description |
|---|---|---|
| `features.BUILDINGS.YES` | `building=yes` | Generic unclassified building |
| `features.BUILDINGS.BUILDING` | `building=building` | Explicitly tagged building |
| `features.BUILDINGS.HOUSE` | `building=house` | Single-family house |
| `features.BUILDINGS.DETACHED` | `building=detached` | Detached house |
| `features.BUILDINGS.SEMIDETACHED_HOUSE` | `building=semidetached_house` | Semi-detached house |
| `features.BUILDINGS.APARTMENTS` | `building=apartments` | Apartment building |
| `features.BUILDINGS.TERRACE` | `building=terrace` | Terraced houses |
| `features.BUILDINGS.BUNGALOW` | `building=bungalow` | Single-storey house |
| `features.BUILDINGS.RESIDENTIAL_TYPE` | `building=residential` | Generic residential (single value; see `RESIDENTIAL` shorthand) |
| `features.BUILDINGS.RETAIL` | `building=retail` | Retail building |
| `features.BUILDINGS.OFFICE` | `building=office` | Office building |
| `features.BUILDINGS.SUPERMARKET` | `building=supermarket` | Supermarket |
| `features.BUILDINGS.HOTEL` | `building=hotel` | Hotel |
| `features.BUILDINGS.COMMERCIAL_TYPE` | `building=commercial` | Generic commercial (single value; see `COMMERCIAL` shorthand) |
| `features.BUILDINGS.WAREHOUSE` | `building=warehouse` | Warehouse |
| `features.BUILDINGS.MANUFACTURE` | `building=manufacture` | Factory or manufacturing building |
| `features.BUILDINGS.INDUSTRIAL_TYPE` | `building=industrial` | Generic industrial (single value; see `INDUSTRIAL` shorthand) |
| `features.BUILDINGS.HOSPITAL` | `building=hospital` | Hospital |
| `features.BUILDINGS.SCHOOL` | `building=school` | School |
| `features.BUILDINGS.UNIVERSITY` | `building=university` | University building |
| `features.BUILDINGS.CHURCH` | `building=church` | Church |
| `features.BUILDINGS.CATHEDRAL` | `building=cathedral` | Cathedral |
| `features.BUILDINGS.MOSQUE` | `building=mosque` | Mosque |
| `features.BUILDINGS.TEMPLE` | `building=temple` | Temple |
| `features.BUILDINGS.SYNAGOGUE` | `building=synagogue` | Synagogue |
| `features.BUILDINGS.GOVERNMENT` | `building=government` | Government building |
| `features.BUILDINGS.CIVIC` | `building=civic` | Civic building |
| `features.BUILDINGS.PUBLIC` | `building=public` | Generic public building |
| `features.BUILDINGS.GARAGE` | `building=garage` | Private garage |
| `features.BUILDINGS.GARAGES` | `building=garages` | Block of garages |
| `features.BUILDINGS.PARKING` | `building=parking` | Parking structure |
| `features.BUILDINGS.SHED` | `building=shed` | Shed or outbuilding |
| `features.BUILDINGS.ROOF` | `building=roof` | Roof structure |
| `features.BUILDINGS.CONSTRUCTION` | `building=construction` | Building under construction |

Shorthands:

| Shorthand | Composition |
|---|---|
| `features.BUILDINGS.RESIDENTIAL` | `RESIDENTIAL_TYPE` \| `HOUSE` \| `DETACHED` \| `SEMIDETACHED_HOUSE` \| `APARTMENTS` \| `TERRACE` \| `BUNGALOW` |
| `features.BUILDINGS.COMMERCIAL` | `COMMERCIAL_TYPE` \| `RETAIL` \| `OFFICE` \| `SUPERMARKET` \| `HOTEL` |
| `features.BUILDINGS.INDUSTRIAL` | `INDUSTRIAL_TYPE` \| `WAREHOUSE` \| `MANUFACTURE` |
| `features.BUILDINGS.RELIGIOUS` | `CHURCH` \| `CATHEDRAL` \| `MOSQUE` \| `TEMPLE` \| `SYNAGOGUE` |
| `features.BUILDINGS.INSTITUTIONAL` | `HOSPITAL` \| `SCHOOL` \| `UNIVERSITY` \| `GOVERNMENT` \| `CIVIC` \| `PUBLIC` |
| `features.BUILDINGS.SINGLE_FAMILY` | `HOUSE` \| `DETACHED` \| `SEMIDETACHED_HOUSE` \| `BUNGALOW` |
| `features.BUILDINGS.MULTI_FAMILY` | `APARTMENTS` \| `TERRACE` |

### GREEN_SPACES

OSM tags: `leisure`, `natural`, `landuse`

| Member | OSM tag | Description |
|---|---|---|
| `features.GREEN_SPACES.PARK` | `leisure=park` | Public park |
| `features.GREEN_SPACES.GARDEN` | `leisure=garden` | Public or private garden |
| `features.GREEN_SPACES.NATURE_RESERVE` | `leisure=nature_reserve` | Protected nature reserve |
| `features.GREEN_SPACES.RECREATION_GROUND` | `leisure=recreation_ground` | Recreation area |
| `features.GREEN_SPACES.COMMON` | `leisure=common` | Public common land |
| `features.GREEN_SPACES.GOLF_COURSE` | `leisure=golf_course` | Golf course |
| `features.GREEN_SPACES.WOOD` | `natural=wood` | Natural woodland |
| `features.GREEN_SPACES.SCRUB` | `natural=scrub` | Scrubland |
| `features.GREEN_SPACES.GRASSLAND` | `natural=grassland` | Natural grassland |
| `features.GREEN_SPACES.HEATH` | `natural=heath` | Heath or moorland |
| `features.GREEN_SPACES.WETLAND` | `natural=wetland` | Wetland or marsh |
| `features.GREEN_SPACES.FOREST` | `landuse=forest` | Managed forest |
| `features.GREEN_SPACES.MEADOW` | `landuse=meadow` | Meadow |
| `features.GREEN_SPACES.GRASS` | `landuse=grass` | Managed grass area |
| `features.GREEN_SPACES.ORCHARD` | `landuse=orchard` | Orchard |
| `features.GREEN_SPACES.VINEYARD` | `landuse=vineyard` | Vineyard |
| `features.GREEN_SPACES.CEMETERY` | `landuse=cemetery` | Cemetery |
| `features.GREEN_SPACES.ALLOTMENTS` | `landuse=allotments` | Allotment garden |

Shorthands:

| Shorthand | Composition |
|---|---|
| `features.GREEN_SPACES.PARKS` | `PARK` \| `GARDEN` \| `RECREATION_GROUND` \| `COMMON` |
| `features.GREEN_SPACES.FORESTS` | `WOOD` \| `FOREST` |
| `features.GREEN_SPACES.NATURAL` | `WOOD` \| `SCRUB` \| `GRASSLAND` \| `HEATH` \| `WETLAND` |
| `features.GREEN_SPACES.PROTECTED` | `NATURE_RESERVE` \| `WETLAND` |
| `features.GREEN_SPACES.AGRICULTURAL` | `MEADOW` \| `GRASS` \| `ORCHARD` \| `VINEYARD` \| `ALLOTMENTS` |
| `features.GREEN_SPACES.ALL` | `PARK` \| `GARDEN` \| `NATURE_RESERVE` \| `RECREATION_GROUND` \| `COMMON` \| `GOLF_COURSE` \| `WOOD` \| `SCRUB` \| `GRASSLAND` \| `HEATH` \| `WETLAND` \| `FOREST` \| `MEADOW` \| `GRASS` \| `ORCHARD` \| `VINEYARD` \| `CEMETERY` \| `ALLOTMENTS` |

