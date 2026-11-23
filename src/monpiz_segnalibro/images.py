"""Image preparation: the logo, resampled to the output resolution.

ReportLab only places the pixels, so the PDF stays light whatever the size of
the source file; transparency is kept, the logo sits straight on the paper.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image
from reportlab.lib.utils import ImageReader

POINTS_PER_INCH = 72.0


class ImageLibrary:
    def __init__(self, assets_dir: Path, dpi: int) -> None:
        if dpi <= 0:
            raise ValueError("dpi must be positive")
        self._assets_dir = assets_dir
        self._dpi = dpi

    def size(self, path: Path) -> tuple[int, int]:
        """Pixel size of an asset, without decoding it."""
        with Image.open(self._assets_dir / path) as image:
            return image.size

    def effective_dpi(self, path: Path, width_pt: float) -> float:
        """Resolution the asset prints at when ``width_pt`` wide."""
        return self.size(path)[0] / width_pt * POINTS_PER_INCH

    def fitted(self, path: Path, width_pt: float, height_pt: float) -> ImageReader:
        """The whole image (transparency kept), downscaled to the output DPI, never upscaled."""
        with Image.open(self._assets_dir / path) as source:
            image = source.convert("RGBA")
        target = (
            max(1, round(width_pt / POINTS_PER_INCH * self._dpi)),
            max(1, round(height_pt / POINTS_PER_INCH * self._dpi)),
        )
        if target[0] < image.width and target[1] < image.height:
            image = image.resize(target, Image.Resampling.LANCZOS, reducing_gap=3.0)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        return ImageReader(buffer)
