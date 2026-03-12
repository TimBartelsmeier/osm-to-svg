"""Building feature catalog (OSM building=)."""

from osm_to_svg.features.spec import FeatureSpec


def _b(value: str) -> FeatureSpec:
    """Shorthand for a single building= filter."""
    return FeatureSpec({"building": [value]}, needs_areas=True)


class BUILDINGS:
    """Building features (OSM building= tag).

    All building specs use area processing (needs_areas=True) because buildings
    are represented as closed polygons in OSM.

    Note: RESIDENTIAL_TAG, COMMERCIAL_TAG, and INDUSTRIAL_TAG refer to the
    specific OSM tag values building=residential, building=commercial, and
    building=industrial. The shorthand names RESIDENTIAL, COMMERCIAL, and
    INDUSTRIAL cover broader groups of related building subtypes.

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.BUILDINGS.RESIDENTIAL, style)
    """

    # ---- individual types ----
    YES = _b("yes")
    """building=yes: Unspecified building outline with no finer classification."""
    BUILDING = _b("building")
    """building=building: Explicitly tagged generic building."""

    HOUSE = _b("house")
    """building=house: Single-family detached house."""
    DETACHED = _b("detached")
    """building=detached: Fully detached residential building."""
    SEMIDETACHED_HOUSE = _b("semidetached_house")
    """building=semidetached_house: Two dwellings sharing one wall."""
    APARTMENTS = _b("apartments")
    """building=apartments: Multi-unit apartment building."""
    TERRACE = _b("terrace")
    """building=terrace: Terraced row-house building."""
    BUNGALOW = _b("bungalow")
    """building=bungalow: Single-storey house."""
    RESIDENTIAL_TAG = _b("residential")
    """building=residential: OSM tag value for generic residential buildings."""

    RETAIL = _b("retail")
    """building=retail: Building used for retail trade."""
    OFFICE = _b("office")
    """building=office: Office building."""
    SUPERMARKET = _b("supermarket")
    """building=supermarket: Supermarket building."""
    HOTEL = _b("hotel")
    """building=hotel: Hotel building."""
    COMMERCIAL_TAG = _b("commercial")
    """building=commercial: OSM tag value for generic commercial buildings."""

    WAREHOUSE = _b("warehouse")
    """building=warehouse: Large storage building."""
    MANUFACTURE = _b("manufacture")
    """building=manufacture: Manufacturing or factory building."""
    INDUSTRIAL_TAG = _b("industrial")
    """building=industrial: OSM tag value for generic industrial buildings."""

    HOSPITAL = _b("hospital")
    """building=hospital: Hospital or medical facility building."""
    SCHOOL = _b("school")
    """building=school: School building."""
    UNIVERSITY = _b("university")
    """building=university: University building."""
    DORMITORY = _b("dormitory")
    """building=dormitory: Dormitory or student residence building."""

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
    FARMHOUSE = _b("farmhouse")
    """building=farmhouse: Main dwelling building on a farm."""
    BARN = _b("barn")
    """building=barn: Farm storage or livestock building."""
    STABLE = _b("stable")
    """building=stable: Building for housing horses or other animals."""
    SPORTS_HALL = _b("sports_hall")
    """building=sports_hall: Indoor sports facility building."""
    STADIUM = _b("stadium")
    """building=stadium: Stadium structure."""

    ROOF = _b("roof")
    """building=roof: Roof structure with no fully enclosed walls."""
    CONSTRUCTION = _b("construction")
    """building=construction: Building currently under construction."""

    # ---- shorthands ----
    RESIDENTIAL = (
        RESIDENTIAL_TAG
        | HOUSE
        | DETACHED
        | SEMIDETACHED_HOUSE
        | APARTMENTS
        | TERRACE
        | BUNGALOW
    )
    """Shorthand for residential dwelling buildings.

    OSM tags: building=residential, house, detached, semidetached_house,
    apartments, terrace, bungalow.

    See also RESIDENTIAL_TAG for the single tag value.
    """
    COMMERCIAL = COMMERCIAL_TAG | RETAIL | OFFICE | SUPERMARKET | HOTEL
    """Shorthand for commercial and business-use buildings.

    OSM tags: building=commercial, retail, office, supermarket, hotel.

    See also COMMERCIAL_TAG for the single tag value.
    """
    INDUSTRIAL = INDUSTRIAL_TAG | WAREHOUSE | MANUFACTURE
    """Shorthand for industrial production and storage buildings.

    OSM tags: building=industrial, warehouse, manufacture.

    See also INDUSTRIAL_TAG for the single tag value.
    """
    RELIGIOUS = CHURCH | CATHEDRAL | MOSQUE | TEMPLE | SYNAGOGUE
    """Shorthand for places of worship and religious buildings.

    OSM tags: building=church, cathedral, mosque, temple, synagogue.
    """
    INSTITUTIONAL = (
        HOSPITAL | SCHOOL | UNIVERSITY | DORMITORY | GOVERNMENT | CIVIC | PUBLIC
    )
    """Shorthand for civic, government, education, and healthcare institutions.

    OSM tags: building=hospital, school, university, dormitory, government,
    civic, public.
    """
    AGRICULTURAL = FARMHOUSE | BARN | STABLE | SHED
    """Shorthand for agricultural buildings and farm outbuildings.

    OSM tags: building=farmhouse, barn, stable, shed.
    """
    SPORTS = SPORTS_HALL | STADIUM
    """Shorthand for sports venue buildings.

    OSM tags: building=sports_hall, stadium.
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
        | AGRICULTURAL
        | SPORTS
        | YES
        | BUILDING
        | GARAGE
        | GARAGES
        | PARKING
        | ROOF
        | CONSTRUCTION
    )
    """Shorthand for all building feature types covered by this module."""
