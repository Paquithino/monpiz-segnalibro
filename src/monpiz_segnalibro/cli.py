"""Command line: ``build``, ``watch`` and ``check``."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .builder import BuildOptions, build
from .content import load_bookmark
from .errors import ContentError
from .watch import watch

DEFAULT_CONTENT = Path("content/segnalibro.yaml")
DEFAULT_ASSETS = Path("assets")
DEFAULT_OUTPUT = Path("dist/MonPiz-Segnalibro.pdf")
PREVIEW_OUTPUT = Path("dist/MonPiz-Segnalibro-anteprima.pdf")
VECTOR_SUFFIX = "-vettoriale"  # MonPiz-Segnalibro.pdf -> MonPiz-Segnalibro-vettoriale.pdf


def _add_content_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("--content", type=Path, default=DEFAULT_CONTENT)
    command.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)


def _add_output_args(command: argparse.ArgumentParser, output: Path) -> None:
    command.add_argument("-o", "--output", type=Path, default=output)
    command.add_argument("--marks", action="store_true", help="segni di taglio")
    command.add_argument(
        "--guides", action="store_true", help="rifilo, area di sicurezza e foro (solo bozza)"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="monpiz-segnalibro", description="Cartellino segnalibro MonPiz")
    commands = parser.add_subparsers(dest="command", required=True)

    build_cmd = commands.add_parser(
        "build", help="genera il PDF da stampa e la copia vettoriale con i testi in tracciati"
    )
    _add_content_args(build_cmd)
    _add_output_args(build_cmd, DEFAULT_OUTPUT)
    build_cmd.add_argument("--no-bleed", action="store_true", help="senza abbondanza: come apparirà rifilato")
    build_cmd.add_argument(
        "--no-vector", action="store_true", help=f"senza la copia <nome>{VECTOR_SUFFIX}.pdf"
    )

    watch_cmd = commands.add_parser("watch", help="anteprima: rigenera il PDF a ogni modifica salvata")
    _add_content_args(watch_cmd)
    _add_output_args(watch_cmd, PREVIEW_OUTPUT)
    watch_cmd.add_argument("--bleed", action="store_true", help="con abbondanza (default: già rifilato)")

    check_cmd = commands.add_parser("check", help="valida contenuti, logo e font")
    _add_content_args(check_cmd)
    return parser


def _options(args: argparse.Namespace, *, bleed: bool, vector: bool) -> BuildOptions:
    output: Path = args.output
    return BuildOptions(
        content_file=args.content,
        assets_dir=args.assets,
        output=output,
        vector_output=output.with_stem(output.stem + VECTOR_SUFFIX) if vector else None,
        bleed=bleed,
        marks=args.marks,
        guides=args.guides,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "check":
            fmt = load_bookmark(args.content, args.assets).format
            print(f"Contenuti validi. Formato {fmt.width_mm:g} x {fmt.height_mm:g} mm.")
            return 0
        if args.command == "watch":
            watch(_options(args, bleed=args.bleed, vector=False))
            return 0
        result = build(_options(args, bleed=not args.no_bleed, vector=not args.no_vector))
    except ContentError as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:  # Ctrl+C ends the watch
        return 0

    width, height = result.size_mm
    for output in result.outputs:
        kind = "vettoriale, testi in tracciati" if output.outlined else "testi con font incorporati"
        print(f"{output.path} ({output.size_bytes / 1_000:.0f} kB, {kind})")
    print(f"Formato {width:g} x {height:g} mm, fronte e retro.")
    return 0
