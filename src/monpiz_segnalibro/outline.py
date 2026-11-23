"""Text converted to outlines, for the fully vector PDF.

Printers often ask for "testi convertiti in tracciati": no fonts in the file,
so nothing can be substituted or reflowed on their side. Each glyph is read
from the same TrueType file ReportLab embeds and drawn as a filled path,
advancing by the same widths (``hmtx``) ReportLab uses for ``stringWidth``:
the outlined text lands exactly where the live text would.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfgen.pathobject import PDFPathObject

from .theme import TextStyle


class _PathPen(BasePen):  # type: ignore[misc]
    """fontTools pen writing into a ReportLab path, with an affine placement."""

    def __init__(self, glyph_set: Any, path: PDFPathObject, x: float, y: float, scale: float) -> None:
        super().__init__(glyph_set)
        self._path, self._x, self._y, self._scale = path, x, y, scale

    def _point(self, point: tuple[float, float]) -> tuple[float, float]:
        return self._x + point[0] * self._scale, self._y + point[1] * self._scale

    def _moveTo(self, pt: tuple[float, float]) -> None:
        self._path.moveTo(*self._point(pt))

    def _lineTo(self, pt: tuple[float, float]) -> None:
        self._path.lineTo(*self._point(pt))

    def _curveToOne(self, p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> None:
        self._path.curveTo(*self._point(p1), *self._point(p2), *self._point(p3))

    def _closePath(self) -> None:
        self._path.close()

    # TrueType quadratics are raised to cubics by BasePen._qCurveToOne.


class Outliner:
    """Draws text as paths, one font file per :class:`~monpiz_segnalibro.theme.Font`."""

    def __init__(self, fonts_dir: Path) -> None:
        self._fonts_dir = fonts_dir

    @cache  # noqa: B019 - one Outliner per build, the cache dies with it
    def _font(self, name: str) -> TTFont:
        return TTFont(str(self._fonts_dir / f"{name}.ttf"))

    def draw(self, canvas: Canvas, text: str, x: float, baseline: float, style: TextStyle) -> None:
        """``text`` with its left edge at ``x`` and baseline at ``baseline`` (PDF coordinates)."""
        font = self._font(style.font.value)
        cmap = font.getBestCmap()
        glyphs = font.getGlyphSet()
        metrics = font["hmtx"]
        scale = style.size / font["head"].unitsPerEm

        path = canvas.beginPath()
        cursor = x
        for char in text:
            name = cmap.get(ord(char), ".notdef")
            glyphs[name].draw(_PathPen(glyphs, path, cursor, baseline, scale))
            cursor += metrics[name][0] * scale + style.tracking
        canvas.saveState()
        canvas.setFillColor(style.color)
        canvas.drawPath(path, stroke=0, fill=1, fillMode=1)  # non-zero winding, as TrueType wants
        canvas.restoreState()
