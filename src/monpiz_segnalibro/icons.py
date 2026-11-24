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

IconName = Literal["ricamo", "acqua", "lana", "crushable", "riciclo"]
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


def _side_arrow(start: tuple[float, float], end: tuple[float, float]) -> tuple[Stroke, Stroke]:
    """One side of the recycling triangle: a stitched shaft from ``start`` towards ``end``,
    stopping short of both corners, and a solid arrowhead pointing at the next side.
    """
    (x0, y0), (x1, y1) = start, end
    length = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length  # along the side
    nx, ny = -uy, ux
    tail = (x0 + ux * length * 0.2, y0 + uy * length * 0.2)
    tip = (x0 + ux * length * 0.84, y0 + uy * length * 0.84)
    back, half = 9.0, 6.5
    head = _line(
        (tip[0] - ux * back + nx * half, tip[1] - uy * back + ny * half),
        tip,
        (tip[0] - ux * back - nx * half, tip[1] - uy * back - ny * half),
    )
    return Stroke(_line(tail, tip), "yellow", 3.4), Stroke(head, "yellow", 3.4, None)


# Recycling: the classic triangle of three arrows chasing each other, clockwise.
_TOP, _RIGHT, _LEFT = (50.0, 22.0), (77.0, 69.0), (23.0, 69.0)
RECYCLE: tuple[Stroke, ...] = (
    *_side_arrow(_TOP, _RIGHT),
    *_side_arrow(_RIGHT, _LEFT),
    *_side_arrow(_LEFT, _TOP),
)

ICONS: dict[str, tuple[Stroke, ...]] = {
    "ricamo": EMBROIDERY,
    "acqua": WATER,
    "lana": WOOL,
    "crushable": CRUSHABLE,
    "riciclo": RECYCLE,
}
