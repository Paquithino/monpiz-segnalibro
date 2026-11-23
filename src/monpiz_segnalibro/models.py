"""Content schema of the bookmark.

Strict like the lookbook's and the brochure's: unknown keys are rejected, so a
typo in the YAML fails loudly instead of silently disappearing from the print.
Image paths are relative to the assets directory; :mod:`content` checks that
they exist.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from .icons import IconName

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Meta(_Model):
    title: Text
    author: Text
    subject: str = ""


class Format(_Model):
    """Trimmed size of the card, in millimetres, as quoted by the printer."""

    width_mm: float = Field(gt=0)
    height_mm: float = Field(gt=0)
    bleed_mm: float = Field(3.0, ge=0)


class Hole(_Model):
    """Round hole for the string, centred across the card. Punched by the printer."""

    diameter_mm: float = Field(gt=0, le=10)
    from_top_mm: float = Field(gt=0)  # top edge -> centre of the hole

    @property
    def bottom_mm(self) -> float:
        return self.from_top_mm + self.diameter_mm / 2


class Front(_Model):
    logo: Path  # an SVG: the whole card stays vector (see vector.py for what it may contain)
    logo_width_mm: float = Field(gt=0)  # across the card: the logo is turned on its side

    @field_validator("logo")
    @classmethod
    def _svg(cls, value: Path) -> Path:
        if value.suffix.lower() != ".svg":
            raise ValueError("il logo deve essere un file .svg (vettoriale)")
        return value


class Detail(_Model):
    name: Text
    name_en: str = ""  # bilingual cards: the English name, in italics under the Italian one
    text: str = ""  # description (list) or short line under the name (grid)
    icon: IconName | None = None  # drawn in a yellow circle beside the text (see icons.py)


class QrCode(_Model):
    url: Text
    label: Text


class Back(_Model):
    eyebrow: Text
    title: Text
    title_italic: str = ""
    layout: Literal["list", "grid"] = "list"  # grid: two per row, for three or four details
    details: list[Detail] = Field(min_length=1, max_length=4)
    note: str = ""  # "Non buttare questo cartellino..."
    note_en: str = ""  # bilingual cards: in italics under the note
    divider: Literal["montagne", "trattini", "nessuno"] = "montagne"  # between details and note
    qr: list[QrCode] = Field(default_factory=list, max_length=2)
    footer: str = ""
    footer_en: str = ""  # bilingual cards: second footer line


class Bookmark(_Model):
    meta: Meta
    format: Format
    hole: Hole | None = None
    front: Front
    back: Back

    @model_validator(mode="after")
    def _fits(self) -> Bookmark:
        if self.front.logo_width_mm >= self.format.width_mm:
            raise ValueError("front.logo_width_mm deve essere minore di format.width_mm")
        if self.hole and (
            self.hole.diameter_mm >= self.format.width_mm / 2
            or self.hole.bottom_mm >= self.format.height_mm / 4
        ):
            raise ValueError("il foro è troppo grande o troppo in basso per il formato")
        return self

    def asset_paths(self) -> Iterator[Path]:
        yield self.front.logo
