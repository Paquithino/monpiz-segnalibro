"""Assembles the two faces and renders the print PDF.

    page 1: front (logo)
    page 2: back  (details, note, QR codes)

Every page is the trimmed card plus a bleed, declared as TrimBox and BleedBox
for the printer's preflight. ``marks`` adds crop marks in a slug around it;
``guides`` draws the trim, the safe area and the hole on top of the
artwork, for proofing on screen only. The hole is centred across the card,
so it lines up on both faces whichever way the sheet is turned.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from . import __version__
from .content import load_bookmark
from .faces import BackFace, Face, FrontFace, RenderContext
from .fonts import register_fonts
from .geometry import mm
from .images import ImageLibrary
from .models import Bookmark
from .surface import Surface
from .theme import Font, Theme, default_theme

SLUG = 24.0  # room outside the bleed for crop marks
MARK_LENGTH = 14.0
MARK_GAP = 3.0  # marks stop short of the bleed
MARK_WIDTH = 0.3
GUIDE_COLOR = HexColor("#E6007E")  # process magenta: unmistakably not part of the design


@dataclass(frozen=True, slots=True)
class BuildOptions:
    content_file: Path
    assets_dir: Path
    output: Path
    dpi: int = 300
    bleed: bool = True
    marks: bool = False
    guides: bool = False


@dataclass(frozen=True, slots=True)
class BuildResult:
    output: Path
    size_bytes: int
    size_mm: tuple[float, float]
    warnings: tuple[str, ...]


def faces(bookmark: Bookmark) -> Sequence[tuple[str, Face]]:
    return [("Fronte", FrontFace(bookmark.front)), ("Retro", BackFace(bookmark.back))]


def render(bookmark: Bookmark, options: BuildOptions, theme: Theme | None = None) -> list[str]:
    """Write the PDF to ``options.output``; returns the print warnings."""
    theme = theme or default_theme()
    register_fonts(options.assets_dir / "fonts")
    ctx = RenderContext(theme, ImageLibrary(options.assets_dir, options.dpi), bookmark.hole)
    fmt = bookmark.format
    width, height = mm(fmt.width_mm), mm(fmt.height_mm)

    bleed = mm(fmt.bleed_mm) if options.bleed else 0.0
    margin = bleed + (SLUG if options.marks else 0.0)  # trim edge -> page edge
    trim = (margin, margin, margin + width, margin + height)
    partial = options.output.with_name(f".{options.output.name}.{os.getpid()}.partial")
    options.output.parent.mkdir(parents=True, exist_ok=True)

    canvas = Canvas(
        str(partial),
        pagesize=(width + 2 * margin, height + 2 * margin),
        invariant=True,
        initialFontName=Font.SANS.value,  # avoids a stray, non-embedded Helvetica
        trimBox=trim,
        bleedBox=(trim[0] - bleed, trim[1] - bleed, trim[2] + bleed, trim[3] + bleed),
    )
    canvas.setTitle(bookmark.meta.title)
    canvas.setAuthor(bookmark.meta.author)
    canvas.setSubject(bookmark.meta.subject)
    canvas.setCreator(f"monpiz-segnalibro {__version__}")

    try:
        for name, face in faces(bookmark):
            canvas.bookmarkPage(name)
            canvas.addOutlineEntry(name, name)  # "Fronte" / "Retro" in the viewer's sidebar
            canvas.saveState()
            canvas.translate(margin, margin)
            surface = Surface(canvas, width, height, bleed=bleed)
            surface.clip()
            face.draw(surface, ctx)
            if options.guides:
                _draw_guides(surface, ctx)
            canvas.restoreState()
            if options.marks:
                _draw_marks(canvas, trim, bleed)
            canvas.showPage()
        canvas.save()
        partial.replace(options.output)
    finally:
        partial.unlink(missing_ok=True)
    return ctx.warnings


def build(options: BuildOptions) -> BuildResult:
    bookmark = load_bookmark(options.content_file, options.assets_dir)
    warnings = render(bookmark, options)
    return BuildResult(
        output=options.output,
        size_bytes=options.output.stat().st_size,
        size_mm=(bookmark.format.width_mm, bookmark.format.height_mm),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _draw_marks(canvas: Canvas, trim: tuple[float, float, float, float], bleed: float) -> None:
    """Crop marks at the four corners."""
    left, bottom, right, top = trim
    start, end = bleed + MARK_GAP, bleed + MARK_GAP + MARK_LENGTH
    canvas.saveState()
    canvas.setStrokeColorCMYK(1, 1, 1, 1)  # registration black: shows on every plate
    canvas.setLineWidth(MARK_WIDTH)
    for x, dx in ((left, -1), (right, 1)):
        for y, dy in ((bottom, -1), (top, 1)):
            canvas.line(x + dx * start, y, x + dx * end, y)
            canvas.line(x, y + dy * start, x, y + dy * end)
    canvas.restoreState()


def _draw_guides(surface: Surface, ctx: RenderContext) -> None:
    """Trim, safe area and hole: proofing only, never for print."""
    surface.rect_outline(surface.box, GUIDE_COLOR, 0.4)
    surface.rect_outline(surface.box.inset(ctx.theme.grid.margin), GUIDE_COLOR, 0.4)
    if ctx.hole:
        centre = (surface.width / 2, mm(ctx.hole.from_top_mm))
        surface.circle(centre, mm(ctx.hole.diameter_mm) / 2, GUIDE_COLOR, 0.4)
