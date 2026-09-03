"""Rendering of probe layouts to publication-quality figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from .layout import ProbeLayout

# Colour scheme kept consistent with the figures in the thesis.
COLORS: dict[str, str] = {
    "electrode": "#e63946",
    "fnirs_detector": "#6495ed",
    "fnirs_source": "#008b8b",
    "fdcs_detector": "#c71585",
    "fdcs_source": "#ff69b4",
}

LEGEND_LABELS: dict[str, str] = {
    "electrode": "EEG electrode (E)",
    "fnirs_detector": "fNIRS detector (Dn)",
    "fnirs_source": "fNIRS source (Sn)",
    "fdcs_detector": "fDCS detector (Dc)",
    "fdcs_source": "fDCS source (Sc)",
}


def plot_layout(
    layout: ProbeLayout,
    show_midpoints: bool = True,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Draw a probe layout to scale, with admissible-pair midpoints marked."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4.5))

    ax.add_patch(
        plt.Rectangle(
            (0, 0),
            layout.width,
            layout.height,
            fill=False,
            edgecolor="black",
            linewidth=1.5,
        )
    )

    def draw(points, kind, prefix):
        radius = layout.footprints[kind] / 2
        for i, point in enumerate(points, start=1):
            ax.add_patch(plt.Circle(point, radius, color=COLORS[kind], alpha=0.65))
            ax.text(
                point[0],
                point[1],
                f"{prefix}{i}",
                ha="center",
                va="center",
                fontsize=8,
                color="white",
                fontweight="bold",
            )

    draw(layout.electrodes, "electrode", "E")
    draw(layout.fnirs_detectors, "fnirs_detector", "Dn")
    draw(layout.fnirs_sources, "fnirs_source", "Sn")
    draw(layout.fdcs_detectors, "fdcs_detector", "Dc")
    draw(layout.fdcs_sources, "fdcs_source", "Sc")

    if show_midpoints:
        for channel in layout.channels("fnirs"):
            ax.plot(*channel.midpoint, "x", color="navy", markersize=7, mew=2)
        for channel in layout.channels("fdcs"):
            ax.plot(*channel.midpoint, "x", color="magenta", markersize=7, mew=2)

    ax.set_aspect("equal", "box")
    ax.set_xlim(-1, layout.width + 1)
    ax.set_ylim(-0.5, layout.height + 0.5)
    ax.set_xlabel("Position X (cm)")
    ax.set_ylabel("Position Y (cm)")
    ax.set_title(layout.name, fontsize=11, fontweight="bold")

    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label=LEGEND_LABELS[kind],
            markerfacecolor=COLORS[kind],
            markersize=10,
        )
        for kind in LEGEND_LABELS
    ]
    handles.append(
        Line2D(
            [0],
            [0],
            marker="x",
            color="navy",
            label="Pair midpoint",
            linestyle="none",
            markersize=8,
        )
    )
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=8)
    return ax


def save_layout(layout: ProbeLayout, path: str | Path, dpi: int = 200) -> Path:
    """Render a layout and write it to disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    plot_layout(layout, ax=ax)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path
