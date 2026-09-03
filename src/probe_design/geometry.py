"""Geometric primitives for multimodal probe layouts.

All coordinates and distances are expressed in centimetres, in the local
reference frame of a flat probe (origin at the bottom-left corner).

The routines here are two-dimensional geometry on the probe plane. They say
nothing about how light propagates through tissue; they exist to catch layout
conflicts before a design reaches CAD or the printer.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

Point = Sequence[float]


def distance(a: Point, b: Point) -> float:
    """Centre-to-centre Euclidean distance between two components."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def is_blocked(
    a: Point,
    b: Point,
    obstacles: Iterable[Point],
    buffer: float,
) -> bool:
    """Flag a pair whose straight line runs too close to a third component.

    This is a two-dimensional clearance heuristic on the probe plane, not a
    model of photon propagation. A component whose centre sits within
    ``buffer`` centimetres of the segment joining ``a`` and ``b`` leaves too
    little room on the probe surface between that pair, so the pair is
    rejected at the layout stage. Only obstacles whose orthogonal projection
    falls strictly inside the segment are considered; the endpoints
    themselves are ignored.

    Parameters
    ----------
    a, b:
        Centres of the two optodes under test.
    obstacles:
        Centres of every component mounted on the probe.
    buffer:
        Clearance radius in centimetres. Components with a larger footprint
        need a larger buffer.
    """
    x1, y1 = a[0], a[1]
    x2, y2 = b[0], b[1]
    segment_length = math.hypot(x2 - x1, y2 - y1)

    if segment_length == 0:
        return False

    for obstacle in obstacles:
        ox, oy = obstacle[0], obstacle[1]
        if (ox, oy) == (x1, y1) or (ox, oy) == (x2, y2):
            continue

        # Perpendicular distance from the obstacle centre to the line a-b.
        numerator = abs((y2 - y1) * ox - (x2 - x1) * oy + x2 * y1 - y2 * x1)
        perpendicular = numerator / segment_length

        # Normalised projection of the obstacle onto the segment.
        t = ((ox - x1) * (x2 - x1) + (oy - y1) * (y2 - y1)) / segment_length**2

        if 0 < t < 1 and perpendicular < buffer:
            return True

    return False


def midpoint(a: Point, b: Point) -> tuple[float, float]:
    """Midpoint of a source-detector pair on the probe plane.

    Used as a coarse geometric marker for where a pair's measurement area
    falls relative to the probe outline. It is a planar construction, not an
    estimate of the cortical volume the channel is sensitive to.
    """
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
