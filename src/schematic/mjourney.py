"""Source-traced M-Journey layer projection for the original Legible Cities renderer.

This is a *reading guide*, not a transit router. Connected colored guides
describe the grouping/order of authored journey moments. Unless a guide edge
has a direct source connection it MUST NOT be interpreted as a directed
relationship, movement, transfer, or customer pathway.

The canonical research graph is preserved in the input and audit sidecar;
LineGraph is only a derived drawing representation. No GTFS is invented.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .linegraph import Edge, Line, LineGraph, Node

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_TRAVERSABLE_KINDS = {"sequence", "branch", "convergence", "handoff"}


class ProjectionError(ValueError):
    """Invalid, incomplete, or misleading journey-to-map projection."""


@dataclass
class JourneyProjection:
    graph: LineGraph
    audit: dict[str, Any]
    stages: list[dict[str, Any]]
    layers: list[dict[str, Any]]


def _unique(items: list[dict], label: str) -> dict[str, dict]:
    ids: dict[str, dict] = {}
    for item in items:
        key = item.get("id")
        if not isinstance(key, str) or not key:
            raise ProjectionError(f"{label} has an empty or non-string id")
        if key in ids:
            raise ProjectionError(f"duplicate {label} id {key}")
        ids[key] = item
    return ids


def _validate(data: dict) -> tuple[dict, dict, dict, dict]:
    if data.get("schema") not in {"mjourney-sanitized-equipment-v1", "mjourney-sanitized-journey-v1"}:
        raise ProjectionError("unexpected M-Journey fixture schema")
    moments = _unique(data["moments"], "moment")
    connections = _unique(data["connections"], "connection")
    stages = _unique(data["stages"], "stage")
    layers = _unique(data["layers"], "layer")
    if not (moments and stages and layers):
        raise ProjectionError("journey must contain moments, stages and layers")
    for layer in layers.values():
        if not _HEX.fullmatch(layer["color"]):
            raise ProjectionError(f"invalid color for layer {layer['id']}")
    for moment in moments.values():
        if moment["stageId"] not in stages or moment["layerId"] not in layers:
            raise ProjectionError(f"unknown stage/layer on moment {moment['id']}")
        if not moment.get("label"):
            raise ProjectionError(f"unlabeled moment {moment['id']}")
    for edge in connections.values():
        if edge["fromId"] not in moments or edge["toId"] not in moments:
            raise ProjectionError(f"connection {edge['id']} has a missing endpoint")
    return moments, connections, stages, layers


def audit_editorial_paths(data: dict) -> list[dict[str, Any]]:
    """Check each proposed compressed path against the actual directed edges.

    A verified *chain* is not itself an approved transit line. Dependencies
    and lifecycle returns are deliberately not classified as ordinary travel.
    """
    moments, connections, _, _ = _validate(data)
    results = []
    for segment in data.get("editorialPathCandidates", []):
        here = segment["fromId"]
        problems = []
        if here not in moments or segment["toId"] not in moments:
            problems.append("missing station endpoint")
        if not segment.get("sourceEdgeIds"):
            problems.append("missing source edge provenance")
        for eid in segment.get("sourceEdgeIds", []):
            source = connections.get(eid)
            if source is None:
                problems.append(f"missing edge {eid}")
                continue
            if source["fromId"] != here:
                problems.append(f"non-contiguous directed edge {eid} after {here}")
            here = source["toId"]
            if source["kind"] == "dependency":
                problems.append(f"dependency is not route travel: {eid}")
            elif source["kind"] == "lifecycle_return":
                problems.append(f"lifecycle return needs separate treatment: {eid}")
            elif source["kind"] not in _TRAVERSABLE_KINDS:
                problems.append(f"unreviewed connection kind {source['kind']}: {eid}")
        if here != segment["toId"]:
            problems.append(f"chain ends at {here}, not {segment['toId']}")
        results.append({
            "id": segment["id"],
            "sourceEdgeIds": list(segment.get("sourceEdgeIds", [])),
            "directedChain": not any("non-contiguous" in p or "missing" in p
                                     or "chain ends" in p for p in problems),
            "eligibleForRouteReview": not problems,
            "approvedForRendering": False,
            "problems": problems,
        })
    return results


def build_projection(data: dict, station_ids: list[str] | None = None) -> JourneyProjection:
    """Create seven source-classified *visual guides* for fork rendering.

    Each guide connects successive visible moments in the SAME authored layer
    as an editorial index only. A guide that has no exact corresponding source
    connection is explicitly non-traversable; route finding and interchange
    claims must not use these display-only graph edges.

    Stage order is an authored sequence, not elapsed time. Coordinate positions
    are deterministic layout seeds, not researched geography or timing.
    """
    moments, connections, stage_by_id, layer_by_id = _validate(data)
    stations = list(station_ids if station_ids is not None
                    else data.get("curatedStationIds", list(moments)))
    if len(stations) != len(set(stations)):
        raise ProjectionError("duplicate curated station id")
    missing = set(stations) - set(moments)
    if missing:
        raise ProjectionError(f"unknown curated moments: {', '.join(sorted(missing))}")
    if not stations:
        raise ProjectionError("the curated projection needs at least one station")

    ordered_stages = sorted(stage_by_id.values(), key=lambda x: x["order"])
    ordered_layers = sorted(layer_by_id.values(), key=lambda x: x["order"])
    if len({s["order"] for s in ordered_stages}) != len(ordered_stages):
        raise ProjectionError("duplicate stage order")
    if len({l["order"] for l in ordered_layers}) != len(ordered_layers):
        raise ProjectionError("duplicate layer order")
    stage_rank = {s["id"]: i for i, s in enumerate(ordered_stages)}
    layer_rank = {l["id"]: i for i, l in enumerate(ordered_layers)}
    source_rank = {id_: i for i, id_ in enumerate(moments)}

    by_group: dict[tuple[str, str], list[str]] = {}
    for mid in stations:
        m = moments[mid]
        by_group.setdefault((m["stageId"], m["layerId"]), []).append(mid)

    coord: dict[str, tuple[float, float]] = {}
    for (stage_id, layer_id), ids in by_group.items():
        for idx, mid in enumerate(sorted(ids, key=lambda x: source_rank[x])):
            coord[mid] = (140 + stage_rank[stage_id] * 170 + idx * 40,
                          115 + layer_rank[layer_id] * 135)

    nodes = {
        mid: Node(
            id=mid, coord=coord[mid], station_id=mid,
            station_label=moments[mid]["label"],
            props={
                "sourceMomentId": mid,
                "stageId": moments[mid]["stageId"],
                "layerId": moments[mid]["layerId"],
                "evidenceRefPresent": moments[mid]["evidenceRefPresent"],
                "projectionRole": "authored-moment",
            },
        ) for mid in stations
    }

    source_pairs: dict[tuple[str, str], list[str]] = {}
    for conn in connections.values():
        source_pairs.setdefault((conn["fromId"], conn["toId"]), []).append(conn["id"])
    edges = []
    guide_audit = []
    for layer in ordered_layers:
        ordered = sorted(
            (mid for mid in stations if moments[mid]["layerId"] == layer["id"]),
            key=lambda mid: (stage_rank[moments[mid]["stageId"]], coord[mid][0], source_rank[mid]),
        )
        line = Line(id=layer["id"], label=layer["name"], color=layer["color"])
        for left, right in zip(ordered, ordered[1:]):
            # Same-layer membership does not establish a source connection.
            direct_ids = source_pairs.get((left, right), [])
            source_id = next(
                (eid for eid in direct_ids if connections[eid]["kind"] in _TRAVERSABLE_KINDS),
                None,
            )
            classification = ("authored-direct-connection" if source_id
                              else "non-traversable-organizational-guide")
            edges.append(Edge(
                src=left, dst=right,
                geometry=[coord[left], coord[right]], lines=[line],
                props={
                    "projectionRole": classification,
                    "traversable": bool(source_id),
                    "sourceEdgeIds": [source_id] if source_id else [],
                    "layerId": layer["id"],
                },
            ))
            guide_audit.append({
                "fromId": left, "toId": right, "layerId": layer["id"],
                "role": classification,
                "sourceEdgeIds": [source_id] if source_id else [],
            })

    graph = LineGraph(nodes=nodes, edges=edges)
    audit = {
        "journeyId": data["journeyId"],
        "reviewStatus": "candidate-layout-not-approved-as-traversable-routes",
        "canonical": {
            "momentCount": len(moments), "connectionCount": len(connections),
            "stageCount": len(stage_by_id), "layerCount": len(layer_by_id),
            "momentIds": list(moments), "connectionIds": list(connections),
        },
        "projection": {
            "stationIds": stations, "drawnGuideCount": len(edges),
            "nonTraversableGuides": sum(not e.props["traversable"] for e in edges),
            "transfers": [],  # none inferred from cross-layer dependencies
            "guideSemantics": "line continuity groups moments, not a customer path",
        },
        "guides": guide_audit,
        "editorialPathReview": audit_editorial_paths(data),
    }
    return JourneyProjection(graph=graph, audit=audit,
                             stages=ordered_stages, layers=ordered_layers)


def from_json(path: str | Path, station_ids: list[str] | None = None) -> JourneyProjection:
    return build_projection(json.loads(Path(path).read_text(encoding="utf-8")), station_ids)


# Source-backed route view. Kept separate from the original editorial-layer
# projection above so existing semantics/tests remain stable.
_NETWORK_SUPPORT_IDS = {
    # Feasibility branches, all direct source sequences.
    "edge03", "edge05", "edge07", "edge09", "edge11", "edge13",
    "edge14", "edge15", "edge17", "edge18", "edge19",
    # Parallel business-case and governance pathways.
    "edge23", "edge25", "edge28", "edge29", "edge31",
    "edge35", "edge40",
    # Delivery preparation, validation and handover.
    "edge57", "edge58", "edge63", "edge65", "edge79", "edge81",
}
_NETWORK_COLORS = (
    "#3685F4", "#FF4C95", "#16C9D9", "#F3B92C",
    "#9862E6", "#FF9151", "#24BE82",
)


def _octilinear(source: tuple[float, float], target: tuple[float, float]
               ) -> list[tuple[float, float]]:
    """Make 0/45/90-degree geometry without inventing intermediate stations.

    These are purely visual bend vertices on one confirmed source edge, NOT
    new research moments. Ends retain their exact source-linked station IDs.
    """
    x0, y0 = source
    x1, y1 = target
    dx, dy = x1 - x0, y1 - y0
    if abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-6:
        return [source, target]
    sx = 1 if dx > 0 else -1
    sy = 1 if dy > 0 else -1
    diagonal = min(abs(dy), abs(dx) * 0.60)
    if abs(dx) > abs(dy) * 1.4:
        # Lead with the diagonal then follow the horizontal corridor.
        elbow = (x0 + sx * diagonal, y0 + sy * diagonal)
        return [source, elbow, target]
    # Brief horizontal departure, a diagonal turn and a final vertical
    # arrival. Every segment is horizontal, vertical or 45 degrees.
    horizontal = max(0.0, abs(dx) - diagonal)
    a = (x0 + sx * horizontal, y0)
    b = (a[0] + sx * diagonal, y0 + sy * diagonal)
    out = [source]
    for point in (a, b, target):
        if point != out[-1]:
            out.append(point)
    return out


def build_network_projection(data: dict, *, full: bool = False) -> JourneyProjection:
    """Build a *connected* map from actual authored customer-journey edges.

    Color on each directed segment refers to the layer from which the
    relationship originates. A change of color at a station is a witnessed
    transition between authored layers, not an inferred passenger interchange.
    Only sequence/branch/convergence/handoff edges are drawn; dependency
    overlays and lifecycle feedback have different semantics and remain in
    the audit, not represented as customer travel.

    This bypasses LOOM because the source graph is not GTFS. It reuses the
    original Legible Cities LineGraph and SVG renderer unchanged.
    """
    moments, connections, stages, layers = _validate(data)
    ordered_stages = sorted(stages.values(), key=lambda s: s["order"])
    ordered_layers = sorted(layers.values(), key=lambda l: l["order"])
    sindex = {s["id"]: i for i, s in enumerate(ordered_stages)}
    lindex = {l["id"]: i for i, l in enumerate(ordered_layers)}
    if len(sindex) != len({s["order"] for s in ordered_stages}):
        raise ProjectionError("ambiguous stage order")
    if len(lindex) != len({l["order"] for l in ordered_layers}):
        raise ProjectionError("ambiguous layer order")
    # Every station gets a monotonically increasing position inside its
    # authored stage, with inter-stage gutters for chapter and label framing.
    grouped: dict[str, list[str]] = {s["id"]: [] for s in ordered_stages}
    for mid, moment in moments.items():
        grouped[moment["stageId"]].append(mid)
    coordinates = {}
    stage_ranges = []
    left = 85.0
    for stage in ordered_stages:
        ids = grouped[stage["id"]]
        beginning = left
        for slot, mid in enumerate(ids):
            coordinates[mid] = (left + slot * 43.0, 105 + lindex[moments[mid]["layerId"]] * 225.0)
        left += max(len(ids) - 1, 1) * 43.0 + 148.0
        stage_ranges.append({
            "id": stage["id"], "name": stage["shortName"],
            "startX": beginning, "endX": left - 80.0,
        })

    allowed = [
        edge for edge in connections.values()
        if edge["kind"] in _TRAVERSABLE_KINDS
        and (full or edge.get("primary") or edge["id"] in _NETWORK_SUPPORT_IDS)
    ]
    excluded = [
        {"id": edge["id"], "kind": edge["kind"],
         "reason": ("dependency/feedback is not an ordinary traversable segment"
                    if edge["kind"] not in _TRAVERSABLE_KINDS
                    else "not selected for focused schematic")}
        for edge in connections.values() if edge not in allowed
    ]
    visible = {v for edge in allowed for v in (edge["fromId"], edge["toId"])}
    nodes = {
        mid: Node(
            id=mid, coord=coordinates[mid], station_id=mid,
            station_label=moments[mid]["label"], props={
                "sourceMomentId": mid, "stageId": moments[mid]["stageId"],
                "layerId": moments[mid]["layerId"],
                "evidenceRefPresent": moments[mid]["evidenceRefPresent"],
            })
        for mid in moments if mid in visible
    }
    routes = [
        Line(id=layer["id"], label=layer["name"],
             color=(_NETWORK_COLORS[i] if data["journeyId"] == "equipment-public-demo"
                    else layer["color"]))
        for i, layer in enumerate(ordered_layers)
    ]
    line_by_layer = {ordered_layers[i]["id"]: routes[i] for i in range(len(routes))}
    drawn = []
    transitions = []
    for source in allowed:
        start, end = source["fromId"], source["toId"]
        source_layer = moments[start]["layerId"]
        destination_layer = moments[end]["layerId"]
        crossing = source_layer != destination_layer
        drawn.append(Edge(
            src=start, dst=end,
            geometry=_octilinear(coordinates[start], coordinates[end]),
            lines=[line_by_layer[source_layer]],
            props={
                "sourceEdgeIds": [source["id"]],
                "sourceKind": source["kind"],
                "sourceRouteId": source["routeId"],
                "crossLayer": crossing,
                "fromLayerId": source_layer,
                "toLayerId": destination_layer,
                "projectionRole": "authored-directed-journey-connection",
                "traversable": True,
            }
        ))
        if crossing:
            transitions.append({
                "sourceEdgeId": source["id"], "fromId": start, "toId": end,
                "fromLayerId": source_layer, "toLayerId": destination_layer,
                "kind": source["kind"], "routeId": source["routeId"],
            })

    graph = LineGraph(nodes=nodes, edges=drawn)
    return JourneyProjection(
        graph=graph, stages=ordered_stages, layers=ordered_layers,
        audit={
            "journeyId": data["journeyId"],
            "reviewStatus": "actual-source-topology-editorial-geometry-review-needed",
            "canonical": {
                "momentCount": len(moments), "connectionCount": len(connections),
                "stageCount": len(stages), "layerCount": len(layers),
            },
            "projection": {
                "mode": "source-connected-full" if full else "source-connected-focused",
                "stationIds": list(nodes),
                "renderedEdgeIds": [e["id"] for e in allowed],
                "drawnConnectionCount": len(allowed),
                "crossLayerConnectionCount": len(transitions),
                "sourceValidatedCrossLayerTransitions": transitions,
                "interchanges": [],
                "inferredConnections": 0,
                "stageRanges": stage_ranges,
                "lineColorSemantics": "authored origin layer of each directed connection",
                "allRenderedSegmentsHaveDirectSourceEdges": True,
                "excludedConnections": excluded,
            },
            "editorialPathReview": audit_editorial_paths(data),
        },
    )


def build_system_v3(data: dict) -> JourneyProjection:
    """Native Legible Cities System map with continuous *category* lines.

    This projection deliberately does NOT use source relationships as colored
    transit segments. One source moment yields one stationary node, assigned
    only to its authored layer; each line continuously presents category
    membership, and every display guide is explicitly non-traversable unless
    its two endpoints have a direct approved source connection (currently none
    of the 87 have been individually approved as travel).

    Canonical connections, authored path branches and the lifecycle return are
    preserved in the audit for interpretation and later route emphasis.
    """
    moments, connections, stages, layers = _validate(data)
    ordered_stages = sorted(stages.values(), key=lambda s: s["order"])
    ordered_layers = sorted(layers.values(), key=lambda l: l["order"])
    stage_order = {s["id"]: i for i, s in enumerate(ordered_stages)}
    layer_order = {l["id"]: i for i, l in enumerate(ordered_layers)}
    # Ten ordinal stage domains; widths reflect label/station density, never months.
    stage_counts = [
        sum(m["stageId"] == stage["id"] for m in moments.values())
        for stage in ordered_stages
    ]
    widths = [max(175., 140. + 22. * n) for n in stage_counts]
    bounds = [70.]
    for width in widths:
        bounds.append(bounds[-1] + width)
    # Natural bends replace rigid swimlane rows. Stage/line anchors are
    # presentation geometry, not measured data or inferred relationships.
    # The waves are deterministic and preserve the seven line identities.
    import math
    center = (len(ordered_layers) - 1) / 2
    category_y = {}
    for li, layer in enumerate(ordered_layers):
        for si, stage in enumerate(ordered_stages):
            drift = 42 * math.sin(si * .72 + li * .56)
            # Stations may visually cluster into corridors around procurement.
            pull = (13 if si in (4, 5, 6) else 0) * (center - li)
            category_y[(layer["id"], stage["id"])] = (
                150 + li * 104 + drift + pull
            )

    # All 67 authored moments retain their stage, identity, and one sourced
    # layer membership. The slot allocation avoids coincident moment markers.
    membership = {layer["id"]: [] for layer in ordered_layers}
    by_bucket: dict[tuple[str, str], list[str]] = {}
    for mid, m in moments.items():
        membership[m["layerId"]].append(mid)
        by_bucket.setdefault((m["stageId"], m["layerId"]), []).append(mid)
    positions = {}
    for mid, m in moments.items():
        ids = by_bucket[(m["stageId"], m["layerId"])]
        slot = ids.index(mid)
        n = len(ids)
        stage = stage_order[m["stageId"]]
        # Use the same x for all memberships in a stage only if their
        # individual slot differs; y stays distinct between categories.
        x = bounds[stage] + widths[stage] * (slot + 1) / (n + 1)
        y = category_y[(m["layerId"], m["stageId"])]
        positions[mid] = (x, y)

    # Native nodes and edges go through the original render/animate engine.
    nodes = {
        mid: Node(
            id=mid, coord=positions[mid], station_id=mid,
            station_label=m["label"],
            props={
                "sourceMomentId": mid, "stageId": m["stageId"],
                "layerIds": [m["layerId"]],
                "evidenceRefPresent": m["evidenceRefPresent"],
                "projectionRole": "canonical-research-moment",
            },
        )
        for mid, m in moments.items()
    }
    lines = [
        Line(id=l["id"], label=l["name"], color=l["color"])
        for l in ordered_layers
    ]
    edges = []
    guide_audit = []
    source_pairs: dict[tuple[str, str], list[str]] = {}
    for e in connections.values():
        source_pairs.setdefault((e["fromId"], e["toId"]), []).append(e["id"])

    for line in lines:
        mids = sorted(membership[line.id],
                      key=lambda mid: (stage_order[moments[mid]["stageId"]],
                                       positions[mid][0], mid))
        for prev, nxt in zip(mids, mids[1:]):
            # A colored line is an organizational membership guide only.
            # It NEVER automatically becomes a verified traversable route.
            relationship_ids = source_pairs.get((prev, nxt), [])
            geom = _octilinear(positions[prev], positions[nxt])
            edges.append(Edge(
                src=prev, dst=nxt, geometry=geom, lines=[line],
                props={
                    "projectionRole": "non-traversable-category-guide",
                    "traversable": False,
                    "layerId": line.id, "sourceEdgeIds": relationship_ids,
                },
            ))
            guide_audit.append({
                "fromId": prev, "toId": nxt, "layerId": line.id,
                "disposition": "non-traversable-category-guide",
                "directAuthoredConnectionIds": relationship_ids,
            })

    graph = LineGraph(nodes=nodes, edges=edges)
    path_branches: dict[str, list[str]] = {}
    for e in connections.values():
        if e["routeId"] not in ("all", None, ""):
            path_branches.setdefault(e["routeId"], []).append(e["id"])
    stage_ranges = [
        {
            "id": stage["id"], "name": stage["shortName"],
            "fullName": stage["name"], "startX": bounds[i],
            "endX": bounds[i+1],
        }
        for i, stage in enumerate(ordered_stages)
    ]
    return JourneyProjection(
        graph=graph,
        stages=ordered_stages,
        layers=ordered_layers,
        audit={
            "schema": "mjourney-system-layout-v3",
            "journeyId": data["journeyId"],
            "semantics": "Seven continuous category membership lines; NOT customer travel",
            "canonical": {
                "momentCount": len(moments), "connectionCount": len(connections),
                "stageCount": len(stages), "layerCount": len(layers),
                "sourceEdgeIds": list(connections),
            },
            "projection": {
                "mode": "system-v3",
                "stationIds": list(nodes),
                "stationCoords": {id_: list(n.coord) for id_, n in nodes.items()},
                "stageRanges": stage_ranges,
                "lineMemberships": {
                    key: list(values) for key, values in membership.items()
                },
                "lines": [
                    {"id": l.id, "name": l.label, "color": l.color,
                     "kind": "category"}
                    for l in lines
                ],
                "guideCount": len(edges),
                "nonTraversableGuides": len(edges),
                "traversableGuides": 0,
                "inferredTransfers": 0,
                "sourcePathBranches": path_branches,
                "lifecycleReturnIds": [
                    e["id"] for e in connections.values()
                    if e["kind"] == "lifecycle_return"
                ],
                "positionsDeterministic": True,
                "stageDistanceMeansElapsedTime": False,
            },
            "guides": guide_audit,
        },
    )
