import pytest

from osm_to_svg.validation import _segments_intersect, validate_bbox


def test_validate_bbox_accepts_valid_values() -> None:
    bbox = ((52.0, 8.0), (52.0, 9.0), (53.0, 9.0), (53.0, 8.0))
    assert validate_bbox(bbox) == (*bbox, bbox[0])


def test_validate_bbox_normalizes_explicitly_closed_values() -> None:
    bbox = ((52.0, 8.0), (52.0, 9.0), (53.0, 9.0), (53.0, 8.0), (52.0, 8.0))
    assert validate_bbox(bbox) == bbox


def test_validate_bbox_rejects_non_numeric_coordinates() -> None:
    with pytest.raises(ValueError, match="real numbers"):
        validate_bbox(((0.0, "invalid"), (0.0, 1.0), (1.0, 1.0)))


@pytest.mark.parametrize(
    "bbox",
    [
        ((90.0, 0.0), (90.0, 1.0), (89.0, 1.0)),
        ((0.0, 179.0), (0.0, -179.0), (1.0, -179.0)),
    ],
)
def test_validate_bbox_rejects_unsupported_geographic_edges(bbox) -> None:
    with pytest.raises(ValueError):
        validate_bbox(bbox)


@pytest.mark.parametrize(
    ("first", "second"),
    [
        (((0.0, 0.0), (0.0, 2.0)), ((0.0, 1.0), (1.0, 1.0))),
        (((0.0, 0.0), (0.0, 2.0)), ((1.0, 1.0), (0.0, 1.0))),
        (((0.0, 1.0), (1.0, 1.0)), ((0.0, 0.0), (0.0, 2.0))),
        (((0.0, 1.0), (1.0, 1.0)), ((0.0, 2.0), (0.0, 0.0))),
        (((1.0, 0.0), (0.0, 0.0)), ((0.0, 1.0), (0.0, -1.0))),
        (((0.0, 0.0), (1.0, 1.0)), ((0.0, 1.0), (1.0, 0.0))),
    ],
)
def test_segment_intersection_handles_touching_and_crossing_segments(
    first, second
) -> None:
    assert _segments_intersect(*first, *second)


def test_validate_bbox_rejects_non_iterable_input() -> None:
    with pytest.raises(ValueError, match="sequence"):
        validate_bbox(None)


def test_validate_bbox_rejects_empty_polygon() -> None:
    with pytest.raises(ValueError, match="at least three"):
        validate_bbox(())


def test_validate_bbox_rejects_wrong_vertex_shape_and_non_finite_values() -> None:
    with pytest.raises(ValueError, match="exactly latitude"):
        validate_bbox(((0.0, 0.0, 1.0), (0.0, 1.0), (1.0, 1.0)))
    with pytest.raises(ValueError, match="finite"):
        validate_bbox(((float("nan"), 0.0), (0.0, 1.0), (1.0, 1.0)))


@pytest.mark.parametrize(
    ("bbox", "error_fragment"),
    [
        (((0.0, -181.0), (0.0, 0.0), (10.0, 0.0)), "Invalid longitude"),
        (((-91.0, 0.0), (0.0, 0.0), (10.0, 0.0)), "Invalid latitude"),
        (((0.0, 0.0), (1.0, 1.0), (2.0, 2.0)), "nonzero area"),
        (((0.0, 0.0), (2.0, 2.0), (0.0, 2.0), (2.0, 0.0)), "self-intersect"),
    ],
)
def test_validate_bbox_rejects_invalid_ranges(
    bbox: tuple[tuple[float, float], ...],
    error_fragment: str,
) -> None:
    with pytest.raises(ValueError, match=error_fragment):
        validate_bbox(bbox)
