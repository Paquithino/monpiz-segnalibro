"""The lookbook's Dolomite skyline: here it echoes the mountains embroidered on the hats.

Same stroke as ``monpiz_lookbook.mountain`` and ``monpiz_brochure.mountain``,
in a 1000 x 700 design box (origin top-left, y downwards); ``place`` maps it
onto the card.
"""

from __future__ import annotations

Point = tuple[float, float]
Stroke = tuple[Point, ...]

BOX_WIDTH = 1000.0

SKYLINE: Stroke = (
    (0, 440), (45, 400), (70, 410), (115, 318), (135, 340),
    (175, 212), (200, 300), (222, 282), (262, 138), (292, 262), (312, 242),
    (352, 108), (372, 182), (386, 168),
    (447, 28), (500, 192), (515, 176),
    (560, 68), (598, 216), (620, 200),
    (668, 148), (705, 266), (730, 250), (780, 212), (815, 310), (850, 296),
    (900, 342), (950, 330), (1000, 366),
)  # fmt: skip


def place(points: Stroke, x: float, top: float, width: float, height: float) -> list[Point]:
    """``points`` stretched onto a ``width`` x ``height`` box at (``x``, ``top``)."""
    ys = [py for _, py in points]
    low, high = min(ys), max(ys)
    return [(x + px / BOX_WIDTH * width, top + (py - low) / (high - low) * height) for px, py in points]
