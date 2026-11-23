"""Pure layout helpers, independent of ReportLab and therefore unit-testable.

Same conventions as the lookbook and the brochure: origin at the top-left
corner, y growing downwards, units in points.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

POINTS_PER_MM = 72.0 / 25.4


def mm(value: float) -> float:
    """Millimetres to points."""
    return value * POINTS_PER_MM


@dataclass(frozen=True, slots=True)
class Box:
    x: float
    top: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.top + self.height

    @property
    def centre(self) -> tuple[float, float]:
        return self.x + self.width / 2, self.top + self.height / 2

    def inset(self, dx: float, dy: float | None = None) -> Box:
        dy = dx if dy is None else dy
        return Box(self.x + dx, self.top + dy, self.width - 2 * dx, self.height - 2 * dy)


def columns(left: float, right: float, count: int, gutter: float) -> list[tuple[float, float]]:
    """``count`` equal columns between ``left`` and ``right``: (x, width) each."""
    width = (right - left - (count - 1) * gutter) / count
    return [(left + index * (width + gutter), width) for index in range(count)]


def wrap_text(text: str, measure: Callable[[str], float], width: float) -> list[str]:
    """Greedy word wrap; explicit newlines are kept, long words are never broken."""
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}" if current else word
            if current and measure(candidate) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return lines


def balanced_lines(text: str, measure: Callable[[str], float], width: float) -> list[str]:
    """Like :func:`wrap_text` for a single short line, but when it needs two lines the
    break goes where the two are closest in length: "Ricamati / a mano", not
    "Ricamati a / mano". Longer text falls back to the greedy wrap.
    """
    greedy = wrap_text(text, measure, width)
    if len(greedy) != 2 or "\n" in text:
        return greedy
    words = text.split()
    splits = [(" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))]
    fitting = [pair for pair in splits if max(measure(pair[0]), measure(pair[1])) <= width]
    if not fitting:
        return greedy
    first, second = min(fitting, key=lambda pair: max(measure(pair[0]), measure(pair[1])))
    return [first, second]
