"""Exact synthetic-layout / LOOM coordinate bridge for M-Journey proofs.

LOOM accepts longitude/latitude but performs its geometric optimization in
Web Mercator metres. The M-Journey seed uses ordinal diagram coordinates, NOT
real geographic coordinates or elapsed time. Transform through the original
schematic.crs functions so solver and diagram axes are genuinely isotropic.

The scale matches the earlier cos(48°) *longitude* seed scale so existing
layouts need not be re-authored. Unlike that approximation, the latitude
mapping is exact at every y coordinate and has a mathematically reversible
inverse. Do not replace solver-produced polylines with elbow geometry.
"""

from __future__ import annotations

import math

from .crs import R, to_mercator, to_wgs84

# This anchor is a synthetic origin for LOOM's input projection, not a claim
# that the equipment-buying journey takes place at longitude 8 / latitude 48.
_SYNTHETIC_ORIGIN = (8.0, 48.0)
_MERCATOR_ORIGIN = to_mercator(_SYNTHETIC_ORIGIN)
_METRES_PER_DIAGRAM_UNIT = (
    R * math.pi / 180 / (2500 * math.cos(math.radians(_SYNTHETIC_ORIGIN[1])))
)


def to_solver_point(point: tuple[float, float]) -> tuple[float, float]:
    """Turn an ordinal diagram point into synthetic WGS84 LOOM input."""
    x, y = point
    ox, oy = _MERCATOR_ORIGIN
    return to_wgs84(
        (ox + x * _METRES_PER_DIAGRAM_UNIT,
         oy + y * _METRES_PER_DIAGRAM_UNIT)
    )


def from_solver_point(point: tuple[float, float]) -> tuple[float, float]:
    """Undo synthetic coordinates after LOOM, in the original metric plane."""
    mx, my = to_mercator(point)
    ox, oy = _MERCATOR_ORIGIN
    return ((mx - ox) / _METRES_PER_DIAGRAM_UNIT,
            (my - oy) / _METRES_PER_DIAGRAM_UNIT)
