"""Back: the hats' details, the invitation to keep the card as a bookmark, the QR codes.

The heading sits at the top and the QR codes with the footer on the bottom
margin; in between, details, divider and note share the free height in equal
gaps, so the blocks keep their proportions whatever the texts. Content that
does not fit stops the build with a message instead of overlapping.

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
from ..surface import Align, MeasuringSurface, Surface, text_width
from ..theme import Theme
from ..vector import load_svg
from .base import RenderContext

EYEBROW_TO_TITLE = 19.0
TITLE_TO_DASHES = 11.0
DASHES = (3.4, 2.2)  # on, off: the rhythm of the logo's dashed arrow
DASH_WIDTH = 2.2
DASH_LENGTH = mm(9.5)
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
SKYLINE_HEIGHT = mm(7.0)  # across the whole column, like the lookbook's skyline
SKYLINE_WIDTH = 1.0
MIN_GAP = 10.0  # least air between the middle blocks
NOTE_SIGN = mm(8.5)  # recycling sign on the right of the note
NOTE_SIGN_TO_TEXT = mm(2.5)
X_HEIGHT = 0.5  # Fraunces lowercase body, share of the size: where a line visibly starts
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

        # Bottom, from the margin up: footer, QR labels, QR codes.
        bottom = surface.height - g.margin
        footers = [line for line in (self.back.footer, self.back.footer_en) if line]
        for index, line in enumerate(footers):
            surface.text(line, x, bottom - (len(footers) - 1 - index) * t.small.leading, t.small)
        label = bottom - (len(footers) - 1) * t.small.leading - LABEL_TO_FOOTER if footers else bottom
        bottom_start = label - t.label.size  # top of the labels, without QR codes
        if self.back.qr:
            qr_bottom = label - QR_TO_LABEL
            for (cx, cw), code in zip(columns(x, x + width, 2, g.gutter), self.back.qr, strict=False):
                side = min(QR_SIDE, cw)
                surface.qr(code.url, Box(cx, qr_bottom - side, side, side), p.ink)
                surface.text(code.label, cx, label, t.label)
            bottom_start = qr_bottom - QR_SIDE

        # Middle, justified: details, divider, note. The free height is shared out in equal
        # gaps (title dashes -> details -> divider -> note -> QR codes), so the blocks keep
        # the same rhythm whatever the texts; measured first with a dry run of the details.
        place_details = _grid if self.back.layout == "grid" else _list
        details_height = place_details(
            MeasuringSurface(surface), ctx, self.back.details, Box(x, 0.0, width, 0.0)
        )
        divider_height = {"montagne": SKYLINE_HEIGHT, "trattini": DASH_WIDTH, "nessuno": 0.0}[
            self.back.divider
        ]
        note = _Note(self.back, ctx, surface, width)
        blocks = (
            [details_height, divider_height, note.height] if divider_height else [details_height, note.height]
        )
        start = dashes + DASH_WIDTH / 2
        room = bottom_start - start
        gap = (room - sum(blocks)) / (len(blocks) + 1)
        if gap < MIN_GAP:
            missing = (MIN_GAP - gap) * (len(blocks) + 1)
            raise ContentError(
                f"Il retro non sta nel formato: mancano {missing / mm(1):.1f} mm. "
                "Accorcia i testi (back.details, back.note), togli il divisore "
                "(back.divider: nessuno) o un QR."
            )

        top = start + gap
        place_details(surface, ctx, self.back.details, Box(x, top, width, 0.0))
        top += details_height + gap
        if self.back.divider == "montagne":
            surface.polyline(place(SKYLINE, x, top, width, SKYLINE_HEIGHT), p.yellow, SKYLINE_WIDTH)
        elif self.back.divider == "trattini":  # the same yellow dashes as under the title
            surface.hline(x, x + DASH_LENGTH, top + DASH_WIDTH / 2, p.yellow, DASH_WIDTH, dash=DASHES)
        if divider_height:
            top += divider_height + gap
        note.draw(top)


class _Note:
    """The "reuse me" note, its English line, and a flat sign on their right if set.

    Its top is the top of the sign or of the first line's lowercase body, so the
    gaps around it look even on the page.
    """

    def __init__(self, back: Back, ctx: RenderContext, surface: Surface, width: float) -> None:
        t = ctx.theme.type
        self._back, self._ctx, self._surface = back, ctx, surface
        self._x = ctx.theme.grid.margin
        self._patch = NOTE_SIGN if back.note_sign else 0.0
        # Text on the left margin like every other block, the patch on the right edge.
        self._text_x = self._x
        self._patch_x = self._x + width - self._patch
        text_width_ = width - (self._patch + NOTE_SIGN_TO_TEXT if back.note_sign else 0.0)
        self._lines = surface.lines(back.note, t.note, text_width_) if back.note else []
        self._en = surface.lines(back.note_en, t.translation, text_width_) if back.note_en else []
        text = 0.0
        if self._lines:
            text = t.note.size * X_HEIGHT + (len(self._lines) - 1) * t.note.leading  # to the last baseline
        if self._en:
            text += NOTE_TO_TRANSLATION + (len(self._en) - 1) * t.translation.leading
        self._text = text
        self.height = max(self._patch, text)

    def draw(self, top: float) -> None:
        t, p = self._ctx.theme.type, self._ctx.theme.palette
        if self._back.note_sign:
            patch = Box(self._patch_x, top + (self.height - self._patch) / 2, self._patch, self._patch)
            sign = load_svg(self._ctx.assets_dir / self._back.note_sign)
            self._surface.artwork(sign, patch, p.accent)  # in the colour of the note
        first = top + (self.height - self._text) / 2 + t.note.size * X_HEIGHT
        for index, line in enumerate(self._lines):
            self._surface.text(line, self._text_x, first + index * t.note.leading, t.note)
        last = first + (len(self._lines) - 1) * t.note.leading
        for index, line in enumerate(self._en):
            self._surface.text(
                line, self._text_x, last + NOTE_TO_TRANSLATION + index * t.translation.leading, t.translation
            )


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
