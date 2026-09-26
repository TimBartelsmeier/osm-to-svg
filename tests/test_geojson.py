import json

import pytest

from osm_to_svg import polygons_from_json


def test_polygons_from_json_converts_geojson_io_feature_collection() -> None:
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[8.0, 52.0], [8.1, 52.0], [8.1, 52.1], [8.0, 52.0]]
                    ],
                },
            }
        ],
    }

    assert polygons_from_json(geojson) == [
        ((52.0, 8.0), (52.0, 8.1), (52.1, 8.1), (52.0, 8.0))
    ]


def test_polygons_from_json_accepts_json_string_and_direct_polygon() -> None:
    geojson = {
        "type": "Polygon",
        "coordinates": [[[8.0, 52.0], [8.1, 52.0], [8.0, 52.1]]],
    }

    assert polygons_from_json(json.dumps(geojson)) == [
        ((52.0, 8.0), (52.0, 8.1), (52.1, 8.0), (52.0, 8.0))
    ]


def test_polygons_from_json_converts_multiple_features() -> None:
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[8.0, 52.0], [8.1, 52.0], [8.0, 52.1]]],
                },
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[9.0, 53.0], [9.1, 53.0], [9.0, 53.1]]],
                },
            },
        ],
    }

    assert polygons_from_json(geojson) == [
        ((52.0, 8.0), (52.0, 8.1), (52.1, 8.0), (52.0, 8.0)),
        ((53.0, 9.0), (53.0, 9.1), (53.1, 9.0), (53.0, 9.0)),
    ]


@pytest.mark.parametrize(
    "geojson",
    [
        {"type": "FeatureCollection", "features": []},
        {
            "type": "Polygon",
            "coordinates": [
                [[8.0, 52.0], [8.1, 52.0], [8.0, 52.1]],
                [[8.02, 52.02], [8.03, 52.02], [8.02, 52.03]],
            ],
        },
    ],
)
def test_polygons_from_json_rejects_unrepresentable_shapes(geojson) -> None:
    with pytest.raises(ValueError):
        polygons_from_json(geojson)


def test_polygons_from_json_rejects_feature_without_geometry() -> None:
    with pytest.raises(TypeError):
        polygons_from_json(
            {"type": "FeatureCollection", "features": [{"type": "Feature"}]}
        )
