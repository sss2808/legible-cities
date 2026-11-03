"""Stage-constrained System *category guide* geometry.

All nodes remain canonical research moments. This module changes only
presentation y-coordinates inside the same ten ordinal stages and the
0/45/90-degree bend vertices on the existing category guides. Relationship
edges, line memberships, ordering and IDs are never created or rewritten.

Cross-category source-edge density is a spacing *demand signal*, never a
transfer, confirmed customer trip, or line-to-line interchange.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

Coord = tuple[float, float]
EPS = 1e-6


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def spacing_by_stage(
    moments: dict[str, dict[str, Any]],
    connections: dict[str, dict[str, Any]],
    ordered_stages: list[dict[str, Any]],
    ordered_layers: list[dict[str, Any]],
    *,
    baseline_gap: float = 104.0,
) -> tuple[dict[tuple[str, str], float], list[dict[str, Any]]]:
    """Allocate six intercategory corridors based on real source connections.

    Demand counts each authored cross-category relationship once in every
    touched operational stage. No source edge becomes a display guide.
    The six gaps have a fixed combined height, so high-demand gaps gain space
    at the expense of lower-demand gaps without expanding the full SVG field.
    """
    if not ordered_layers or not ordered_stages:
        raise ValueError("source stages and layers are required")
    ranks = {l["id"]: i for i, l in enumerate(ordered_layers)}
    n = len(ordered_layers)
    centers: dict[tuple[str, str], float] = {}
    summary = []
    for stage in ordered_stages:
        demand = [0] * max(0, n - 1)
        stage_id = stage["id"]
        for relation in connections.values():
            a, b = moments[relation["fromId"]], moments[relation["toId"]]
            if stage_id not in (a["stageId"], b["stageId"]):
                continue
            lo, hi = sorted((ranks[a["layerId"]], ranks[b["layerId"]]))
            for k in range(lo, hi):
                demand[k] += 1
        if demand:
            avg = sum(demand) / len(demand)
            adjustments = [_clamp((d - avg) * 5.0, -16, 16) for d in demand]
            # Preserve the same overall vertical extent regardless of how
            # many cross-category relationships this stage contains.
            bias = sum(adjustments) / len(adjustments)
            gaps = [baseline_gap + (delta - bias) for delta in adjustments]
            if min(gaps) < baseline_gap - 33 or max(gaps) > baseline_gap + 33:
                raise ValueError("stage corridor gaps exceed bounded range")
            offsets = [0.0]
            for gap in gaps:
                offsets.append(offsets[-1] + gap)
            vertical_center = (offsets[0] + offsets[-1]) / 2
            ys = [150 + (n - 1) * baseline_gap / 2 + (p - vertical_center)
                  for p in offsets]
        else:
            gaps = []
            ys = [150]
        for layer, y in zip(ordered_layers, ys):
            centers[(layer["id"], stage_id)] = round(y, 7)
        summary.append({
            "stageId": stage_id,
            "crossCategoryDemand": demand,
            "gaps": [round(g, 3) for g in gaps],
            "minGap": round(min(gaps), 3) if gaps else None,
            "maxGap": round(max(gaps), 3) if gaps else None,
            "overallGapSpan": round(sum(gaps), 3),
        })
    return centers, summary


def _simplify(points: list[Coord]) -> list[Coord]:
    out: list[Coord] = []
    for point in points:
        if not out or math.dist(point, out[-1]) > EPS:
            out.append(point)
    i = 1
    while i + 1 < len(out):
        a, b, c = out[i - 1:i + 2]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (
            b[1] - a[1]) * (c[0] - b[0])
        dot = (b[0] - a[0]) * (c[0] - b[0]) + (
            b[1] - a[1]) * (c[1] - b[1])
        if abs(cross) < EPS and dot >= -EPS:
            out.pop(i)
        else:
            i += 1
    return out


def centered_step(
    source: Coord, target: Coord, *, before_fraction: float = 0.5,
) -> list[Coord]:
    """Connect endpoints through a centered H-45-H or V-45-V step."""
    x0, y0 = source
    x1, y1 = target
    dx, dy = x1 - x0, y1 - y0
    sx = 1 if dx >= 0 else -1
    sy = 1 if dy >= 0 else -1
    f = _clamp(before_fraction, 0.0, 1.0)
    if abs(dx) >= abs(dy):
        extra = abs(dx) - abs(dy)
        p = (x0 + sx * extra * f, y0)
        q = (p[0] + sx * abs(dy), y1)
    else:
        extra = abs(dy) - abs(dx)
        p = (x0, y0 + sy * extra * f)
        q = (x1, p[1] + sy * abs(dx))
    return _simplify([source, p, q, target])


def is_octilinear(points: list[Coord]) -> bool:
    return len(points) >= 2 and all(
        math.dist(a, b) > EPS and (
            abs(a[0] - b[0]) < EPS or abs(a[1] - b[1]) < EPS or
            abs(abs(a[0] - b[0]) - abs(a[1] - b[1])) < EPS
        ) for a, b in zip(points, points[1:])
    )


def _point_segment_distance(p: Coord, a: Coord, b: Coord) -> float:
    vx, vy = b[0] - a[0], b[1] - a[1]
    d = vx * vx + vy * vy or 1
    t = _clamp(((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / d, 0, 1)
    return math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy)


def _cross(a: Coord, b: Coord, p: Coord) -> float:
    return ((b[0] - a[0]) * (p[1] - a[1]) -
            (b[1] - a[1]) * (p[0] - a[0]))


def proper_intersection(a: Coord, b: Coord, c: Coord, d: Coord) -> bool:
    return (_cross(a, b, c) * _cross(a, b, d) < -EPS and
            _cross(c, d, a) * _cross(c, d, b) < -EPS)


def guide_metrics(
    positions: dict[str, Coord],
    guides: list[dict[str, Any]],
) -> dict[str, Any]:
    """Metrics in *source presentation units*, prior to native SVG Fit."""
    smallest = math.inf
    violations: list[dict[str, Any]] = []
    for guide in guides:
        endpoints = {guide["src"], guide["dst"]}
        for mid, p in positions.items():
            if mid in endpoints:
                continue
            gap = min(_point_segment_distance(p, a, b) for a, b in zip(
                guide["points"], guide["points"][1:]))
            smallest = min(smallest, gap)
            if gap < 30:
                violations.append({"guide": guide["src"] + ">" + guide["dst"],
                                   "station": mid, "distance": round(gap, 3)})
    crossings = 0
    for i, guide in enumerate(guides):
        for other in guides[i + 1:]:
            if guide["layerId"] == other["layerId"]:
                continue
            for a, b in zip(guide["points"], guide["points"][1:]):
                for c, d in zip(other["points"], other["points"][1:]):
                    crossings += int(proper_intersection(a, b, c, d))
    return {
        "guideCount": len(guides),
        "bends": sum(max(0, len(g["points"]) - 2) for g in guides),
        "minimumNonincidentStationClearance": (
            round(smallest, 3) if math.isfinite(smallest) else None),
        "nonincidentStationClearanceViolationsUnder30": violations,
        "crossCategoryGuideIntersections": crossings,
    }


def choose_centered_guide(
    source: Coord, target: Coord,
    *,
    src: str, dst: str,
    positions: dict[str, Coord],
    previously_routed: list[dict[str, Any]],
    layer_id: str,
) -> list[Coord]:
    """Choose a contained octilinear step, never crossing another category.

    The default centered candidate is preferred whenever it clears stations;
    the .35 and .65 variants only adjust *where* its diagonal transition
    occurs. No detours leave the two endpoint x/y envelopes.
    """
    candidates = [centered_step(source, target, before_fraction=f)
                  for f in (0.5, .35, .65, 0, 1)]
    passing = []
    for rank, points in enumerate(candidates):
        if not is_octilinear(points):
            continue
        too_close = False
        for mid, station in positions.items():
            if mid in (src, dst):
                continue
            dist = min(_point_segment_distance(station, a, b)
                       for a, b in zip(points, points[1:]))
            if dist < 30:
                too_close = True
                break
        if too_close:
            continue
        crosses = False
        for existing in previously_routed:
            if existing["layerId"] == layer_id:
                continue
            for a, b in zip(points, points[1:]):
                for c, d in zip(existing["points"], existing["points"][1:]):
                    if proper_intersection(a, b, c, d):
                        crosses = True
                        break
                if crosses:
                    break
            if crosses:
                break
        if not crosses:
            # Prefer centerpoint steps, with fewer bends and longer straight
            # runs as a second-order tie-break. No decorative detours.
            passing.append((rank, len(points) - 2, points))
    if not passing:
        raise ValueError("no source-faithful station-clear centered guide "
                         f"for {src}>{dst}")
    return min(passing, key=lambda p: (p[0], p[1]))[2]
