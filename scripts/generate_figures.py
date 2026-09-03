"""Regenerate every probe figure and the design-iteration summary.

Run from the repository root:

    python scripts/generate_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
# Run straight from a clone, whether or not the package has been installed.
sys.path.insert(0, str(ROOT / "src"))

import matplotlib.pyplot as plt

from probe_design import ProbeLayout, plot_layout, save_layout

CONFIG_DIR = ROOT / "configs"
FIGURE_DIR = ROOT / "figures"

ITERATION_ORDER = [
    "lateral_v1",
    "lateral_v2",
    "lateral_final",
    "occipital",
]


def main() -> None:
    FIGURE_DIR.mkdir(exist_ok=True)
    layouts = []

    for stem in ITERATION_ORDER:
        layout = ProbeLayout.from_json(CONFIG_DIR / f"{stem}.json")
        layouts.append(layout)
        path = save_layout(layout, FIGURE_DIR / f"{stem}.png")
        print(f"[figure] {path.relative_to(ROOT)}")
        print(layout.report())

    # Side-by-side comparison of the three lateral iterations.
    lateral = layouts[:3]
    fig, axes = plt.subplots(1, 3, figsize=(19, 4.6))
    for ax, layout in zip(axes, lateral):
        plot_layout(layout, ax=ax)
        ax.get_legend().remove()
    fig.suptitle(
        "Lateral probe design iterations", fontsize=14, fontweight="bold", y=1.02
    )
    fig.tight_layout()
    comparison = FIGURE_DIR / "lateral_iterations.png"
    fig.savefig(comparison, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"[figure] {comparison.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
