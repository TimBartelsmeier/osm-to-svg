import pytest

from osm_to_svg.validation import validate_bbox


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
