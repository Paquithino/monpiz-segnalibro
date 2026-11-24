"""End-to-end: the real content validates and renders a two-page PDF; bad content fails clearly."""

import re
from pathlib import Path

import pytest
from pypdf import PdfReader

from monpiz_segnalibro.builder import BuildOptions, build
from monpiz_segnalibro.content import load_bookmark
from monpiz_segnalibro.errors import ContentError
from monpiz_segnalibro.faces import RenderContext
from monpiz_segnalibro.geometry import mm
from monpiz_segnalibro.theme import default_theme

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "segnalibro.yaml"
ASSETS = ROOT / "assets"


def _page_streams(path: Path) -> bytes:
    """The decoded drawing operators of every page."""
    streams = [page.get_contents() for page in PdfReader(path).pages]
    return b"\n".join(stream.get_data() for stream in streams if stream is not None)


def _variant(tmp_path: Path, old: str, new: str) -> Path:
    text = CONTENT.read_text(encoding="utf-8")
    assert old in text, f"{old!r} non è in {CONTENT.name}: aggiorna il test"
    variant = tmp_path / "segnalibro.yaml"
    variant.write_text(text.replace(old, new), encoding="utf-8")
    return variant


def test_content_is_valid() -> None:
    bookmark = load_bookmark(CONTENT, ASSETS)
    assert (bookmark.format.width_mm, bookmark.format.height_mm) == (47, 150)


def test_missing_image_is_reported(tmp_path: Path) -> None:
    broken = _variant(tmp_path, "images/logo-giallo.svg", "images/nope.svg")
    with pytest.raises(ContentError, match=re.escape("images/nope.svg")):
        load_bookmark(broken, ASSETS)


def test_unknown_key_is_rejected(tmp_path: Path) -> None:
    broken = _variant(tmp_path, "  footer:", "  fotoer:")
    with pytest.raises(ContentError, match="fotoer"):
        load_bookmark(broken, ASSETS)


def test_build_writes_front_and_back(tmp_path: Path) -> None:
    output = tmp_path / "segnalibro.pdf"
    result = build(BuildOptions(CONTENT, ASSETS, output, marks=True, guides=True))
    data = output.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(re.findall(rb"/Type /Page\b", data)) == 2
    assert b"/TrimBox" in data and b"/BleedBox" in data
    assert result.size_mm == (47, 150)


def test_text_that_does_not_fit_stops_the_build(tmp_path: Path) -> None:
    long_note = "note: " + " ".join(["Riutilizzami come segnalibro."] * 12)
    broken = _variant(tmp_path, 'note: "Il viaggio continua\\ntra le pagine:\\nriutilizzami come\\nsegnalibro."', long_note)
    with pytest.raises(ContentError, match="non sta nel formato"):
        build(BuildOptions(broken, ASSETS, tmp_path / "out.pdf"))


def test_artwork_starts_below_the_hole() -> None:
    bookmark = load_bookmark(CONTENT, ASSETS)
    assert bookmark.hole is not None
    theme = default_theme()
    with_hole = RenderContext(theme, ASSETS, bookmark.hole)
    without = RenderContext(theme, ASSETS, None)
    assert without.content_top == theme.grid.margin
    assert with_hole.content_top > mm(bookmark.hole.bottom_mm)


def test_back_is_bilingual() -> None:
    back = load_bookmark(CONTENT, ASSETS).back
    assert all(detail.name_en for detail in back.details)
    assert back.note_en and back.footer_en and back.note_sign == Path("images/riciclo.svg")


def test_vector_copy_has_no_images_and_no_fonts(tmp_path: Path) -> None:
    output, vector = tmp_path / "segnalibro.pdf", tmp_path / "segnalibro-vettoriale.pdf"
    result = build(BuildOptions(CONTENT, ASSETS, output, vector_output=vector))
    assert [o.outlined for o in result.outputs] == [False, True]
    standard, outlined = output.read_bytes(), vector.read_bytes()
    for path, data in ((output, standard), (vector, outlined)):
        assert b"/Subtype /Image" not in data  # the logo is paths, not pixels
        assert b"0 0 0 1 k" in _page_streams(path)  # ... and keeps its pure K black
    assert b"/FontFile2" in standard
    assert b"/BaseFont" not in outlined  # ReportLab keeps an empty /Font dictionary, nothing in it
