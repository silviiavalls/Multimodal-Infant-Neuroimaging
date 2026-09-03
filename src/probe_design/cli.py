"""Command-line interface: inspect and render probe configurations.

Examples
--------
    probe-design report configs/lateral_final.json
    probe-design plot configs/lateral_final.json -o figures/lateral_final.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .layout import ProbeLayout
from .plotting import save_layout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="probe-design",
        description="Inspect and render multimodal EEG/fNIRS/fDCS probe layouts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    report = sub.add_parser("report", help="print SDS and admissible pairs")
    report.add_argument("config", type=Path, help="path to a layout JSON file")

    plot = sub.add_parser("plot", help="render the layout to an image")
    plot.add_argument("config", type=Path, help="path to a layout JSON file")
    plot.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output image path (default: figures/<config stem>.png)",
    )
    plot.add_argument("--dpi", type=int, default=200, help="output resolution")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    layout = ProbeLayout.from_json(args.config)

    if args.command == "report":
        print(layout.report())
        return 0

    output = args.output or Path("figures") / f"{args.config.stem}.png"
    save_layout(layout, output, dpi=args.dpi)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
