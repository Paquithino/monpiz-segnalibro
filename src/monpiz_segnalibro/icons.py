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

from dataclasses import dataclass
from typing import Literal

BOX = 100.0

IconName = Literal["ricamo", "acqua"]
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

ICONS: dict[str, tuple[Stroke, ...]] = {"ricamo": EMBROIDERY, "acqua": WATER}
