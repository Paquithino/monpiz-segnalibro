"""The minimal SVG reader behind the vector logo."""

from pathlib import Path

import pytest

from monpiz_segnalibro.errors import ContentError
from monpiz_segnalibro.vector import load_svg, parse_path

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def test_relative_and_shorthand_commands_become_absolute() -> None:
    commands = parse_path("m 10 10 h 5 v 5 l -5 0 c 0 -1 1 -2 2 -2 s 2 1 2 2 z")
    assert commands == (
        ("M", (10.0, 10.0)),
        ("L", (15.0, 10.0)),
        ("L", (15.0, 15.0)),
        ("L", (10.0, 15.0)),
        ("C", (10.0, 14.0, 11.0, 13.0, 12.0, 13.0)),
        ("C", (13.0, 13.0, 14.0, 14.0, 14.0, 15.0)),
        ("Z", ()),
    )


def test_extra_pairs_after_a_move_are_lines() -> None:
    assert parse_path("M0 0 10 0 10 10") == (("M", (0.0, 0.0)), ("L", (10.0, 0.0)), ("L", (10.0, 10.0)))


def test_logo_keeps_its_print_colours() -> None:
    logo = load_svg(ASSETS / "images" / "logo-giallo.svg")
    assert logo.aspect == pytest.approx(2.3, abs=0.01)
    assert {path.cmyk for path in logo.paths} == {(0, 0, 0, 1), (0.035, 0.273, 0.813, 0)}


def test_unsupported_svg_is_rejected(tmp_path: Path) -> None:
    svg = tmp_path / "logo.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="5" height="5"/></svg>'
    )
    with pytest.raises(ContentError, match="rect"):
        load_svg(svg)
