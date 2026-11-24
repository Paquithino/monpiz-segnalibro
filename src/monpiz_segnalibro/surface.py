"""Thin drawing layer over the ReportLab canvas, one face of the card at a time.

Coordinates are relative to the trimmed card (origin top-left, y downwards),
so a face module reads like its layout spec. Unlike the brochure's panels,
every edge of the card is a trim edge: a background fill runs into the bleed
on all four sides.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import FILL_EVEN_ODD, FILL_NON_ZERO, Canvas

from .geometry import Box, wrap_text
from .icons import BOX as ICON_BOX
from .icons import Stroke, Thread
from .outline import Outliner
from .theme import Font, TextStyle
from .vector import VectorArtwork

BORDER_INSET = 7.0  # icon units: edge of the patch -> stitched border
BORDER_WIDTH = 1.6
BORDER_STITCH = (4.0, 3.0)


class Align(StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


def _shown(text: str, style: TextStyle) -> str:
    return text.upper() if style.uppercase else text


def text_width(text: str, style: TextStyle) -> float:
    """Advance width of ``text`` rendered in ``style``, tracking included."""
    shown = _shown(text, style)
    return float(stringWidth(shown, style.font, style.size)) + style.tracking * max(len(shown) - 1, 0)


class Surface:
    def __init__(
        self,
        canvas: Canvas,
        width: float,
        height: float,
        *,
        bleed: float = 0.0,
        outliner: Outliner | None = None,
    ) -> None:
        self._canvas = canvas
        self.width = width
        self.height = height
        self._bleed = bleed
        self._outliner = outliner  # set: text is drawn as paths, no fonts in the PDF

    @property
    def box(self) -> Box:
        return Box(0.0, 0.0, self.width, self.height)

    def _y(self, top: float) -> float:
        return self.height - top

    def clip(self) -> None:
        """Clip what follows to the card plus its bleed."""
        b = self._bleed
        path = self._canvas.beginPath()
        path.rect(-b, -b, self.width + 2 * b, self.height + 2 * b)
        self._canvas.clipPath(path, stroke=0, fill=0)

    # -- shapes -------------------------------------------------------------

    def fill(self, color: Color) -> None:
        """Flood the card, bleed included."""
        b = self._bleed
        c = self._canvas
        c.saveState()
        c.setFillColor(color)
        c.rect(-b, -b, self.width + 2 * b, self.height + 2 * b, stroke=0, fill=1)
        c.restoreState()

    def hline(
        self,
        x0: float,
        x1: float,
        top: float,
        color: Color,
        width: float = 0.5,
        dash: tuple[float, float] | None = None,
    ) -> None:
        """Horizontal line; with ``dash`` (on, off) and butt caps, like the dashes of the logo's arrow."""
        c = self._canvas
        c.saveState()
        c.setStrokeColor(color)
        c.setLineWidth(width)
        if dash:
            c.setDash(*dash)
        c.line(x0, self._y(top), x1, self._y(top))
        c.restoreState()

    def polyline(self, points: Sequence[tuple[float, float]], color: Color, width: float) -> None:
        """Stroke an open polyline with round joins and caps."""
        if len(points) < 2:
            return
        c = self._canvas
        c.saveState()
        c.setStrokeColor(color)
        c.setLineWidth(width)
        c.setLineJoin(1)
        c.setLineCap(1)
        path = c.beginPath()
        (x, y), *rest = points
        path.moveTo(x, self._y(y))
        for x, y in rest:
            path.lineTo(x, self._y(y))
        c.drawPath(path, stroke=1, fill=0)
        c.restoreState()

    def circle(self, centre: tuple[float, float], radius: float, color: Color, width: float = 0.5) -> None:
        c = self._canvas
        c.saveState()
        c.setStrokeColor(color)
        c.setLineWidth(width)
        c.circle(centre[0], self._y(centre[1]), radius, stroke=1, fill=0)
        c.restoreState()

    def patch(
        self, strokes: Sequence[Stroke], box: Box, felt: Color, threads: Mapping[Thread, Color]
    ) -> None:
        """A round felt patch filling ``box``: stitched border, then the motif in running stitch.

        Stitches have round ends, like thread pulled through felt; the dash
        pattern is corrected for the caps so stitch and gap keep the lengths
        written in :mod:`icons`.
        """
        c = self._canvas
        scale = min(box.width, box.height) / ICON_BOX
        cx, cy = box.centre
        c.saveState()
        c.translate(cx, self._y(cy))
        c.scale(scale, -scale)  # icon units, origin at the centre, y downwards
        c.setFillColor(felt)
        c.circle(0, 0, ICON_BOX / 2, stroke=0, fill=1)
        c.setLineJoin(1)
        c.setLineCap(1)
        self._stitch(threads["cream"], BORDER_WIDTH, BORDER_STITCH)
        c.circle(0, 0, ICON_BOX / 2 - BORDER_INSET, stroke=1, fill=0)
        c.translate(-ICON_BOX / 2, -ICON_BOX / 2)  # motif space: origin top-left
        for stroke in strokes:
            self._stitch(threads[stroke.thread], stroke.width, stroke.dash)
            path = c.beginPath()
            for command, args in stroke.path:
                if command == "M":
                    path.moveTo(*args)
                elif command == "L":
                    path.lineTo(*args)
                elif command == "C":
                    path.curveTo(*args)
                elif command == "Z":
                    path.close()
            c.drawPath(path, stroke=1, fill=0)
        c.restoreState()

    def _stitch(self, color: Color, width: float, dash: tuple[float, float] | None) -> None:
        c = self._canvas
        c.setStrokeColor(color)
        c.setLineWidth(width)
        if dash:
            on, off = dash
            c.setDash(max(on - width, 0.01), off + width)  # round caps add width/2 at each end
        else:
            c.setDash()

    def rect_outline(self, box: Box, color: Color, width: float = 0.5) -> None:
        c = self._canvas
        c.saveState()
        c.setStrokeColor(color)
        c.setLineWidth(width)
        c.rect(box.x, self._y(box.bottom), box.width, box.height, stroke=1, fill=0)
        c.restoreState()

    # -- vector artwork -----------------------------------------------------

    def artwork_turned(
        self, artwork: VectorArtwork, centre: tuple[float, float], length: float, side: float
    ) -> None:
        """``artwork`` turned 90° anticlockwise, so it reads from bottom to top.

        ``length`` is the artwork's own width (now running up the card) and
        ``side`` its own height (now across the card); ``centre`` is where the
        middle of the artwork lands. Paths with a CMYK colour are filled in
        DeviceCMYK, so the logo keeps its print values (pure K black).
        """
        c = self._canvas
        c.saveState()
        c.translate(centre[0], self._y(centre[1]))
        c.rotate(90)
        # viewBox -> a length x side box centred on the origin, y flipped (SVG grows downwards)
        c.scale(length / artwork.width, -side / artwork.height)
        c.translate(-artwork.x - artwork.width / 2, -artwork.y - artwork.height / 2)
        for vector in artwork.paths:
            if vector.cmyk:
                c.setFillColorCMYK(*vector.cmyk)
            else:
                c.setFillColor(HexColor(vector.rgb))
            path = c.beginPath()
            for command, args in vector.commands:
                if command == "M":
                    path.moveTo(*args)
                elif command == "L":
                    path.lineTo(*args)
                elif command == "C":
                    path.curveTo(*args)
                else:
                    path.close()
            c.drawPath(path, stroke=0, fill=1, fillMode=FILL_EVEN_ODD if vector.even_odd else FILL_NON_ZERO)
        c.restoreState()

    def qr(self, url: str, box: Box, color: Color) -> None:
        """A square QR code for ``url``, filling ``box`` (quiet zone excluded)."""
        widget = QrCodeWidget(url, barLevel="M", barFillColor=color, barStrokeColor=color, barBorder=0)
        x0, y0, x1, y1 = widget.getBounds()
        side = min(box.width, box.height)
        drawing = Drawing(side, side, transform=[side / (x1 - x0), 0, 0, side / (y1 - y0), 0, 0])
        drawing.add(widget)
        # The renderer otherwise selects Times-Roman, a font the PDF would reference without embedding.
        drawing.initialFontName = Font.SANS.value
        renderPDF.draw(drawing, self._canvas, box.x, self._y(box.top + side))
        self.link(url, Box(box.x, box.top, side, side))

    def link(self, url: str, box: Box) -> None:
        """Make ``box`` clickable in PDF viewers (harmless in print)."""
        rect = (box.x, self._y(box.bottom), box.right, self._y(box.top))
        self._canvas.linkURL(url, rect, relative=1, thickness=0)

    # -- text ---------------------------------------------------------------

    def text(
        self, text: str, x: float, baseline: float, style: TextStyle, align: Align = Align.LEFT
    ) -> float:
        """Draw one line; ``x`` is its left edge, centre or right edge per ``align``. Returns its width."""
        width = text_width(text, style)
        left = x - {Align.LEFT: 0.0, Align.CENTER: width / 2, Align.RIGHT: width}[align]
        if self._outliner:
            self._outliner.draw(self._canvas, _shown(text, style), left, self._y(baseline), style)
            return width
        t = self._canvas.beginText(left, self._y(baseline))
        t.setFont(style.font, style.size)
        t.setFillColor(style.color)
        t.setCharSpace(style.tracking)
        t.textOut(_shown(text, style))
        self._canvas.drawText(t)
        return width

    def lines(self, text: str, style: TextStyle, width: float) -> list[str]:
        return wrap_text(_shown(text, style), lambda s: text_width(s, style), width)

    def paragraph(self, text: str, x: float, baseline: float, width: float, style: TextStyle) -> float:
        """Draw wrapped, left-aligned text from ``baseline``; returns the last baseline."""
        lines = self.lines(text, style, width)
        for index, line in enumerate(lines):
            self.text(line, x, baseline + index * style.leading, style)
        return baseline + (len(lines) - 1) * style.leading


class MeasuringSurface(Surface):
    """Same geometry and text metrics as ``real``, but draws nothing.

    Lets a block be laid out once to learn its height, then placed for real.
    Only the calls the layout of the details makes are silenced.
    """

    def __init__(self, real: Surface) -> None:
        super().__init__(real._canvas, real.width, real.height)  # the canvas is never touched

    def patch(
        self, strokes: Sequence[Stroke], box: Box, felt: Color, threads: Mapping[Thread, Color]
    ) -> None:
        return None

    def text(
        self, text: str, x: float, baseline: float, style: TextStyle, align: Align = Align.LEFT
    ) -> float:
        return text_width(text, style)
