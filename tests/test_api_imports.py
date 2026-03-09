from osm_to_svg import SvgMapper as PackageSvgMapper
from osm_to_svg.mapper import SvgMapper as ModuleSvgMapper


def test_svgmapper_package_export_matches_module_class() -> None:
    assert PackageSvgMapper is ModuleSvgMapper
