"""Pure layout helpers."""

import pytest

from monpiz_segnalibro.geometry import Box, columns, mm, wrap_text
from monpiz_segnalibro.mountain import SKYLINE, place


def test_mm_to_points() -> None:
    assert mm(25.4) == pytest.approx(72.0)


def test_box_inset_and_centre() -> None:
    box = Box(0, 0, 100, 40).inset(10)
    assert (box.x, box.top, box.width, box.height) == (10, 10, 80, 20)
    assert box.centre == (50, 20)


def test_columns_fill_the_span() -> None:
    (x0, w0), (x1, w1) = columns(10, 110, 2, 10)
    assert (x0, w0, x1, w1) == (10, 45, 65, 45)


def test_wrap_keeps_newlines_and_long_words() -> None:
    assert wrap_text("aa bb cc\ndd", len, 5) == ["aa bb", "cc", "dd"]
    assert wrap_text("lunghissima", len, 3) == ["lunghissima"]


def test_skyline_fills_its_box() -> None:
    points = place(SKYLINE, 5, 10, 100, 20)
    xs, ys = [x for x, _ in points], [y for _, y in points]
    assert (min(xs), max(xs), min(ys), max(ys)) == (5, 105, 10, 30)


def test_motifs_stay_inside_the_stitched_border() -> None:
    from monpiz_segnalibro.icons import BOX, ICONS

    for name, strokes in ICONS.items():
        for stroke in strokes:
            for _, args in stroke.path:
                for px, py in zip(args[::2], args[1::2], strict=True):
                    distance = ((px - BOX / 2) ** 2 + (py - BOX / 2) ** 2) ** 0.5
                    # inside the stitched border, which runs 7 units in from the edge
                    assert distance < BOX / 2 - 10, f"{name}: ({px}, {py}) tocca il bordo cucito"


def test_balanced_lines_split_evenly() -> None:
    from monpiz_segnalibro.geometry import balanced_lines

    assert balanced_lines("Ricamati a mano", len, 11) == ["Ricamati", "a mano"]
    assert balanced_lines("Corto", len, 11) == ["Corto"]


def test_recycling_sign_stays_in_its_box() -> None:
    from monpiz_segnalibro.icons import BOX, SIGNS

    points = [point for polygon in SIGNS["riciclo"] for point in polygon]
    assert len(SIGNS["riciclo"]) == 6  # three bands, three heads
    assert all(0 <= x <= BOX and 0 <= y <= BOX for x, y in points)
