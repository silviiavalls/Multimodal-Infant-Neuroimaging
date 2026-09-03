"""Computational design and geometric validation of multimodal EEG / fNIRS / fDCS probes.

Developed for the Bachelor's Thesis "Development of a multimodal strategy to
investigate speech processing mechanisms in infants" (Universitat Pompeu Fabra,
2024/2025).
"""

from .geometry import distance, is_blocked, midpoint
from .layout import Channel, ProbeLayout
from .plotting import plot_layout, save_layout

__version__ = "1.0.0"
__all__ = [
    "Channel",
    "ProbeLayout",
    "distance",
    "is_blocked",
    "midpoint",
    "plot_layout",
    "save_layout",
]
