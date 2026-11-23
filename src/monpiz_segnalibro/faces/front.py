"""Front: only the black and yellow logo, turned on its side like on the shoes' bookmark."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import ContentError
from ..geometry import mm
from ..models import Front
from ..surface import Surface
from .base import RenderContext

MIN_PRINT_DPI = 300.0  # flat artwork with hard edges: it needs more than a photo


@dataclass(frozen=True, slots=True)
class FrontFace:
    front: Front

    def draw(self, surface: Surface, ctx: RenderContext) -> None:
        surface.fill(ctx.theme.palette.paper)

        side = mm(self.front.logo_width_mm)  # across the card
        px_w, px_h = ctx.images.size(self.front.logo)
        length = side * px_w / px_h  # up the card

        top, bottom = ctx.content_top, surface.height - ctx.theme.grid.margin
        if length > bottom - top:
            raise ContentError(
                f"Il logo è lungo {length / mm(1):.0f} mm ma c'è spazio per {(bottom - top) / mm(1):.0f} mm: "
                "riduci front.logo_width_mm"
            )

        dpi = ctx.images.effective_dpi(self.front.logo, length)
        if dpi < MIN_PRINT_DPI:
            ctx.warnings.append(
                f"{self.front.logo}: stampato a {dpi:.0f} dpi (consigliati {MIN_PRINT_DPI:.0f})"
            )

        # Centred in the free area below the hole: on a long card it reads as centred on the page.
        centre = (surface.width / 2, (top + bottom) / 2)
        surface.image_turned(ctx.images.fitted(self.front.logo, length, side), centre, length, side)
