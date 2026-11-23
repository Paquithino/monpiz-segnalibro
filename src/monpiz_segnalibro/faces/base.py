"""Shared face infrastructure: render context, face protocol, common measures."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..geometry import mm
from ..models import Hole
from ..surface import Surface
from ..theme import Theme

HOLE_CLEARANCE = mm(4.0)  # free paper below the hole, so the string never covers the artwork


@dataclass(slots=True)
class RenderContext:
    theme: Theme
    assets_dir: Path
    hole: Hole | None

    @property
    def content_top(self) -> float:
        """Where the artwork may start: below the hole and its clearance, or at the margin."""
        margin = self.theme.grid.margin
        if self.hole is None:
            return margin
        return max(margin, mm(self.hole.bottom_mm) + HOLE_CLEARANCE)


class Face(Protocol):
    def draw(self, surface: Surface, ctx: RenderContext) -> None: ...
