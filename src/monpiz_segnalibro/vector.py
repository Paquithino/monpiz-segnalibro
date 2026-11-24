"""Vector artwork from SVG files: just enough SVG for a logo exported from Illustrator.

Supported: ``<path>`` elements with ``d`` (M, L, H, V, C, S, Z, absolute and
relative), ``fill`` as ``#rrggbb``, ``fill-rule`` and two print attributes:
``data-cmyk`` ("c m y k", 0..1), which wins over ``fill`` so the PDF keeps the
brand's CMYK values instead of a conversion, and ``data-spot`` (e.g.
"PANTONE 7747 C"), which makes the colour a spot ink with ``data-cmyk`` as its
process alternate, as in the brand's own files.
Anything else (transforms, strokes, gradients, text, images) is rejected
with a clear message rather than drawn wrong: flatten it in the source file.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .errors import ContentError

SVG = "{http://www.w3.org/2000/svg}"
DRAWABLE = {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "image", "use"}
UNSUPPORTED_ATTRIBUTES = {"transform", "stroke", "opacity", "fill-opacity", "clip-path", "mask", "style"}

Point = tuple[float, float]
# Absolute, normalised commands: ("M", (x, y)), ("L", (x, y)), ("C", (x1, y1, x2, y2, x, y)), ("Z", ()).
Command = tuple[str, tuple[float, ...]]

_TOKEN = re.compile(r"[MmLlHhVvCcSsZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_ARITY = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Z": 0}


@dataclass(frozen=True, slots=True)
class VectorPath:
    commands: tuple[Command, ...]
    rgb: str  # "#rrggbb", for screen
    cmyk: tuple[float, float, float, float] | None  # for print, when the source says so
    spot: str | None  # spot ink name; cmyk is then its process alternate
    even_odd: bool


@dataclass(frozen=True, slots=True)
class VectorArtwork:
    """Paths in the coordinates of the SVG viewBox (origin top-left, y downwards)."""

    x: float
    y: float
    width: float
    height: float
    paths: tuple[VectorPath, ...]

    @property
    def aspect(self) -> float:
        return self.width / self.height


def parse_path(d: str) -> tuple[Command, ...]:
    """Normalise SVG path data to absolute M / L / C / Z."""
    tokens = _TOKEN.findall(d)
    commands: list[Command] = []
    index, op = 0, ""
    x = y = start_x = start_y = 0.0
    last_control: Point | None = None  # second control point of the previous curve, for S

    while index < len(tokens):
        if tokens[index].isalpha():
            op = tokens[index]
            index += 1
        elif not op:
            raise ValueError("i dati del tracciato non iniziano con un comando")
        upper, relative = op.upper(), op.islower()
        arity = _ARITY[upper]
        args = [float(value) for value in tokens[index : index + arity]]
        if len(args) < arity:
            raise ValueError(f"comando {op} incompleto")
        index += arity
        dx, dy = (x, y) if relative else (0.0, 0.0)

        if upper == "M":
            x, y = args[0] + dx, args[1] + dy
            start_x, start_y = x, y
            commands.append(("M", (x, y)))
            op = "l" if relative else "L"  # extra pairs after a move are lines
            last_control = None
        elif upper in "LHV":
            if upper == "H":
                x = args[0] + dx
            elif upper == "V":
                y = args[0] + dy
            else:
                x, y = args[0] + dx, args[1] + dy
            commands.append(("L", (x, y)))
            last_control = None
        elif upper in "CS":
            if upper == "C":
                x1, y1 = args[0] + dx, args[1] + dy
                rest = args[2:]
            else:  # S: first control point mirrors the previous curve's second one
                x1, y1 = (2 * x - last_control[0], 2 * y - last_control[1]) if last_control else (x, y)
                rest = args
            x2, y2 = rest[0] + dx, rest[1] + dy
            x, y = rest[2] + dx, rest[3] + dy
            commands.append(("C", (x1, y1, x2, y2, x, y)))
            last_control = (x2, y2)
        else:  # Z
            commands.append(("Z", ()))
            x, y = start_x, start_y
            last_control = None
            op = ""  # numbers right after Z are an error
    return tuple(commands)


def _colour(value: str, where: str) -> str:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise ContentError(f"{where}: fill deve essere #rrggbb, trovato {value!r}")
    return value.upper()


def _cmyk(value: str | None, where: str) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    parts = [float(part) for part in value.split()]
    if len(parts) != 4 or not all(0.0 <= part <= 1.0 for part in parts):
        raise ContentError(f"{where}: data-cmyk vuole quattro valori tra 0 e 1, trovato {value!r}")
    return parts[0], parts[1], parts[2], parts[3]


def load_svg(path: Path) -> VectorArtwork:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ContentError(f"SVG non leggibile: {path} ({exc})") from exc
    try:
        x, y, width, height = (float(value) for value in root.attrib["viewBox"].replace(",", " ").split())
    except (KeyError, ValueError) as exc:
        raise ContentError(f"{path}: serve un viewBox con quattro numeri") from exc

    paths: list[VectorPath] = []
    for number, element in enumerate(root.iter(), start=1):
        tag = element.tag.removeprefix(SVG)
        if tag in DRAWABLE - {"path"}:
            raise ContentError(f"{path}: <{tag}> non supportato, converti tutto in tracciati")
        bad = UNSUPPORTED_ATTRIBUTES & element.attrib.keys()
        if bad:
            raise ContentError(f"{path}: attributi non supportati {sorted(bad)}, appiattisci il file")
        if tag != "path":
            continue
        where = f"{path.name}, tracciato {number}"
        try:
            commands = parse_path(element.attrib["d"])
        except (KeyError, ValueError) as exc:
            raise ContentError(f"{where}: dati del tracciato non validi ({exc})") from exc
        cmyk = _cmyk(element.attrib.get("data-cmyk"), where)
        spot = element.attrib.get("data-spot")
        if spot is not None and cmyk is None:
            raise ContentError(
                f"{where}: data-spot vuole anche data-cmyk, il colore alternativo in quadricromia"
            )
        paths.append(
            VectorPath(
                commands=commands,
                rgb=_colour(element.attrib.get("fill", "#000000"), where),
                cmyk=cmyk,
                spot=spot,
                even_odd=element.attrib.get("fill-rule") == "evenodd",
            )
        )
    if not paths:
        raise ContentError(f"{path}: nessun tracciato da disegnare")
    return VectorArtwork(x, y, width, height, tuple(paths))
