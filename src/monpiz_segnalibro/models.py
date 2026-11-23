"""Content schema of the bookmark.

Strict like the lookbook's and the brochure's: unknown keys are rejected, so a
typo in the YAML fails loudly instead of silently disappearing from the print.
Image paths are relative to the assets directory; :mod:`content` checks that
they exist.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

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
    logo: Path
    logo_width_mm: float = Field(gt=0)  # across the card: the logo is turned on its side


class Detail(_Model):
    name: Text
    text: Text
    icon: IconName | None = None  # drawn in a yellow circle beside the text (see icons.py)


class QrCode(_Model):
    url: Text
    label: Text


class Back(_Model):
    eyebrow: Text
    title: Text
    title_italic: str = ""
    details: list[Detail] = Field(min_length=1, max_length=4)
    note: str = ""  # "Non buttare questo cartellino..."
    qr: list[QrCode] = Field(default_factory=list, max_length=2)
    footer: str = ""


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
