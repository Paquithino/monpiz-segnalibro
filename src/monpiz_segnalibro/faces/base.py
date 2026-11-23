"""Shared face infrastructure: render context, face protocol, common measures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..geometry import mm
from ..images import ImageLibrary
from ..models import Hole
from ..surface import Surface
from ..theme import Theme

HOLE_CLEARANCE = mm(4.0)  # free paper below the hole, so the string never covers the artwork


@dataclass(slots=True)
class RenderContext:
    theme: Theme
    images: ImageLibrary
    hole: Hole | None
    warnings: list[str] = field(default_factory=list)

    @property
    def content_top(self) -> float:
        """Where the artwork may start: below the hole and its clearance, or at the margin."""
        margin = self.theme.grid.margin
        if self.hole is None:
            return margin
        return max(margin, mm(self.hole.bottom_mm) + HOLE_CLEARANCE)


class Face(Protocol):
    def draw(self, surface: Surface, ctx: RenderContext) -> None: ...
