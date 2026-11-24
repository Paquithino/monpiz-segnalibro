"""Embroidered patches for the details on the back.

Each detail can carry a small round patch of dark felt, like the hats, with a
stitched border and a motif sewn in running stitch: the same mountains and
marks embroidered on the hats. Motifs are drawn in a 100 x 100 design box
(origin top-left, y downwards) and scale with the patch; stitch lengths and
thread weights are in design units too, so a bigger patch gets bigger
stitches, as real embroidery would.

To add a motif: draw it here, add its name to :data:`IconName` and to
:data:`ICONS`; the YAML can then use it in ``back.details[].icon``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

BOX = 100.0

IconName = Literal["ricamo", "acqua", "lana", "crushable"]
Thread = Literal["yellow", "cream", "blue"]  # colours of the thread, resolved by the theme

# One path command: "M" x y, "L" x y, "C" x1 y1 x2 y2 x y, "Z".
Command = tuple[str, tuple[float, ...]]

STITCH = (5.0, 3.2)  # running stitch: thread on top, gap
FINE_STITCH = (3.6, 2.6)


@dataclass(frozen=True, slots=True)
class Stroke:
    path: tuple[Command, ...]
    thread: Thread
    width: float  # design units
    dash: tuple[float, float] | None = STITCH  # None: a solid stroke (cross stitches)


def _line(*points: tuple[float, float]) -> tuple[Command, ...]:
    first, *rest = points
    return (("M", first), *(("L", point) for point in rest))


def _cross(x: float, y: float, arm: float = 3.0) -> tuple[Stroke, Stroke]:
    """A small cross stitch: the blue marks above the peaks on the hats."""
    return (
        Stroke(_line((x - arm, y - arm), (x + arm, y + arm)), "blue", 1.6, None),
        Stroke(_line((x - arm, y + arm), (x + arm, y - arm)), "blue", 1.6, None),
    )


def _drop(cx: float, cy: float, r: float) -> tuple[Command, ...]:
    """A drop, tip up; (``cx``, ``cy``) is the centre of its round part."""
    tip = (cx, cy - 2.1 * r)
    return (
        ("M", tip),
        ("C", (cx, tip[1], cx + r, cy - 0.9 * r, cx + r, cy)),
        ("C", (cx + r, cy + 0.6 * r, cx + 0.55 * r, cy + r, cx, cy + r)),
        ("C", (cx - 0.55 * r, cy + r, cx - r, cy + 0.6 * r, cx - r, cy)),
        ("C", (cx - r, cy - 0.9 * r, cx, tip[1], *tip)),
    )


# Hand embroidery: a ridge of peaks in yellow, a smaller cream peak in front, the
# ground line, and blue cross stitches in the sky.
EMBROIDERY: tuple[Stroke, ...] = (
    Stroke(_line((19, 68), (32, 47), (40, 59), (52, 35), (64, 55), (71, 46), (81, 68)), "yellow", 3.0),
    Stroke(_line((43, 69), (50, 57), (57, 69)), "cream", 2.2, FINE_STITCH),
    Stroke(_line((22, 75), (78, 75)), "cream", 2.0, FINE_STITCH),
    *_cross(31, 31),
    *_cross(46, 23),
    *_cross(63, 26),
    *_cross(74, 36),
)

# Water resistance: a large drop in yellow, two small ones in cream.
WATER: tuple[Stroke, ...] = (
    Stroke(_drop(54, 60, 14), "yellow", 3.0),
    Stroke(_drop(30, 46, 6.5), "cream", 2.0, FINE_STITCH),
    Stroke(_drop(76, 36, 5), "cream", 2.0, FINE_STITCH),
)

# 100% wool: a ball of yarn, its wraps in cream, the loose end trailing off.
WOOL: tuple[Stroke, ...] = (
    Stroke(
        (
            ("M", (48, 27)),
            ("C", (60, 27, 69, 36, 69, 48)),
            ("C", (69, 60, 60, 69, 48, 69)),
            ("C", (36, 69, 27, 60, 27, 48)),
            ("C", (27, 36, 36, 27, 48, 27)),
        ),
        "yellow",
        3.0,
    ),
    Stroke((("M", (40, 29)), ("C", (54, 35, 63, 46, 65, 59))), "cream", 2.0, FINE_STITCH),
    Stroke((("M", (31, 37)), ("C", (45, 42, 55, 54, 56, 67))), "cream", 2.0, FINE_STITCH),
    Stroke((("M", (28, 51)), ("C", (36, 54, 42, 60, 43, 68))), "cream", 2.0, FINE_STITCH),
    Stroke((("M", (66, 61)), ("C", (73, 66, 70, 74, 77, 75))), "yellow", 2.4, FINE_STITCH),  # loose end
)

# Crushable: a hat with a curved arrow over it, rolled up and back into shape.
CRUSHABLE: tuple[Stroke, ...] = (
    Stroke(  # crown, pinched at the top
        (
            ("M", (36, 64)),
            ("L", (38, 46)),
            ("C", (39, 40, 44, 40, 50, 43)),
            ("C", (56, 40, 61, 40, 62, 46)),
            ("L", (64, 64)),
        ),
        "yellow",
        3.0,
    ),
    Stroke((("M", (22, 66)), ("C", (40, 72, 60, 72, 78, 66))), "yellow", 3.0),  # brim
    Stroke(_line((37, 59), (63, 59)), "cream", 2.0, FINE_STITCH),  # band
    Stroke((("M", (28, 44)), ("C", (30, 22, 70, 22, 72, 40))), "cream", 2.2, FINE_STITCH),  # arrow
    Stroke(_line((66, 35), (72, 41), (78, 35)), "cream", 2.2, None),  # arrow head, pointing down
)


Polygon = tuple[tuple[float, float], ...]


def _intersect(
    p: tuple[float, float], d: tuple[float, float], q: tuple[float, float], e: tuple[float, float]
) -> tuple[float, float]:
    """Where the line through ``p`` along ``d`` meets the line through ``q`` along ``e``."""
    det = d[0] * e[1] - d[1] * e[0]
    t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / det
    return p[0] + d[0] * t, p[1] + d[1] * t


def _bent_arrow(
    start: tuple[float, float], corner: tuple[float, float], end: tuple[float, float]
) -> tuple[Polygon, Polygon]:
    """A band folded around ``corner`` (mitred), from ``start`` to ``end``, and its head."""
    half, head_half, head_length = 5.5, 11.0, 11.0

    def unit(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        return (b[0] - a[0]) / length, (b[1] - a[1]) / length

    d1, d2 = unit(start, corner), unit(corner, end)
    n1, n2 = (-d1[1] * half, d1[0] * half), (-d2[1] * half, d2[0] * half)

    def offset(point: tuple[float, float], n: tuple[float, float], sign: int) -> tuple[float, float]:
        return point[0] + sign * n[0], point[1] + sign * n[1]

    band = (
        offset(start, n1, 1),
        _intersect(offset(start, n1, 1), d1, offset(end, n2, 1), d2),
        offset(end, n2, 1),
        offset(end, n2, -1),
        _intersect(offset(start, n1, -1), d1, offset(end, n2, -1), d2),
        offset(start, n1, -1),
    )
    k = head_half / half
    head = (
        (end[0] + n2[0] * k, end[1] + n2[1] * k),
        (end[0] + d2[0] * head_length, end[1] + d2[1] * head_length),
        (end[0] - n2[0] * k, end[1] - n2[1] * k),
    )
    return band, head


def _recycling_sign() -> tuple[Polygon, ...]:
    """The universal recycling sign, flat: three folded arrows chasing each other around a
    triangle, clockwise, each one turning over a corner. One arrow, rotated by 120° twice.
    """
    cx, cy, radius = 50.0, 54.0, 38.0
    corners = [
        (cx + radius * math.cos(math.radians(a)), cy + radius * math.sin(math.radians(a)))
        for a in (-90, 30, 150)  # top, bottom right, bottom left (y downwards)
    ]

    def along(a: tuple[float, float], b: tuple[float, float], f: float) -> tuple[float, float]:
        return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f

    shapes: list[Polygon] = []
    for i in range(3):
        corner, before, after = corners[i], corners[(i + 2) % 3], corners[(i + 1) % 3]
        shapes.extend(_bent_arrow(along(corner, before, 0.36), corner, along(corner, after, 0.36)))
    return tuple(shapes)


# Flat signs, drawn without a patch in a single colour.
SIGNS: dict[str, tuple[Polygon, ...]] = {"riciclo": _recycling_sign()}
SignName = Literal["riciclo"]

ICONS: dict[str, tuple[Stroke, ...]] = {
    "ricamo": EMBROIDERY,
    "acqua": WATER,
    "lana": WOOL,
    "crushable": CRUSHABLE,
}
