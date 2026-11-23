"""Line icons for the details on the back, drawn as vector paths.

Each icon lives in a 100 x 100 design box (origin top-left, y downwards) and
is meant to sit inside a filled circle of the same box: keep the drawing
within roughly 20..80 so it breathes inside the circle. Strokes are in design
units too (3.2 = about 0.8 pt in a circle 8.5 mm wide), so line weights
scale with the badge. A ``knockout`` stroke is drawn in the circle's colour,
to cut a gap through what is under it (the eye of the needle).

To add an icon: draw it here, add its name to :data:`IconName` and to
:data:`ICONS`; the YAML can then use it in ``back.details[].icon``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BOX = 100.0

IconName = Literal["ricamo", "acqua"]

# One path command: "M" x y, "L" x y, "C" x1 y1 x2 y2 x y, "Z".
Command = tuple[str, tuple[float, ...]]


@dataclass(frozen=True, slots=True)
class Stroke:
    path: tuple[Command, ...]
    width: float  # design units
    dash: tuple[float, float] | None = None  # on, off, in design units; dashes get butt caps
    knockout: bool = False


def _line(*points: tuple[float, float]) -> tuple[Command, ...]:
    first, *rest = points
    return (("M", first), *(("L", point) for point in rest))


LINE = 3.2

# Hand embroidery: a needle on the diagonal, its thread looping down into a row of
# stitches. The stitches are dashes, like the arrow of the logo.
EMBROIDERY: tuple[Stroke, ...] = (
    Stroke(_line((31, 63), (63, 31)), 5.6),  # shank
    Stroke(_line((24, 70), (33, 61)), 2.6),  # point, thinner
    Stroke(_line((55.0, 39.0), (61.0, 33.0)), 2.3, knockout=True),  # eye
    Stroke((("M", (59, 35)), ("C", (78, 22, 86, 56, 72, 72))), LINE),  # thread from the eye
    Stroke(_line((72, 72), (26, 76)), LINE, dash=(6.0, 4.5)),  # running stitches
)

# Water resistance: a drop with a highlight, and a small drop beside it.
WATER: tuple[Stroke, ...] = (
    Stroke(
        (
            ("M", (52, 20)),
            ("C", (52, 20, 34, 44, 34, 58)),
            ("C", (34, 68, 42, 77, 52, 77)),
            ("C", (62, 77, 70, 68, 70, 58)),
            ("C", (70, 44, 52, 20, 52, 20)),
            ("Z", ()),
        ),
        LINE,
    ),
    Stroke((("M", (43, 58)), ("C", (43, 64, 46, 68, 50, 69))), LINE),  # highlight
    Stroke(
        (
            ("M", (28, 30)),
            ("C", (28, 30, 22, 38, 22, 42)),
            ("C", (22, 46, 25, 48, 28, 48)),
            ("C", (31, 48, 34, 46, 34, 42)),
            ("C", (34, 38, 28, 30, 28, 30)),
            ("Z", ()),
        ),
        2.6,
    ),
)

ICONS: dict[str, tuple[Stroke, ...]] = {"ricamo": EMBROIDERY, "acqua": WATER}
