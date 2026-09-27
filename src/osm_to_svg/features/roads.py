"""Road feature catalog (OSM highway=)."""

from osm_to_svg.features.spec import FeatureSpec


def _r(value: str) -> FeatureSpec:
    """Shorthand for a single highway= filter (roads)."""
    return FeatureSpec({"highway": [value]})


class ROADS:
    """Road features (OSM highway= tag).

    Individual types match a single highway= value.
    Shorthands group common subsets for cartographic use.
    CYCLEWAY is standalone and not included in MAJOR, LOCAL,
    or PEDESTRIAN shorthands; include it explicitly when needed.

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.ROADS.MAJOR, style)
        mapper.render_features(features.ROADS.MOTORWAY | features.ROADS.TRUNK, style)
    """

    # ---- individual types ----
    MOTORWAY = _r("motorway")
    """highway=motorway: High-capacity divided motorway; access via entry/exit ramps only."""
    MOTORWAY_LINK = _r("motorway_link")
    """highway=motorway_link: Ramp connecting to or from a motorway."""
    TRUNK = _r("trunk")
    """highway=trunk: High-importance road that does not meet full motorway standard."""
    TRUNK_LINK = _r("trunk_link")
    """highway=trunk_link: Ramp connecting to or from a trunk road."""
    PRIMARY = _r("primary")
    """highway=primary: Major road linking large towns."""
    PRIMARY_LINK = _r("primary_link")
    """highway=primary_link: Slip road connecting to a primary road."""
    SECONDARY = _r("secondary")
    """highway=secondary: Road linking towns and larger villages."""
    SECONDARY_LINK = _r("secondary_link")
    """highway=secondary_link: Slip road connecting to a secondary road."""
    TERTIARY = _r("tertiary")
    """highway=tertiary: Road linking smaller settlements."""
    TERTIARY_LINK = _r("tertiary_link")
    """highway=tertiary_link: Slip road connecting to a tertiary road."""
    RESIDENTIAL = _r("residential")
    """highway=residential: Road within a residential area."""
    UNCLASSIFIED = _r("unclassified")
    """highway=unclassified: Minor road connecting settlements; lowest public road class."""
    SERVICE = _r("service")
    """highway=service: Access road for parking lots, driveways, and service areas."""
    LIVING_STREET = _r("living_street")
    """highway=living_street: Pedestrian-priority street with very low speed limit."""
    CYCLEWAY = _r("cycleway")
    """highway=cycleway: Dedicated cycling path."""
    FOOTWAY = _r("footway")
    """highway=footway: Designated footpath for pedestrians."""
    PATH = _r("path")
    """highway=path: Unpaved trail shared by pedestrians, cyclists, or horses."""
    BRIDLEWAY = _r("bridleway")
    """highway=bridleway: Route designated primarily for horse riders."""
    PEDESTRIAN_TAG = _r("pedestrian")
    """highway=pedestrian: OSM tag value for pedestrianised streets and plazas."""
    STEPS = _r("steps")
    """highway=steps: Stairway connection between levels."""
    TRACK = _r("track")
    """highway=track: Unpaved track for agricultural or forestry access."""
    ROAD = _r("road")
    """highway=road: Road of unknown or unspecified classification."""
    BUS_GUIDEWAY = _r("bus_guideway")
    """highway=bus_guideway: Guided busway unsuitable for ordinary traffic."""
    BUSWAY = _r("busway")
    """highway=busway: Dedicated roadway for bus rapid transit."""
    RACEWAY = _r("raceway")
    """highway=raceway: Course or track for motor racing."""
    ESCAPE = _r("escape")
    """highway=escape: Runaway truck ramp or emergency escape lane."""
    CORRIDOR = _r("corridor")
    """highway=corridor: Indoor hallway mapped as a way."""
    VIA_FERRATA = _r("via_ferrata")
    """highway=via_ferrata: Equipped climbing route."""
    ELEVATOR = _r("elevator")
    """highway=elevator: Elevator or lift connecting pathway levels."""
    ESCALATOR = _r("escalator")
    """highway=escalator: Escalator connecting pathway levels."""
    CONSTRUCTION = _r("construction")
    """highway=construction: Highway under construction."""
    PROPOSED = _r("proposed")
    """highway=proposed: Planned highway not yet under construction."""

    # ---- shorthands ----
    MAJOR = (
        MOTORWAY
        | MOTORWAY_LINK
        | TRUNK
        | TRUNK_LINK
        | PRIMARY
        | PRIMARY_LINK
        | SECONDARY
        | SECONDARY_LINK
        | TERTIARY
        | TERTIARY_LINK
    )
    """Shorthand for arterial road network from motorway through tertiary, including link roads.

    OSM tags: highway=motorway, motorway_link, trunk, trunk_link, primary,
    primary_link, secondary, secondary_link, tertiary, tertiary_link.
    """
    ARTERIAL = MOTORWAY | MOTORWAY_LINK | TRUNK | TRUNK_LINK | PRIMARY | PRIMARY_LINK
    """Shorthand for highest-hierarchy roads: motorway, trunk, and primary classes with links.

    OSM tags: highway=motorway, motorway_link, trunk, trunk_link, primary,
    primary_link.
    """
    LOCAL = RESIDENTIAL | UNCLASSIFIED | SERVICE | LIVING_STREET
    """Shorthand for local access street network and traffic-calmed residential streets.

    OSM tags: highway=residential, unclassified, service, living_street.
    """
    PEDESTRIAN = FOOTWAY | PATH | BRIDLEWAY | PEDESTRIAN_TAG | STEPS
    """Shorthand for walkable and low-speed path networks.

    OSM tags: highway=footway, path, bridleway, pedestrian, steps.

    See also PEDESTRIAN_TAG for the single highway=pedestrian tag value.
    """
    ACTIVE_MOBILITY = CYCLEWAY | FOOTWAY | PATH | BRIDLEWAY | PEDESTRIAN_TAG | STEPS
    """Shorthand for active-mobility paths and non-motorized connectors.

    OSM tags: highway=cycleway, footway, path, bridleway, pedestrian, steps.
    """
    SPECIAL = BUS_GUIDEWAY | BUSWAY | RACEWAY | ESCAPE
    """Shorthand for special-purpose highway ways.

    OSM tags: highway=bus_guideway, busway, raceway, escape.
    """
    ALL = (
        MAJOR
        | LOCAL
        | ACTIVE_MOBILITY
        | TRACK
        | ROAD
        | SPECIAL
        | CORRIDOR
        | VIA_FERRATA
        | ELEVATOR
        | ESCALATOR
        | CONSTRUCTION
        | PROPOSED
    )
    """Shorthand for every renderable ``highway=*`` value in this catalog.

    Node-only highway features such as bus stops, crossings, and traffic
    signals are intentionally excluded because the parser extracts ways and
    areas, not standalone nodes.
    """
