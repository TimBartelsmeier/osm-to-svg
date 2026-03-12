# osm-to-svg

A Python library for generating SVG maps from OpenStreetMap data. It allows creating SVG files that contain styled layers for roads, waterways, bodies of water, railways, buildings and green spaces; and allows placing POI markers. 

TODO: advanced styling, arbitrary combinations, scaling, etc.

> [!WARNING]
> This project was programmed entirely with AI tools (Github Copilot with Claude Sonnet 4.5 & 4.6 and GPT-5.3.-Codex). This was partly because I needed such a tool for a private project but didn't have the time to implement it myself, and partly because I wanted to try out for myself how well “vibecoding” works.
I have tested the functionality and, at least for my application, everything works as expected and without unintended side-effects. However, I have only given a cursory inspection to the generated code itself and I accept no liability for it.

## Installation

This library is currently not published to PyPI, conda-forge, or similar. You can install it directly from this repo with your favorite package manager that supports installing from git (for example, `pip` or `pixi`). I recommend [`pixi`](https://pixi.prefix.dev/latest/) because it allows managing packages and tools from pypi, conda repos like conda-forge, and from git (like this package) simultaneously.

With `pixi`, you'd do something like this:
1. [Install pixi on you system](https://pixi.prefix.dev/latest/installation)
2. Create a new directory for your project.
3. Open a terminal in the directory and run `pixi init`
4. Run `pixi add python`
5. Run `pixi add --pypi "osm-to-svg @ git+https://github.com/TimBartelsmeier/osm-to-svg"` to install this repository.
6. Done! You can now use this package in python by importing `osm_to_svg`. Note that with pixi, you need to run `pixi run python <file/arguments>` instead of `python <file/arguments>`.
7. You probably also want to install `osmium-tool` - see below for details.

If you need to update this package, just run step 5 again. This will download the latest version from Github.

### Additional helpful packages
To extract a region of interest from a larger `.osm.pbf` file, [`osmium-tool`](https://osmcode.org/osmium-tool/) has to be available via the PATH environment variable. You can install it globally if you like, but if you manage your project with `conda` or `pixi`, the easiest way is to install it to your project from conda-forge (i.e. `pixi add osmium-tool`).

To play around with the styling options and see the results immediately without switching files, I recommend working in a Jupyter notebook (`pixi add jupyter`).

## Usage

### Coordinate conventions
This library uses the following conventions for coordinates:
- **Individual coordinates**: `(latitude, longitude)` — lat first.
- **Bounding boxes**: `(south_lat, west_lon, north_lat, east_lon)` — lat/lon pairs for the SW and NE corners.

> [!NOTE]
> Most of the code examples shown in this README are also included in the [example scripts](./examples/).

### Obtaining OSM data
To create maps, you need an `osm.pbf` file that contains the OSM data from your region of interest (ROI). The file _can_ include a larger region than what you are interested in, but this will result in longer processing times and larger files because the entire region contained in the PBF file is rendered into the SVG - if you later pass a bounding box to `create_map`, the SVG is simply cropped to that region. Therefore, you should make sure that the PBF file you use for plotting only contains the region you actually want to plot.

The most reliable way to obtain an `osm.pbf` file of your ROI is to download a pre-built file from an online hoster. For example, [Geofabrik](https://download.geofabrik.de/) offers files that contain entire continents, countries, or subdivisions of countries. (To reduce the processing time, you should select the smallest division you can find that still encompasses your entire ROI.) You can then use this libraries `extract_from_pbf` method to extract a PBF file containing only your ROI.

```python
from osm_to_svg import download_from_url, extract_from_pbf

download_from_url(
    url="https://download.geofabrik.de/europe/germany/niedersachsen-latest.osm.pbf",
    output_path="niedersachsen.osm.pbf",
)

extract_from_pbf(
    source_pbf_path="niedersachsen.osm.pbf",
    bbox=(52.34, 9.68, 52.41, 9.79),  # (south_lat, west_lon, north_lat, east_lon)
    output_path="hannover.osm.pbf",
)
```

As detailed [above](#additional-helpful-packages), extraction requires `osmium-tool`.

#### Geocoding & bounding arodund coordinates
Instead of looking the coordinates up yourself, you can use `geocode_place` to query [OSM's Nominatim search engine](https://nominatim.openstreetmap.org/) for a place's coordinates, and then use `get_bbox_around_coordinates` to compute a bounding box of the desired size around them.

```python
from osm_to_svg import geocode_place, get_bbox_around_coordinates

# Step 1 – resolve the place name to coordinates
lat, lon = geocode_place("Hannover, Germany")

# Step 2 – build a bounding box around those coordinates
bbox = get_bbox_around_coordinates(
    lat,
    lon,
    width_km=7.5,
    height_km=7.5,
)
# returns (south_lat, west_lon, north_lat, east_lon)

# You can now pass the bbox object to extract_from_pbf (described above) and/or to pass create_map (described below).
```

`get_bbox_around_coordinates` also accepts asymmetric extents: you can specify ``east_km`` and ``west_km`` instead of ``width_km``, and/or  ``north_km`` and ``south_km`` instead of ``height_km`` (see the function's docstring for the full parameter reference).

#### Alternative approach: Overpass API

Data can also be downloaded directly from the Overpass API. Note that this is often overloaded, may time out, applies rate limiting, and only supports small bounding boxes.

```python
from osm_to_svg import download_from_overpass

download_from_overpass(
    bbox=(52.372, 9.735, 52.378, 9.745),
    output_path="area.osm.pbf"
)
```

### Creating maps
The `create_map` method is used to create SVG images from the cartographic data.


Options:
- `pbf_path` — path to the `.osm.pbf` file to read.
- `scale` — map scale denominator (default: `100000` for scale 1:100,000, i.e. 1 km in reality equals 1 cm in the output SVG). The scale is accurate at the centre latitude of the map bounds.
- `dpi` — dots per inch for the output SVG (default: `96`). Common values: `96` (screen), `72` (print), `300` (high-res print).
- `bounds` — optional bounding box as `(south_lat, west_lon, north_lat, east_lon)`. It is recommended to pass this even if your PBF file is already cropped to the region of interest because some features contained in the PBF file (such as long roads) can extend out of the PBF's region. Specifying the bounding box ensures the SVG is sized correctly and cropped to the region of interest. If omitted, bounds are derived from the PBF file by scanning all nodes.
- `background_color` — optional background fill for the SVG (e.g. `"#FFFFFF"`, `"white"`). Defaults to `None` (transparent).
- `feature_layers` — list of `(FeatureSpec, Style)` tuples. See below for details.
- `poi_layers` — list of `([(lat, lon), ...], PoiStyle)` tuples. See below for details.
- `output_path` — path for the final combined SVG file.
- `show_progress` — if `True`, displays two progress bars via `tqdm`: an outer bar showing the current layer (e.g. `Layer 1/3 [highway]`), and an inner bar showing per-layer progress. The inner bar is indeterminate while the PBF file is being parsed (which is most likely the majority of the processing time per layer), then switches to a determinate feature count during SVG rendering. Defaults to `False`.

#### Specifiying features (roads, forests, ...)
`feature_layers` is a list of `(FeatureSpec, Style)` tuples. Each entry results in one layer in the SVG file, with one or more OSM features output in the same style. The available features (and how to combine them) are described [below](#available-features).

Feature layers are styled with the `Style` class. All attributes are optional and default to no stroke and no fill (i.e. invisible). Options:
- `stroke` — stroke colour as a CSS colour string (e.g. `"#000000"`, `"red"`). Use `"none"` for no stroke (default: `"none"`).
- `stroke_width` — stroke width in points (1 pt = 1/72 inch) (default: `1.0`).
- `fill` — fill colour. Use `"none"` for no fill (default: `"none"`).
- `opacity` — overall opacity, `0.0`–`1.0` (default: `1.0`).
- `stroke_opacity` — stroke-only opacity, `0.0`–`1.0` (default: `None` = inherits `opacity`).
- `fill_opacity` — fill-only opacity, `0.0`–`1.0` (default: `None` = inherits `opacity`).

#### Adding point of interests (POIs)
`poi_layers` is a list of `([(lat, lon), ...], PoiStyle)` tuples. Each entry places the same marker SVG at every coordinate in the list using the given `PoiStyle`.

Coordinates must be provided as `(latitude, longitude)` pairs.

POI markers are styled with the `PoiStyle` class. Required:
- `marker_svg_path` — path to the SVG file used as the marker icon.

Exactly one of the following sizing methods must also be provided (specifying zero or more than one raises a `ValueError`):
- `scale` — scale factor relative to the marker SVG's intrinsic dimensions (e.g. `1.0` = native size, `2.0` = double size).
- `width_meters` — sets the marker width to a fixed distance in metres on the map (e.g. `500` makes the marker 500 m wide at the map scale).
- `height_meters` — sets the marker height to a fixed distance in metres on the map.

Optional:
- `anchor` — which point of the marker SVG is aligned to the POI coordinate. Accepted values: `"center"` (default), `"top"`, `"top-right"`, `"right"`, `"bottom-right"`, `"bottom"`, `"bottom-left"`, `"left"`, `"top-left"`. Use `"bottom"` for a classic pin-style marker where the tip points to the location.

#### Full example
See [examples/example_4_multiple_layers.py](examples/example_4_multiple_layers.py) for an example script that includes multiple layers and POI markers.

## Available features
All features are accessed through the `features` subpackage. Individual types match one or more OSM tag constraints, for example, `osm_to_svg.features.ROADS.MOTORWAY`, `osm_to_svg.features.WATERWAYS.CANAL`, or `osm_to_svg.features.WATER_POLYGONS.LAKE`. Multiple features can be combined with the `|` operator: `features.ROADS.MOTORWAY | features.WATERWAYS.CANAL` will create a new `FeatureSpec` object that, when passed to `create_map`, will result in motorways _and_ canal centerlines being plotted. There are also a lot of pre-defined unions ("shorthands") for typical use cases, for example, `features.ROADS.MAJOR` encompasses all major link roads, but no residential roads.

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
    feature_layers=[(features.ROADS.MAJOR | features.WATER_POLYGONS.OPEN_WATER, style)],
    output_path="roads_and_water.svg",
)
```

Note: OSM is very granular in separating different types of features. For example, motorways (`features.ROADS.MOTORWAYS`) are tagged differently than the ramps leading to them (`features.ROADS.MOTORWAY_LINK`). This can be a curse and a blessing: it gives you very granular control over your maps, but if you have unexpected "gaps" in your map, you probabaly need to research what additional tags you need to include in your query. The shorthand groups included in this library are intended to provide a good starting point for common applications.

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
| `features.ROADS.PEDESTRIAN_TYPE` | `highway=pedestrian` | Pedestrianised street or plaza (specific OSM tag value; see PEDESTRIAN for a shorthand group that also encompasses other features that would commonly be counted as pedestrian paths) |
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

### WATERWAYS

OSM tag: `waterway`

`features.WATERWAYS` is for linear centerlines that should normally be stroked, not filled. Use this namespace for river and canal lines. Rivers and canals intentionally overlap with `features.WATER_POLYGONS` because some OSM data also represents them as area geometries.

| Member | OSM value | Description |
|---|---|---|
| `features.WATERWAYS.RIVER` | `waterway=river` | Major natural watercourse centerline |
| `features.WATERWAYS.STREAM` | `waterway=stream` | Minor natural watercourse centerline |
| `features.WATERWAYS.CANAL` | `waterway=canal` | Artificial navigable waterway centerline |
| `features.WATERWAYS.DRAIN` | `waterway=drain` | Drainage channel centerline |
| `features.WATERWAYS.DITCH` | `waterway=ditch` | Small drainage ditch centerline |

Shorthands:

| Shorthand | Composition |
|---|---|
| `features.WATERWAYS.ALL` | `RIVER` \| `STREAM` \| `CANAL` \| `DRAIN` \| `DITCH` |
| `features.WATERWAYS.FLOWING` | `RIVER` \| `STREAM` \| `CANAL` |
| `features.WATERWAYS.NATURAL` | `RIVER` \| `STREAM` |
| `features.WATERWAYS.ARTIFICIAL` | `CANAL` \| `DRAIN` \| `DITCH` |
| `features.WATERWAYS.DRAINAGE` | `DRAIN` \| `DITCH` |
| `features.WATERWAYS.MAJOR` | `RIVER` \| `CANAL` |

### WATER_POLYGONS

OSM tags: `natural`, `water`, `wetland`, `landuse`, `waterway`

`features.WATER_POLYGONS` is for fill-safe area features. Use it for lakes, riverbanks, canal basins, wetlands, and similar polygonal water features. Some members overlap intentionally with `features.WATERWAYS`: `RIVER` and `CANAL` target filled area geometries here, while the same names under `features.WATERWAYS` target centerlines.

| Member | OSM value | Description |
|---|---|---|
| `features.WATER_POLYGONS.WATER_AREA` | `natural=water` | Generic open-water polygon |
| `features.WATER_POLYGONS.LAKE` | `natural=water` + `water=lake` | Lake polygon |
| `features.WATER_POLYGONS.RESERVOIR` | `natural=water` + `water=reservoir` | Reservoir polygon |
| `features.WATER_POLYGONS.POND` | `natural=water` + `water=pond` | Pond polygon |
| `features.WATER_POLYGONS.LAGOON` | `natural=water` + `water=lagoon` | Lagoon polygon |
| `features.WATER_POLYGONS.BASIN` | `landuse=basin` or `natural=water` + `water=basin` | Basin polygon |
| `features.WATER_POLYGONS.SALT_POND` | `landuse=salt_pond` | Salt pond polygon |
| `features.WATER_POLYGONS.RIVER` | `waterway=riverbank` or `natural=water` + `water=river` | River area polygon; overlaps with `WATERWAYS.RIVER` |
| `features.WATER_POLYGONS.CANAL` | `natural=water` + `water=canal` | Canal area polygon; overlaps with `WATERWAYS.CANAL` |
| `features.WATER_POLYGONS.WETLAND_TYPE` | `natural=wetland` | Generic wetland polygon; also matches `GREEN_SPACES.WETLAND` (specific OSM tag value; see WETLANDS for a shorthand group that also encompasses other wetland subtypes such as marsh, swamp, reedbed, and saltmarsh) |
| `features.WATER_POLYGONS.MARSH` | `natural=wetland` + `wetland=marsh` | Marsh polygon |
| `features.WATER_POLYGONS.SWAMP` | `natural=wetland` + `wetland=swamp` | Swamp polygon |
| `features.WATER_POLYGONS.REEDBED` | `natural=wetland` + `wetland=reedbed` | Reedbed polygon |
| `features.WATER_POLYGONS.SALTMARSH` | `natural=wetland` + `wetland=saltmarsh` | Saltmarsh polygon |
| `features.WATER_POLYGONS.COASTLINE` | `natural=coastline` | Coastline or sea-edge polygon |

Shorthands:

| Shorthand | Composition |
|---|---|
| `features.WATER_POLYGONS.OPEN_WATER` | `WATER_AREA` \| `LAKE` \| `RESERVOIR` \| `POND` \| `LAGOON` \| `BASIN` \| `SALT_POND` |
| `features.WATER_POLYGONS.FLOWING` | `RIVER` \| `CANAL` |
| `features.WATER_POLYGONS.WETLANDS` | `WETLAND_TYPE` \| `MARSH` \| `SWAMP` \| `REEDBED` \| `SALTMARSH` |
| `features.WATER_POLYGONS.MAJOR` | `LAKE` \| `RESERVOIR` \| `RIVER` \| `CANAL` |
| `features.WATER_POLYGONS.NATURAL` | `WATER_AREA` \| `LAKE` \| `POND` \| `LAGOON` \| `RIVER` \| `WETLANDS` |
| `features.WATER_POLYGONS.ARTIFICIAL` | `RESERVOIR` \| `CANAL` \| `BASIN` \| `SALT_POND` |
| `features.WATER_POLYGONS.INLAND` | `OPEN_WATER` \| `FLOWING` \| `WETLANDS` |
| `features.WATER_POLYGONS.MAJOR_INLAND` | `LAKE` \| `RESERVOIR` \| `RIVER` \| `CANAL` |
| `features.WATER_POLYGONS.ALL` | `INLAND` \| `COASTLINE` |

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
| `features.BUILDINGS.RESIDENTIAL_TYPE` | `building=residential` | Generic residential building (specific OSM tag value; see RESIDENTIAL for a shorthand group that also encompasses other residential building types such as houses, detached buildings, apartments, terraces, and bungalows) |
| `features.BUILDINGS.RETAIL` | `building=retail` | Retail building |
| `features.BUILDINGS.OFFICE` | `building=office` | Office building |
| `features.BUILDINGS.SUPERMARKET` | `building=supermarket` | Supermarket |
| `features.BUILDINGS.HOTEL` | `building=hotel` | Hotel |
| `features.BUILDINGS.COMMERCIAL_TYPE` | `building=commercial` | Generic commercial building (specific OSM tag value; see COMMERCIAL for a shorthand group that also encompasses other building types used for commercial purposes such as retail, office, supermarket, and hotel buildings) |
| `features.BUILDINGS.WAREHOUSE` | `building=warehouse` | Warehouse |
| `features.BUILDINGS.MANUFACTURE` | `building=manufacture` | Factory or manufacturing building |
| `features.BUILDINGS.INDUSTRIAL_TYPE` | `building=industrial` | Generic industrial building (specific OSM tag value; see INDUSTRIAL for a shorthand group that also encompasses other building types used for industrial purposes such as warehouses and manufacturing facilities) |
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

