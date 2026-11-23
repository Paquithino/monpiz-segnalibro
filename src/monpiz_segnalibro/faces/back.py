"""Back: the hats' details, the invitation to keep the card as a bookmark, the QR codes.

Laid out from both ends: the heading and the details run down from the top,
the QR codes and the footer sit on the bottom margin, and the note (with the
mountain line, if enabled) is centred in the space left between the two.
Content that does not fit stops the build with a message instead of
overlapping.

The details come in two layouts, chosen in the YAML:

- ``list``: one under the other, the felt patch with the name beside it and
  the description below, across the column. Room for two or three.
- ``grid``: two per row, each a patch with the name and a short line centred
  under it, like a set of patches sewn side by side. Room for four.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from reportlab.lib.colors import Color

from ..errors import ContentError
from ..geometry import Box, balanced_lines, columns, mm
from ..icons import ICONS, Thread
from ..models import Back, Detail
from ..mountain import SKYLINE, place
from ..surface import Align, Surface, text_width
from ..theme import Theme
from .base import RenderContext

EYEBROW_TO_TITLE = 19.0
TITLE_TO_DASHES = 11.0
DASHES = (3.4, 2.2)  # on, off: the rhythm of the logo's dashed arrow
DASH_WIDTH = 2.2
DASH_LENGTH = mm(9.5)
DASHES_TO_DETAIL = 12.0  # dashes -> top of the first detail
CAP_HEIGHT = 0.7  # Fraunces capitals, share of the font size

# list layout
BADGE = mm(11.0)  # diameter of the felt patch
BADGE_TO_TEXT = mm(2.5)
BADGE_TO_DESCRIPTION = 10.0  # bottom of the patch -> first baseline of the description
NAME_TO_TEXT = 10.5
DETAIL_GAP = 12.0  # bottom of a detail -> top of the next

# grid layout
GRID_BADGE = mm(10.5)
GRID_BADGE_TO_NAME = 10.0  # bottom of the patch -> first baseline of the name
GRID_NAME_TO_TEXT = 8.0
GRID_ROW_GAP = 11.0  # bottom of a row -> top of the next
GRID_GUTTER = mm(2.0)

QR_SIDE = mm(15.0)
QR_TO_LABEL = 8.0  # bottom of the QR code -> label baseline
LABEL_TO_FOOTER = 13.0
SKYLINE_SPAN = mm(20.0)  # a small ridge, not a full-width rule: it divides the blocks
SKYLINE_HEIGHT = mm(7.0)
SKYLINE_WIDTH = 1.0
SKYLINE_TO_NOTE = 20.0
MIN_GAP = 12.0  # least air above and below the middle group
NOTE_TO_TRANSLATION = 12.0  # last baseline of the note -> first baseline of its English line
NAME_TO_TRANSLATION = 9.0  # last baseline of a name -> its English line


def _threads(theme: Theme) -> dict[Thread, Color]:
    p = theme.palette
    return {"yellow": p.yellow, "cream": p.thread_cream, "blue": p.thread_blue}


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

        area = Box(x, dashes + DASHES_TO_DETAIL, width, 0.0)
        if self.back.layout == "grid":
            top_end = _grid(surface, ctx, self.back.details, area)
        else:
            top_end = _list(surface, ctx, self.back.details, area)

        # Bottom, from the margin up: footer, QR labels, QR codes.
        bottom = surface.height - g.margin
        footers = [line for line in (self.back.footer, self.back.footer_en) if line]
        for index, line in enumerate(footers):
            surface.text(line, x, bottom - (len(footers) - 1 - index) * t.small.leading, t.small)
        label = bottom - (len(footers) - 1) * t.small.leading - LABEL_TO_FOOTER if footers else bottom
        bottom_start = label
        if self.back.qr:
            qr_bottom = label - QR_TO_LABEL
            for (cx, cw), code in zip(columns(x, x + width, 2, g.gutter), self.back.qr, strict=False):
                side = min(QR_SIDE, cw)
                surface.qr(code.url, Box(cx, qr_bottom - side, side, side), p.ink)
                surface.text(code.label, cx, label, t.label)
            bottom_start = qr_bottom - QR_SIDE

        # Middle: the mountain line (optional) and the note, centred in what is left.
        note_lines = surface.lines(self.back.note, t.note, width) if self.back.note else []
        en_lines = surface.lines(self.back.note_en, t.translation, width) if self.back.note_en else []
        skyline = SKYLINE_HEIGHT + SKYLINE_TO_NOTE - t.note.size if self.back.skyline else 0.0
        note = t.note.size + (len(note_lines) - 1) * t.note.leading if note_lines else 0.0
        if en_lines:
            note += NOTE_TO_TRANSLATION + (len(en_lines) - 1) * t.translation.leading
        group = skyline + note
        room = bottom_start - top_end
        if room < group + 2 * MIN_GAP:
            raise ContentError(
                f"Il retro non sta nel formato: mancano {(group + 2 * MIN_GAP - room) / mm(1):.1f} mm. "
                "Accorcia i testi (back.details, back.note), togli la linea delle montagne "
                "(back.skyline) o un QR."
            )
        top = top_end + (room - group) / 2
        if self.back.skyline:
            surface.polyline(place(SKYLINE, x, top, SKYLINE_SPAN, SKYLINE_HEIGHT), p.yellow, SKYLINE_WIDTH)
        first = top + skyline + t.note.size
        for index, line in enumerate(note_lines):
            surface.text(line, x, first + index * t.note.leading, t.note)
        first += (len(note_lines) - 1) * t.note.leading + NOTE_TO_TRANSLATION
        for index, line in enumerate(en_lines):
            surface.text(line, x, first + index * t.translation.leading, t.translation)


def _list(surface: Surface, ctx: RenderContext, details: Sequence[Detail], area: Box) -> float:
    """Details one under the other; returns the bottom of the last one."""
    t = ctx.theme.type
    x, width, row = area.x, area.width, area.top
    for detail in details:
        if detail.icon:
            # The felt patch, the name beside it (centred on it, on two lines if needed)
            # and the description under both, across the whole column.
            badge = Box(x, row, BADGE, BADGE)
            surface.patch(ICONS[detail.icon], badge, ctx.theme.palette.felt, _threads(ctx.theme))
            name_x = badge.right + BADGE_TO_TEXT
            names = balanced_lines(detail.name, lambda s: text_width(s, t.item), x + width - name_x)
            cap_to_base = t.item.size * CAP_HEIGHT
            block = cap_to_base + (len(names) - 1) * t.item.leading
            if detail.name_en:
                block += NAME_TO_TRANSLATION
            name = row + (BADGE - block) / 2 + cap_to_base
            for index, line in enumerate(names):
                surface.text(line, name_x, name + index * t.item.leading, t.item)
            if detail.name_en:
                last_name = name + (len(names) - 1) * t.item.leading
                surface.text(detail.name_en, name_x, last_name + NAME_TO_TRANSLATION, t.translation)
            text = badge.bottom + BADGE_TO_DESCRIPTION
            bottom = badge.bottom
        else:
            name = surface.paragraph(detail.name, x, row + t.item.size, width, t.item)
            if detail.name_en:
                name = surface.paragraph(detail.name_en, x, name + NAME_TO_TRANSLATION, width, t.translation)
            text = name + NAME_TO_TEXT
            bottom = name
        if detail.text:
            last = surface.paragraph(detail.text, x, text, width, t.text)
            bottom = last + t.text.leading - t.text.size
        row = bottom + DETAIL_GAP
    return row - DETAIL_GAP


def _grid(surface: Surface, ctx: RenderContext, details: Sequence[Detail], area: Box) -> float:
    """Details two per row, centred in their cell; returns the bottom of the last row."""
    t = ctx.theme.type
    style = t.grid_item

    def measure(text: str) -> float:
        return text_width(text, style)

    cells = columns(area.x, area.right, 2, GRID_GUTTER)
    row = area.top
    for start in range(0, len(details), 2):
        row_bottom = row
        for (cx, cw), detail in zip(cells, details[start : start + 2], strict=False):
            centre = cx + cw / 2
            below = row
            if detail.icon:
                badge = Box(centre - GRID_BADGE / 2, row, GRID_BADGE, GRID_BADGE)
                surface.patch(ICONS[detail.icon], badge, ctx.theme.palette.felt, _threads(ctx.theme))
                below = badge.bottom + GRID_BADGE_TO_NAME
            else:
                below = row + t.grid_item.size
            names = balanced_lines(detail.name, measure, cw)
            for index, line in enumerate(names):
                surface.text(line, centre, below + index * style.leading, style, Align.CENTER)
            last = below + (len(names) - 1) * style.leading
            bottom = last + style.leading - style.size
            if detail.name_en:
                last += NAME_TO_TRANSLATION
                surface.text(detail.name_en, centre, last, t.translation, Align.CENTER)
                bottom = last + t.translation.leading - t.translation.size
            if detail.text:
                lines = surface.lines(detail.text, t.caption, cw)
                first = last + GRID_NAME_TO_TEXT
                for index, line in enumerate(lines):
                    surface.text(line, centre, first + index * t.caption.leading, t.caption, Align.CENTER)
                bottom = first + (len(lines) - 1) * t.caption.leading + t.caption.leading - t.caption.size
            row_bottom = max(row_bottom, bottom)
        row = row_bottom + GRID_ROW_GAP
    return row - GRID_ROW_GAP
