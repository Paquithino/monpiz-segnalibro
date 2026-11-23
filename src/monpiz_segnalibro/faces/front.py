"""Front: only the black and yellow logo, turned on its side like on the shoes' bookmark."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import ContentError
from ..geometry import mm
from ..models import Front
from ..surface import Surface
from ..vector import load_svg
from .base import RenderContext


@dataclass(frozen=True, slots=True)
class FrontFace:
    front: Front

    def draw(self, surface: Surface, ctx: RenderContext) -> None:
        surface.fill(ctx.theme.palette.paper)

        logo = load_svg(ctx.assets_dir / self.front.logo)
        side = mm(self.front.logo_width_mm)  # across the card
        length = side * logo.aspect  # up the card

        top, bottom = ctx.content_top, surface.height - ctx.theme.grid.margin
        if length > bottom - top:
            raise ContentError(
                f"Il logo è lungo {length / mm(1):.0f} mm ma c'è spazio per {(bottom - top) / mm(1):.0f} mm: "
                "riduci front.logo_width_mm"
            )

        # Centred in the free area below the hole: on a long card it reads as centred on the page.
        centre = (surface.width / 2, (top + bottom) / 2)
        surface.artwork_turned(logo, centre, length, side)
