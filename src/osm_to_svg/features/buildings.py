"""Building feature catalog (OSM building=)."""

from osm_to_svg.features.spec import FeatureSpec


def _b(value: str) -> FeatureSpec:
    """Shorthand for a single building= filter."""
    return FeatureSpec({"building": [value]}, needs_areas=True)


class BUILDINGS:
    """Building features (OSM building= tag).

    All building specs use area processing (needs_areas=True) because buildings
    are represented as closed polygons in OSM.

    Note: RESIDENTIAL_TYPE, COMMERCIAL_TYPE, and INDUSTRIAL_TYPE refer to the
    single OSM tag values ``building=residential``, ``building=commercial``, and
    ``building=industrial`` respectively. The shorthand names RESIDENTIAL,
    COMMERCIAL, and INDUSTRIAL cover broader groups of related building subtypes.

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.BUILDINGS.RESIDENTIAL, style)
    """

    # ---- individual types ----
    YES = _b("yes")
    """building=yes: Unspecified building (generic building outline with no further classification)."""
    BUILDING = _b("building")
    """building=building: Explicitly tagged as building=building (rare OSM usage)."""
    HOUSE = _b("house")
    """building=house: Single-family detached house."""
    DETACHED = _b("detached")
    """building=detached: Fully detached residential building, standing alone on its plot."""
    SEMIDETACHED_HOUSE = _b("semidetached_house")
    """building=semidetached_house: Two residential units sharing one party wall."""
    APARTMENTS = _b("apartments")
    """building=apartments: Multi-unit apartment building."""
    TERRACE = _b("terrace")
    """building=terrace: Row of terraced houses sharing party walls."""
    BUNGALOW = _b("bungalow")
    """building=bungalow: Single-storey house."""
    RESIDENTIAL_TYPE = _b("residential")
    """building=residential: Generic residential building (single tag value; see RESIDENTIAL for the group shorthand)."""
    RETAIL = _b("retail")
    """building=retail: Building used for retail trade."""
    OFFICE = _b("office")
    """building=office: Office building."""
    SUPERMARKET = _b("supermarket")
    """building=supermarket: Supermarket building."""
    HOTEL = _b("hotel")
    """building=hotel: Hotel building."""
    COMMERCIAL_TYPE = _b("commercial")
    """building=commercial: Generic commercial building (single tag value; see COMMERCIAL for the group shorthand)."""
    WAREHOUSE = _b("warehouse")
    """building=warehouse: Large storage building."""
    MANUFACTURE = _b("manufacture")
    """building=manufacture: Manufacturing or factory building."""
    INDUSTRIAL_TYPE = _b("industrial")
    """building=industrial: Generic industrial building (single tag value; see INDUSTRIAL for the group shorthand)."""
    HOSPITAL = _b("hospital")
    """building=hospital: Hospital or medical facility building."""
    SCHOOL = _b("school")
    """building=school: School building."""
    UNIVERSITY = _b("university")
    """building=university: University building."""
    CHURCH = _b("church")
    """building=church: Christian church building."""
    CATHEDRAL = _b("cathedral")
    """building=cathedral: Cathedral building."""
    MOSQUE = _b("mosque")
    """building=mosque: Mosque building."""
    TEMPLE = _b("temple")
    """building=temple: Temple building."""
    SYNAGOGUE = _b("synagogue")
    """building=synagogue: Synagogue building."""
    GOVERNMENT = _b("government")
    """building=government: Government or public administration building."""
    CIVIC = _b("civic")
    """building=civic: Civic building for public services."""
    PUBLIC = _b("public")
    """building=public: Generic public-use building."""
    GARAGE = _b("garage")
    """building=garage: Single private garage."""
    GARAGES = _b("garages")
    """building=garages: Block of multiple private garages."""
    PARKING = _b("parking")
    """building=parking: Multi-storey or enclosed parking structure."""
    SHED = _b("shed")
    """building=shed: Small outbuilding or storage shed."""
    ROOF = _b("roof")
    """building=roof: Roof structure with no fully enclosed walls."""
    CONSTRUCTION = _b("construction")
    """building=construction: Building currently under construction."""

    # ---- shorthands ----
    RESIDENTIAL = (
        RESIDENTIAL_TYPE
        | HOUSE
        | DETACHED
        | SEMIDETACHED_HOUSE
        | APARTMENTS
        | TERRACE
        | BUNGALOW
    )
    """Shorthand for residential dwelling buildings across detached, attached, and multi-unit forms.

    OSM tags: building=residential, house, detached, semidetached_house,
    apartments, terrace, bungalow.

    See also RESIDENTIAL_TYPE for the single tag value.
    """
    COMMERCIAL = COMMERCIAL_TYPE | RETAIL | OFFICE | SUPERMARKET | HOTEL
    """Shorthand for commercial and business-use buildings.

    OSM tags: building=commercial, retail, office, supermarket, hotel.

    See also COMMERCIAL_TYPE for the single tag value.
    """
    INDUSTRIAL = INDUSTRIAL_TYPE | WAREHOUSE | MANUFACTURE
    """Shorthand for industrial production and storage buildings.

    OSM tags: building=industrial, warehouse, manufacture.

    See also INDUSTRIAL_TYPE for the single tag value.
    """
    RELIGIOUS = CHURCH | CATHEDRAL | MOSQUE | TEMPLE | SYNAGOGUE
    """Shorthand for places of worship and religious buildings.

    OSM tags: building=church, cathedral, mosque, temple, synagogue.
    """
    INSTITUTIONAL = HOSPITAL | SCHOOL | UNIVERSITY | GOVERNMENT | CIVIC | PUBLIC
    """Shorthand for civic, government, education, and healthcare institutions.

    OSM tags: building=hospital, school, university, government, civic, public.
    """
    SINGLE_FAMILY = HOUSE | DETACHED | SEMIDETACHED_HOUSE | BUNGALOW
    """Shorthand for single-household and low-density dwelling buildings.

    OSM tags: building=house, detached, semidetached_house, bungalow.
    """
    MULTI_FAMILY = APARTMENTS | TERRACE
    """Shorthand for multi-household residential buildings.

    OSM tags: building=apartments, terrace.
    """
    ALL = (
        RESIDENTIAL
        | COMMERCIAL
        | INDUSTRIAL
        | RELIGIOUS
        | INSTITUTIONAL
        | YES
        | BUILDING
        | GARAGE
        | GARAGES
        | PARKING
        | SHED
        | ROOF
        | CONSTRUCTION
    )
    """Shorthand for all building feature types covered by this module.

    OSM tags: building=yes, building, residential, house, detached,
    semidetached_house, apartments, terrace, bungalow, commercial, retail,
    office, supermarket, hotel, industrial, warehouse, manufacture, hospital,
    school, university, church, cathedral, mosque, temple, synagogue,
    government, civic, public, garage, garages, parking, shed, roof,
    construction.
    """
