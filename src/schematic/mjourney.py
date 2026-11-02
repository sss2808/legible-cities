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
    if data.get("schema") != "mjourney-sanitized-equipment-v1":
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
