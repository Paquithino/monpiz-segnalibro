"""Design tokens: palette, typography and grid.

Palette and typefaces are the lookbook's and the brochure's, plus the yellow
of the logo (RGB 243-189-72, Pantone 142 C), used only for graphic accents
(on cream paper it is too light for text), and the felt and threads of the
embroidered patches. Type sizes are re-cut for a column 37 mm wide instead
of scaling the brochure's ones, which would make the running text too small
to read. All measurements are in points.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from reportlab.lib.colors import Color, HexColor

from .geometry import mm


class Font(StrEnum):
    """Font names as registered in ReportLab (see :mod:`fonts`)."""

    DISPLAY = "Fraunces-Display"
    DISPLAY_ITALIC = "Fraunces-DisplayItalic"
    SERIF = "Fraunces-Text"
    SANS = "Inter-Regular"


@dataclass(frozen=True, slots=True)
class Palette:
    ink: Color
    body: Color
    muted: Color
    accent: Color  # olive: small capitals, italic lines
    paper: Color
    rule: Color
    yellow: Color  # the logo's arrow: dashes, mountain line, yellow thread
    felt: Color  # the patches of the details: the dark grey felt of the hats
    thread_cream: Color
    thread_blue: Color  # the small marks embroidered above the peaks


@dataclass(frozen=True, slots=True)
class TextStyle:
    font: Font
    size: float
    leading: float
    color: Color
    tracking: float = 0.0
    uppercase: bool = False


@dataclass(frozen=True, slots=True)
class Typography:
    eyebrow: TextStyle  # spaced capitals above the title
    title: TextStyle
    title_italic: TextStyle  # second line of the title, for contrast
    item: TextStyle  # name of a detail
    text: TextStyle  # description of a detail
    note: TextStyle  # "usalo come segnalibro"
    label: TextStyle  # captions under the QR codes
    small: TextStyle  # footer


@dataclass(frozen=True, slots=True)
class Grid:
    margin: float = mm(5.0)  # trim edge -> content
    gutter: float = mm(4.0)


@dataclass(frozen=True, slots=True)
class Theme:
    palette: Palette
    type: Typography
    grid: Grid


def default_theme() -> Theme:
    p = Palette(
        ink=HexColor("#24291F"),
        body=HexColor("#4B5245"),
        muted=HexColor("#6A6E5E"),
        accent=HexColor("#6D6F2E"),
        paper=HexColor("#EFECE2"),
        rule=HexColor("#CFC9B6"),
        yellow=HexColor("#F3BD48"),
        felt=HexColor("#34362F"),
        thread_cream=HexColor("#EFE6CF"),
        thread_blue=HexColor("#7FA8C9"),
    )
    t = Typography(
        eyebrow=TextStyle(Font.SANS, 5.4, 7.0, p.accent, tracking=1.3, uppercase=True),
        title=TextStyle(Font.DISPLAY, 17.0, 18.0, p.ink),
        title_italic=TextStyle(Font.DISPLAY_ITALIC, 12.5, 14.5, p.accent),
        item=TextStyle(Font.SERIF, 9.0, 11.0, p.ink),
        text=TextStyle(Font.SANS, 6.6, 9.4, p.body),
        note=TextStyle(Font.DISPLAY_ITALIC, 9.6, 12.0, p.accent),
        label=TextStyle(Font.SANS, 5.4, 7.0, p.ink),
        small=TextStyle(Font.SANS, 5.4, 7.0, p.muted),
    )
    return Theme(palette=p, type=t, grid=Grid())
