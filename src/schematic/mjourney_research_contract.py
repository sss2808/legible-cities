"""Read-only source contract for the native M-Journey System rendering.

A category line is a visible grouping, NEVER a passenger route, transfer,
or directed research connection. Preserve the source graph independently
of native LineGraph, which exists solely to provide drawing geometry.
"""
from __future__ import annotations
import hashlib
import json

from .mjourney import _validate, ProjectionError

FOCUS_KINDS = {"sequence", "branch", "convergence", "handoff"}


class ResearchContractError(ProjectionError):
    """Source and rendered semantic projection disagree."""


def _require(condition, message):
    if not condition:
        raise ResearchContractError(message)


def build_system_contract(source, projection, *, focus_paths=None):
    """Validate System V3. Focus paths are highlighted directed chains, NOT
    independently approved customer itineraries. No data or geometry changes.
    """
    moments, relations, stages, layers = _validate(source)
    audit = projection.audit["projection"]
    graph = projection.graph
    _require(audit.get("mode") == "system-v3", "expected System V3 projection")
    _require(set(graph.nodes) == set(moments), "source moment identities changed")
    _require(len(graph.stations) == len(moments)
             and {n.station_id for n in graph.stations} == set(moments),
             "canonical station IDs repeated or missing")
    _require(len({s["order"] for s in stages.values()}) == len(stages),
             "duplicated stage order")
    _require(len({l["order"] for l in layers.values()}) == len(layers),
             "duplicated layer order")
    ordered_stages = sorted(stages.values(), key=lambda s: (s["order"], s["id"]))
    ordered_layers = sorted(layers.values(), key=lambda l: (l["order"], l["id"]))
    ranges = audit.get("stageRanges", [])
    _require(len(ranges) == len(stages), "stage domain count changed")
    by_stage = {}
    last_right = None
    for stage, domain in zip(ordered_stages, ranges):
        _require(stage["id"] == domain["id"]
                 and stage["shortName"] == domain["name"],
                 "stage headings or order changed")
        left, right = domain["startX"], domain["endX"]
        _require(left < right and (last_right is None or left >= last_right),
                 "overlapping or reversed stage domains")
        last_right = right
        by_stage[stage["id"]] = (left, right)

    for mid, moment in moments.items():
        node = graph.nodes[mid]
        _require(node.station_id == mid and node.props.get("sourceMomentId") == mid,
                 f"{mid}: station does not map to original moment")
        _require(node.props.get("stageId") == moment["stageId"]
                 and node.props.get("layerIds") == [moment["layerId"]],
                 f"{mid}: authored stage or category changed")
        _require(node.station_label == moment["label"],
                 f"{mid}: canonical label changed")
        _require(by_stage[moment["stageId"]][0] <= node.coord[0]
                 <= by_stage[moment["stageId"]][1],
                 f"{mid}: station left its source stage")
        _require(bool(node.props.get("evidenceRefPresent"))
                 == bool(moment.get("evidenceRefPresent")),
                 f"{mid}: evidence-reference flag changed")

    by_pair = {}
    for e in relations.values():
        by_pair.setdefault((e["fromId"], e["toId"]), set()).add(e["id"])
    guides, seen = [], set()
    for edge in graph.edges:
        _require(edge.props.get("projectionRole")
                 == "non-traversable-category-guide"
                 and edge.props.get("traversable") is False,
                 "display guide was promoted to traversable source edge")
        lid = edge.props.get("layerId")
        _require(lid in layers and edge.src in moments and edge.dst in moments,
                 "category guide has unknown source identity")
        _require(edge.src != edge.dst and moments[edge.src]["layerId"] == lid
                 and moments[edge.dst]["layerId"] == lid,
                 "category guide changes canonical line membership")
        _require(len(edge.lines) == 1 and edge.lines[0].id == lid,
                 "rendered line identity differs from authored category")
        key = (lid, edge.src, edge.dst)
        _require(key not in seen, "duplicate category guide")
        seen.add(key)
        actual_refs = edge.props.get("sourceEdgeIds")
        expected_refs = by_pair.get((edge.src, edge.dst), set())
        _require(isinstance(actual_refs, list) and len(actual_refs) == len(expected_refs)
                 and set(actual_refs) == expected_refs,
                 "category guide falsely claims a directed source relationship")
        _require(bool(edge.geometry) and tuple(edge.geometry[0])
                 == tuple(graph.nodes[edge.src].coord)
                 and tuple(edge.geometry[-1]) == tuple(graph.nodes[edge.dst].coord),
                 "guide endpoints disagree with canonical station geometry")
        guides.append({
            "id": f"guide:{lid}:{edge.src}:{edge.dst}",
            "lineId": lid, "fromId": edge.src, "toId": edge.dst,
            "kind": "category", "traversable": False,
            "matchingDirectedSourceEdgeIds": sorted(expected_refs),
        })
    expected_guides = sum(
        max(0, sum(m["layerId"] == lid for m in moments.values()) - 1)
        for lid in layers
    )
    _require(len(guides) == expected_guides,
             "category guide count does not match canonical membership")

    focus = []
    seen_focus = set()
    for item in focus_paths or []:
        fid, seq = item.get("id"), item.get("sourceEdgeIds")
        _require(isinstance(fid, str) and bool(fid) and fid not in seen_focus,
                 "focus IDs must be unique and nonempty")
        seen_focus.add(fid)
        _require(isinstance(seq, list) and bool(seq) and len(seq) == len(set(seq)),
                 "focus requires distinct ordered source edge IDs")
        visited, end = [], None
        for eid in seq:
            e = relations.get(eid)
            _require(e is not None, f"{fid}: fabricated source edge {eid}")
            _require(e["kind"] in FOCUS_KINDS,
                     f"{fid}: {eid} kind is not an authorized focus step")
            _require(end is None or end == e["fromId"],
                     f"{fid}: disconnected directed focus at {eid}")
            if end is None:
                visited.append(e["fromId"])
            end = e["toId"]
            visited.append(end)
        focus.append({
            "id": fid, "sourceEdgeIds": list(seq), "momentIds": visited,
            "kind": "source-backed-highlight",
            "approvedAsCustomerItinerary": False,
            "createsTransfer": False,
        })

    canonical = {
        "journeyId": source.get("journeyId"),
        "stages": [{"id": s["id"], "order": s["order"], "name": s["shortName"]}
                   for s in ordered_stages],
        "categories": [{"id": l["id"], "name": l["name"],
                        "order": l["order"], "color": l["color"]}
                       for l in ordered_layers],
        "moments": [{
            "id": m["id"], "label": m["label"], "stageId": m["stageId"],
            "layerId": m["layerId"], "evidenceClass": m.get("evidenceClass"),
            "evidenceRefPresent": bool(m.get("evidenceRefPresent")),
        } for m in sorted(moments.values(), key=lambda m: m["id"])],
        "relationships": [{
            "id": e["id"], "fromId": e["fromId"], "toId": e["toId"],
            "kind": e["kind"], "routeId": e.get("routeId"),
            "evidenceStatus": e.get("evidenceStatus", "not_supplied_in_public_fixture"),
            "role": "authored-directed-source-relationship",
        } for e in sorted(relations.values(), key=lambda e: e["id"])],
    }
    digest = hashlib.sha256(json.dumps(
        canonical, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    return {
        "schema": "mjourney-system-research-contract/v1",
        "canonicalSemanticSha256": digest,
        "canonical": canonical,
        "presentation": {
            "representation": "System",
            "stageDomains": ranges,
            "categoryGuides": sorted(guides, key=lambda g: g["id"]),
            "momentLineMemberships": [
                {"momentId": mid, "lineIds": [moments[mid]["layerId"]]}
                for mid in sorted(moments)],
            "lineKinds": {lid: "category" for lid in sorted(layers)},
            "categoryGuidesNavigable": False,
            "interchangesInferredFromMembership": False,
            "approvedTransfers": [],
        },
        "focusSequences": focus,
        "integrity": {
            "passed": True, "stationCount": len(moments),
            "sourceRelationshipCount": len(relations),
            "guideCount": len(guides),
            "researchEdgesManufacturedFromGuides": 0,
            "geometryCreatesNoSourceAuthority": True,
        },
    }
