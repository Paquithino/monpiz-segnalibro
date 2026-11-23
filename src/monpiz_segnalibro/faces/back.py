"""Back: the hats' details, the invitation to keep the card as a bookmark, the QR codes.

Laid out from both ends: the heading and the details run down from the top,
the QR codes and the footer sit on the bottom margin, and the mountain line
with the note is centred in the space left between the two. Content that
does not fit stops the build with a message instead of overlapping.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import ContentError
from ..geometry import Box, columns, mm
from ..models import Back
from ..mountain import SKYLINE, place
from ..surface import Surface
from .base import RenderContext

EYEBROW_TO_TITLE = 19.0
TITLE_TO_DASHES = 11.0
DASHES = (3.4, 2.2)  # on, off: the rhythm of the logo's dashed arrow
DASH_WIDTH = 2.2
DASH_LENGTH = mm(9.5)
DASHES_TO_DETAIL = 19.0
NAME_TO_TEXT = 10.5
DETAIL_GAP = 15.0  # last line of a detail -> next name
QR_SIDE = mm(15.0)
QR_TO_LABEL = 8.0  # bottom of the QR code -> label baseline
LABEL_TO_FOOTER = 13.0
SKYLINE_HEIGHT = mm(8.0)
SKYLINE_WIDTH = 1.1
SKYLINE_TO_NOTE = 20.0
MIN_GAP = 12.0  # least air above and below the middle group


@dataclass(frozen=True, slots=True)
class BackFace:
    back: Back

    def draw(self, surface: Surface, ctx: RenderContext) -> None:
        p, t, g = ctx.theme.palette, ctx.theme.type, ctx.theme.grid
        x, width = g.margin, surface.width - 2 * g.margin
        surface.fill(p.paper)

        # Top: heading, yellow dashes, details.
        baseline = ctx.content_top + t.eyebrow.size
        surface.text(self.back.eyebrow, x, baseline, t.eyebrow)
        last = surface.paragraph(self.back.title, x, baseline + EYEBROW_TO_TITLE, width, t.title)
        if self.back.title_italic:
            last = surface.paragraph(
                self.back.title_italic, x, last + t.title_italic.leading, width, t.title_italic
            )
        dashes = last + TITLE_TO_DASHES
        surface.hline(x, x + DASH_LENGTH, dashes, p.yellow, DASH_WIDTH, dash=DASHES)

        name = dashes + DASHES_TO_DETAIL
        for detail in self.back.details:
            surface.text(detail.name, x, name, t.item)
            last = surface.paragraph(detail.text, x, name + NAME_TO_TEXT, width, t.text)
            name = last + DETAIL_GAP + t.item.size
        top_end = last + t.text.leading - t.text.size  # just under the descenders of the last line

        # Bottom, from the margin up: footer, QR labels, QR codes.
        bottom = surface.height - g.margin
        if self.back.footer:
            surface.text(self.back.footer, x, bottom, t.small)
            label = bottom - LABEL_TO_FOOTER
        else:
            label = bottom
        bottom_start = label
        if self.back.qr:
            qr_bottom = label - QR_TO_LABEL
            for (cx, cw), code in zip(columns(x, x + width, 2, g.gutter), self.back.qr, strict=False):
                side = min(QR_SIDE, cw)
                surface.qr(code.url, Box(cx, qr_bottom - side, side, side), p.ink)
                surface.text(code.label, cx, label, t.label)
            bottom_start = qr_bottom - QR_SIDE

        # Middle: the mountain line and the note, centred in what is left.
        note_lines = surface.lines(self.back.note, t.note, width) if self.back.note else []
        group = SKYLINE_HEIGHT + (
            SKYLINE_TO_NOTE + (len(note_lines) - 1) * t.note.leading if note_lines else 0
        )
        room = bottom_start - top_end
        if room < group + 2 * MIN_GAP:
            raise ContentError(
                f"Il retro non sta nel formato: mancano {(group + 2 * MIN_GAP - room) / mm(1):.1f} mm. "
                "Accorcia i testi (back.details, back.note) o togli un QR."
            )
        top = top_end + (room - group) / 2
        skyline = place(SKYLINE, x, top, width, SKYLINE_HEIGHT)
        surface.polyline(skyline, p.yellow, SKYLINE_WIDTH)
        for index, line in enumerate(note_lines):
            surface.text(line, x, top + SKYLINE_HEIGHT + SKYLINE_TO_NOTE + index * t.note.leading, t.note)
