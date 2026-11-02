"""Source-authority certificate for a selected M-Journey cartographic projection.

The source manifest is frozen BEFORE optimization. Research direction and
sourceEdgeId live in the manifest, not in LOOM's undirected geometric edges.
LOOM node pointers are transient and must never enter semantic fingerprints.
No GUI or transit routing logic belongs in this module.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json

from .linegraph import LineGraph

TRAVERSABLE_KINDS = frozenset({"sequence", "branch", "convergence", "handoff"})
CERTIFICATE_SCHEMA = "mjourney-source-certificate/v1"


def _stable(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def fingerprint(data):
    """Hash normalized semantic data, not raw LOOM JSON or transient pointers."""
    return sha256(_stable(data)).hexdigest()


def _unique(items, context):
    if len(items) != len(set(items)):
        raise ValueError(f"{context}: repeated identity")


def _ids(items, context):
    ids = [x["id"] for x in items]
    _unique(ids, context)
    if any(not isinstance(x, str) or not x for x in ids):
        raise ValueError(f"{context}: missing identity")
    return ids


def build_source_manifest(source, routes, *, source_bytes=None):
    """Freeze canonical source + explicit approved route chains for one projection.

    routes: {stable_route_id: [sourceEdgeId, ...]}.
    A line here means an authored continuous visual chain, not a persona.
    """
    if not isinstance(source, dict) or not isinstance(routes, dict) or not routes:
        raise ValueError("source and nonempty route chains are required")
    stages = source["stages"]
    layers = source["layers"]
    moments = source["moments"]
    connections = source["connections"]
    stage_ids = _ids(stages, "stages")
    layer_ids = _ids(layers, "layers")
    moment_ids = _ids(moments, "moments")
    edge_ids = _ids(connections, "connections")
    stage_orders = [s["order"] for s in stages]
    layer_orders = [l["order"] for l in layers]
    _unique(stage_orders, "stage order")
    _unique(layer_orders, "layer order")
    if sorted(stage_orders) != list(range(len(stages))):
        raise ValueError("stage ordinals must be contiguous and unique")
    if sorted(layer_orders) != list(range(len(layers))):
        raise ValueError("layer ordinals must be contiguous and unique")
    by_moment = {m["id"]: m for m in moments}
    by_edge = {e["id"]: e for e in connections}
    for m in moments:
        if m["stageId"] not in stage_ids or m["layerId"] not in layer_ids:
            raise ValueError(f"{m['id']}: unknown stage or research layer")
    for e in connections:
        if e["fromId"] not in moment_ids or e["toId"] not in moment_ids:
            raise ValueError(f"{e['id']}: unknown canonical endpoint")
        if e["fromId"] == e["toId"]:
            raise ValueError(f"{e['id']}: self connection not authorized")
    _unique(list(routes), "route IDs")
    membership = defaultdict(list)
    chains = {}
    stations = set()
    for rid, chain in routes.items():
        if not isinstance(rid, str) or not rid or not isinstance(chain, list) or not chain:
            raise ValueError("route requires stable ID and ordered source edge list")
        _unique(chain, f"route {rid} edges")
        steps = []
        for eid in chain:
            if eid not in by_edge:
                raise ValueError(f"route {rid}: fabricated source edge {eid}")
            e = by_edge[eid]
            if e["kind"] not in TRAVERSABLE_KINDS:
                raise ValueError(f"route {rid}: non-traversable {eid} ({e['kind']})")
            if steps and steps[-1] != e["fromId"]:
                raise ValueError(f"route {rid}: disconnected directed chain at {eid}")
            if not steps:
                steps.append(e["fromId"])
            steps.append(e["toId"])
            membership[eid].append(rid)
            stations.update((e["fromId"], e["toId"]))
        # A directed route looping to an earlier source station is not implicitly
        # a lifecycle return. It requires a separate approved semantic rule.
        _unique(steps, f"route {rid} stations")
        chains[rid] = {
            "edgeIds": list(chain), "stationIds": steps,
            "classification": ("candidate_pathway" if rid in
                               ("ae_epc_mediated", "direct_customer_led")
                               else "authored_activity_chain"),
        }
    projection_edges = []
    for eid in sorted(membership):
        e = by_edge[eid]
        projection_edges.append({
            "sourceEdgeId": eid, "fromId": e["fromId"], "toId": e["toId"],
            "kind": e["kind"], "routeIds": sorted(membership[eid]),
        })
    projected_stations = [
        {"stationId": mid, "stageId": by_moment[mid]["stageId"],
         "layerId": by_moment[mid]["layerId"]}
        for mid in sorted(stations)
    ]
    canonical = {
        "journeyId": source.get("journeyId"),
        "stages": [{"id": s["id"], "order": s["order"]} for s in stages],
        "layers": [{"id": l["id"], "order": l["order"]} for l in layers],
        "stations": [{"stationId": m["id"], "stageId": m["stageId"],
                      "layerId": m["layerId"]} for m in moments],
        "relations": [{"sourceEdgeId": e["id"], "fromId": e["fromId"],
                       "toId": e["toId"], "kind": e["kind"]}
                      for e in connections],
    }
    canonical["stages"].sort(key=lambda r: r["id"])
    canonical["layers"].sort(key=lambda r: r["id"])
    canonical["stations"].sort(key=lambda r: r["stationId"])
    canonical["relations"].sort(key=lambda r: r["sourceEdgeId"])
    semantic = {
        "canonical": canonical,
        "projection": {
            "stations": projected_stations,
            "edges": projection_edges,
            "routes": chains,
        },
    }
    return {
        "schema": CERTIFICATE_SCHEMA,
        "sourceBytesSha256": sha256(source_bytes).hexdigest()
        if source_bytes is not None else None,
        "canonicalCounts": {"moments": len(moments),
                            "relations": len(connections), "stages": len(stages),
                            "layers": len(layers)},
        "projectionCounts": {"moments": len(stations),
                             "relations": len(projection_edges),
                             "lines": len(chains)},
        "sourceStationLabels": {mid: by_moment[mid]["label"]
                                for mid in sorted(stations)},
        "canonical": canonical,
        "projection": semantic["projection"],
        "semanticSha256": fingerprint(semantic),
        "fingerprintPolicy": (
            "Stable canonical source IDs, directed source endpoints, stage/layer "
            "membership and ordered route chains; no LOOM pointer IDs or coordinates"
        ),
    }


def verify_source_manifest(source, manifest, routes, *, source_bytes=None):
    """Fail closed on any change to the approved semantic source projection."""
    errors = []
    try:
        regenerated = build_source_manifest(source, routes, source_bytes=source_bytes)
    except (ValueError, KeyError, TypeError) as e:
        return {"passed": False, "errors": [f"invalid source projection: {e}"]}
    if manifest.get("schema") != CERTIFICATE_SCHEMA:
        errors.append("certificate schema mismatch")
    if manifest.get("semanticSha256") != regenerated["semanticSha256"]:
        errors.append("canonical source/projection semantic fingerprint changed")
    if manifest.get("canonical") != regenerated["canonical"]:
        errors.append("canonical station/stage/layer or directed relation changed")
    if manifest.get("projection") != regenerated["projection"]:
        errors.append("selected route/edge/line membership changed")
    if source_bytes is not None and manifest.get("sourceBytesSha256") != regenerated["sourceBytesSha256"]:
        errors.append("source fixture byte digest changed")
    if manifest.get("sourceStationLabels") != regenerated["sourceStationLabels"]:
        errors.append("source station labels changed")
    if manifest.get("canonicalCounts") != regenerated["canonicalCounts"]:
        errors.append("canonical counts changed")
    if manifest.get("projectionCounts") != regenerated["projectionCounts"]:
        errors.append("projection counts changed")
    return {"passed": not errors, "errors": errors,
            "semanticSha256": regenerated["semanticSha256"]}


def _station_adjacency(graph):
    """Collapse geometry-only helpers but stop at each *canonical* station.

    Every link is keyed by line ID and unordered station pair. This is a track
    certificate. Research-edge direction is NEVER inferred from LOOM geometry.
    """
    by_line = defaultdict(lambda: defaultdict(set))
    errors = []
    for e in graph.edges:
        if e.src not in graph.nodes or e.dst not in graph.nodes:
            errors.append(f"edge references unknown graph node: {e.src} -> {e.dst}")
            continue
        line_ids = [line.id for line in e.lines]
        if len(line_ids) != len(set(line_ids)):
            errors.append(f"duplicate route on graph edge {e.src} -> {e.dst}")
        for line_id in line_ids:
            by_line[line_id][e.src].add(e.dst)
            by_line[line_id][e.dst].add(e.src)
    by_id = {n.id: n.station_id for n in graph.stations}
    observed = defaultdict(set)
    for line_id, links in by_line.items():
        for node_id, station_id in by_id.items():
            if node_id not in links:
                continue
            pending = [node_id]
            seen = {node_id}
            while pending:
                here = pending.pop()
                for nxt in links[here]:
                    if nxt in seen:
                        continue
                    seen.add(nxt)
                    target = by_id.get(nxt)
                    if target is not None:
                        if target != station_id:
                            observed[line_id].add(tuple(sorted((station_id, target))))
                    else:
                        pending.append(nxt)
    return observed, errors


def validate_projection_graph(graph: LineGraph, manifest, *,
                              require_source_edge_ids=True):
    """Validate the actual adapter or post-solver graph against a frozen source.

    Strict mode is for the pre-optimization projection: each track must retain
    directed sourceEdgeId provenance and exact line membership. Post-LOOM
    mode checks canonical stations and connectivity but reports direction and
    edge provenance as unverifiable unless separately mapped to the manifest.
    """
    errors, warnings = [], []
    if manifest.get("schema") != CERTIFICATE_SCHEMA:
        return {"passed": False, "errors": ["unsupported certificate schema"]}
    proj = manifest["projection"]
    expected_stations = {x["stationId"]: x for x in proj["stations"]}
    expected_edges = {x["sourceEdgeId"]: x for x in proj["edges"]}
    expected_lines = set(proj["routes"])
    station_ids = [n.station_id for n in graph.stations]
    if any(not sid for sid in station_ids):
        errors.append("missing canonical station_id")
    if len(station_ids) != len(set(station_ids)):
        errors.append("duplicate canonical station_id")
    missing = sorted(set(expected_stations) - set(station_ids))
    added = sorted(set(station_ids) - set(expected_stations))
    if missing:
        errors.append(f"missing stations: {missing}")
    if added:
        errors.append(f"unapproved stations: {added}")
    for n in graph.stations:
        canonical = expected_stations.get(n.station_id)
        if canonical is None:
            continue
        if require_source_edge_ids and n.station_label != manifest["sourceStationLabels"].get(n.station_id):
            errors.append(f"{n.station_id}: source station label changed")
        for field, source_field in (("stageId", "stageId"), ("sourceLayerId", "layerId")):
            if field in n.props and n.props[field] != canonical[source_field]:
                errors.append(f"{n.station_id}: incorrect {field}")
        if require_source_edge_ids and ("stageId" not in n.props
                                         or "sourceLayerId" not in n.props):
            errors.append(f"{n.station_id}: missing stage/layer provenance")
    line_ids = {l.id for e in graph.edges for l in e.lines}
    if line_ids != expected_lines:
        errors.append(f"line IDs differ: missing={sorted(expected_lines-line_ids)}, "
                      f"extra={sorted(line_ids-expected_lines)}")
    expected_pairs = defaultdict(set)
    for edge in proj["edges"]:
        for rid in edge["routeIds"]:
            expected_pairs[rid].add(tuple(sorted((edge["fromId"], edge["toId"]))))
    observed, graph_errors = _station_adjacency(graph)
    errors.extend(graph_errors)
    for rid in sorted(expected_lines | set(observed)):
        lost = sorted(expected_pairs[rid] - observed[rid])
        gained = sorted(observed[rid] - expected_pairs[rid])
        if lost:
            errors.append(f"{rid}: missing station adjacencies: {lost}")
        if gained:
            errors.append(f"{rid}: unapproved station adjacencies: {gained}")
    if require_source_edge_ids:
        seen = []
        for e in graph.edges:
            ids = e.props.get("sourceEdgeIds")
            if not isinstance(ids, list) or len(ids) != 1:
                errors.append(f"missing or ambiguous sourceEdgeIds on {e.src}->{e.dst}")
                continue
            source_id = ids[0]
            seen.append(source_id)
            record = expected_edges.get(source_id)
            if record is None:
                errors.append(f"unapproved sourceEdgeId {source_id}")
                continue
            src = graph.nodes.get(e.src)
            dst = graph.nodes.get(e.dst)
            if not src or not dst or src.station_id != record["fromId"] or dst.station_id != record["toId"]:
                errors.append(f"{source_id}: directed source endpoints changed")
            if e.props.get("sourceKind") != record["kind"]:
                errors.append(f"{source_id}: source relationship kind changed")
            members = [line.id for line in e.lines]
            if sorted(members) != record["routeIds"]:
                errors.append(f"{source_id}: per-edge route membership changed")
        if len(seen) != len(set(seen)):
            errors.append("duplicated sourceEdgeId in projection graph")
        if set(seen) != set(expected_edges):
            errors.append(f"source-edge coverage changed: "
                          f"missing={sorted(set(expected_edges)-set(seen))}, "
                          f"extra={sorted(set(seen)-set(expected_edges))}")
    else:
        warnings.append("post-solver graph geometry is undirected: original relation "
                        "direction is retained in frozen source manifest, not inferred")
        warnings.append("post-solver per-source-edge mapping requires an independent "
                        "edge provenance reconstruction when helper vertices are inserted")
    core = {
        "stationIds": sorted(station_ids),
        "lineIds": sorted(line_ids),
        "stationAdjacencyByLine": {rid: [list(pair) for pair in sorted(observed[rid])]
                                   for rid in sorted(observed)},
    }
    return {
        "passed": not errors, "errors": errors, "warnings": warnings,
        "sourceEdgeProvenanceVerified": bool(require_source_edge_ids and not errors),
        "directedSourceAuthority": "frozen_manifest_only" if not require_source_edge_ids
                                    else "strict_projection",
        "graphSemanticSha256": fingerprint(core),
        "stationCount": len(station_ids), "lineCount": len(line_ids),
    }
