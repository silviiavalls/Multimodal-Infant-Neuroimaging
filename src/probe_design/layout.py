"""Declarative model of a multimodal probe and its derived channels."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .geometry import distance, is_blocked, midpoint

Modality = Literal["fnirs", "fdcs"]

# Effective layout footprint of each component, in centimetres: the diameter
# of the area it occupies on the probe surface, which for the fDCS optodes is
# set by the housing of the pressure mechanism rather than by the optode
# itself. These are the values used for spacing and clearance, not physical
# optode diameters.
DEFAULT_FOOTPRINTS: dict[str, float] = {
    "electrode": 1.10,
    "fnirs_source": 0.70,
    "fnirs_detector": 1.10,
    "fdcs_source": 1.60,
    "fdcs_detector": 1.60,
}

# Admissible source-detector separation (SDS) per modality, in centimetres.
# Separation sets the depth the measurement is weighted towards: shorter
# separations are dominated by superficial tissue, longer ones carry more
# weight from deeper tissue but return far fewer photons. These windows are
# the ranges adopted for this setup.
DEFAULT_SDS_LIMITS: dict[Modality, tuple[float, float]] = {
    "fnirs": (1.8, 3.0),
    "fdcs": (1.5, 2.0),
}

# Clearance used when testing whether a third component sits too close to the
# line between a source and a detector.
DEFAULT_BUFFERS: dict[Modality, float] = {"fnirs": 0.30, "fdcs": 0.25}


def _plural(count: int, noun: str) -> str:
    """'1 source' / '2 sources'."""
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


@dataclass(frozen=True)
class Channel:
    """A source-detector pair that satisfies the layout constraints."""

    modality: Modality
    source: str
    detector: str
    sds: float
    midpoint: tuple[float, float]

    def __str__(self) -> str:
        return f"{self.source}-{self.detector} ({self.modality}, {self.sds:.2f} cm)"


@dataclass
class ProbeLayout:
    """A flat multimodal probe carrying EEG, fNIRS and fDCS components.

    The layout is fully described by the outline of the probe and the centre
    of every component. Everything else - source-detector separations, which
    pairs are admissible, their midpoints on the probe plane - is derived.
    """

    name: str
    width: float
    height: float
    electrodes: list[list[float]] = field(default_factory=list)
    fnirs_sources: list[list[float]] = field(default_factory=list)
    fnirs_detectors: list[list[float]] = field(default_factory=list)
    fdcs_sources: list[list[float]] = field(default_factory=list)
    fdcs_detectors: list[list[float]] = field(default_factory=list)
    footprints: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_FOOTPRINTS)
    )
    sds_limits: dict[str, tuple[float, float]] = field(
        default_factory=lambda: {k: tuple(v) for k, v in DEFAULT_SDS_LIMITS.items()}
    )
    description: str = ""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    @classmethod
    def from_json(cls, path: str | Path) -> ProbeLayout:
        """Load a layout from a JSON configuration file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        footprints = dict(DEFAULT_FOOTPRINTS) | data.pop("footprints", {})
        sds_limits = {k: tuple(v) for k, v in DEFAULT_SDS_LIMITS.items()}
        sds_limits.update({k: tuple(v) for k, v in data.pop("sds_limits", {}).items()})
        return cls(footprints=footprints, sds_limits=sds_limits, **data)

    # ------------------------------------------------------------------
    # Labelling
    # ------------------------------------------------------------------
    @property
    def labels(self) -> dict[str, list[float]]:
        """Map every component label to its centre.

        Labels follow the convention used throughout the thesis: ``E`` for EEG
        electrodes, ``Sn``/``Dn`` for fNIRS sources and detectors, ``Sc``/``Dc``
        for fDCS sources and detectors.
        """
        mapping: dict[str, list[float]] = {}
        for prefix, points in (
            ("E", self.electrodes),
            ("Sn", self.fnirs_sources),
            ("Dn", self.fnirs_detectors),
            ("Sc", self.fdcs_sources),
            ("Dc", self.fdcs_detectors),
        ):
            for i, point in enumerate(points, start=1):
                mapping[f"{prefix}{i}"] = point
        return mapping

    @property
    def all_positions(self) -> list[list[float]]:
        """Every component centre, used as the obstacle set for clearance tests."""
        return (
            self.electrodes
            + self.fnirs_sources
            + self.fnirs_detectors
            + self.fdcs_sources
            + self.fdcs_detectors
        )

    # ------------------------------------------------------------------
    # Derived quantities
    # ------------------------------------------------------------------
    def distance_between(self, a: str, b: str) -> float:
        """Centre-to-centre distance between two labelled components."""
        labels = self.labels
        return distance(labels[a], labels[b])

    def channels(self, modality: Modality) -> list[Channel]:
        """Every admissible source-detector pair for one modality.

        A pair is admissible when its separation falls inside the modality's
        window and no other component sits within the clearance buffer of the
        line joining the two.
        """
        if modality == "fnirs":
            sources, detectors = self.fnirs_sources, self.fnirs_detectors
            s_prefix, d_prefix = "Sn", "Dn"
        else:
            sources, detectors = self.fdcs_sources, self.fdcs_detectors
            s_prefix, d_prefix = "Sc", "Dc"

        low, high = self.sds_limits[modality]
        buffer = DEFAULT_BUFFERS[modality]
        obstacles = self.all_positions

        found: list[Channel] = []
        for i, source in enumerate(sources, start=1):
            for j, detector in enumerate(detectors, start=1):
                sds = distance(source, detector)
                if not low <= sds <= high:
                    continue
                if is_blocked(source, detector, obstacles, buffer):
                    continue
                found.append(
                    Channel(
                        modality=modality,
                        source=f"{s_prefix}{i}",
                        detector=f"{d_prefix}{j}",
                        sds=sds,
                        midpoint=midpoint(source, detector),
                    )
                )
        return found

    def all_channels(self) -> list[Channel]:
        """Admissible pairs across both optical modalities."""
        return self.channels("fnirs") + self.channels("fdcs")

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def report(self) -> str:
        """Human-readable summary of the layout and its admissible pairs."""
        lines = [
            f"{self.name}  ({self.width} x {self.height} cm)",
            "-" * 56,
            f"EEG           : {_plural(len(self.electrodes), 'electrode')}",
            (
                f"fNIRS optodes : {_plural(len(self.fnirs_sources), 'source')}, "
                f"{_plural(len(self.fnirs_detectors), 'detector')}"
            ),
            (
                f"fDCS optodes  : {_plural(len(self.fdcs_sources), 'source')}, "
                f"{_plural(len(self.fdcs_detectors), 'detector')}"
            ),
            "",
        ]
        for modality in ("fnirs", "fdcs"):
            low, high = self.sds_limits[modality]
            found = self.channels(modality)
            lines.append(
                f"Admissible {modality.upper()} pairs "
                f"(SDS {low}-{high} cm, clearance satisfied): {len(found)}"
            )
            for channel in found:
                mx, my = channel.midpoint
                lines.append(
                    f"  {channel.source:>4s}-{channel.detector:<4s} "
                    f"SDS = {channel.sds:5.2f} cm   "
                    f"midpoint = ({mx:.2f}, {my:.2f})"
                )
            lines.append("")
        return "\n".join(lines)

    def __iter__(self) -> Iterator[Channel]:
        return iter(self.all_channels())
