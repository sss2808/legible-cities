"""Negative/positive controls for the M-Journey System research boundary."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from schematic.mjourney import build_system_v3
from schematic.mjourney_research_contract import (
    ResearchContractError, build_system_contract,
)

ROOT = Path(__file__).resolve().parents[1]
EQUIPMENT = ROOT / "fixtures/mjourney/equipment-sanitized-v1.json"
STARTER = ROOT / "fixtures/mjourney/b2b-starter-v1.json"


@pytest.fixture()
def equipment():
    return json.loads(EQUIPMENT.read_text())


def test_all_canonical_edges_retained_without_becoming_transit_tracks(equipment):
    out = build_system_contract(equipment, build_system_v3(equipment))
    assert out["schema"] == "mjourney-system-research-contract/v1"
    assert out["integrity"]["stationCount"] == 67
    assert out["integrity"]["sourceRelationshipCount"] == 87
    assert out["integrity"]["guideCount"] == 60
    assert len(out["presentation"]["categoryGuides"]) == 60
    assert len(out["canonical"]["relationships"]) == 87
    assert all(not g["traversable"] for g in out["presentation"]["categoryGuides"])
    assert all(r["role"] == "authored-directed-source-relationship"
               for r in out["canonical"]["relationships"])
    assert out["presentation"]["approvedTransfers"] == []
    assert out["presentation"]["categoryGuidesNavigable"] is False
    assert out["presentation"]["interchangesInferredFromMembership"] is False
    assert sum(m["key"] for m in out["canonical"]["moments"]) == 27
    assert sum(m["decision"] for m in out["canonical"]["moments"]) == 15
    assert all(isinstance(m["key"], bool) and isinstance(m["decision"], bool)
               for m in out["canonical"]["moments"])


def test_starter_three_channels_are_not_renamed_seven_workstreams():
    source = json.loads(STARTER.read_text())
    contract = build_system_contract(source, build_system_v3(source))
    assert contract["integrity"]["stationCount"] == 19
    assert contract["integrity"]["sourceRelationshipCount"] == 18
    assert contract["integrity"]["guideCount"] == 16
    assert len(contract["presentation"]["stageDomains"]) == 5
    assert set(contract["presentation"]["lineKinds"]) == {
        l["id"] for l in source["layers"]}
    assert {x["name"] for x in contract["canonical"]["categories"]} == {
        "Online", "Omni", "Offline"}


def test_directed_branch_convergence_focus_is_source_backed_not_approved_travel(equipment):
    focus = [
        {"id": "ae_epc", "sourceEdgeIds": ["edge44", "edge48", "edge49", "edge50"]},
        {"id": "direct", "sourceEdgeIds": ["edge45", "edge51", "edge52"]},
    ]
    contract = build_system_contract(equipment, build_system_v3(equipment),
                                     focus_paths=focus)
    assert len(contract["focusSequences"]) == 2
    a, b = contract["focusSequences"]
    assert a["momentIds"] == ["eq31", "eq32", "eq34", "eq36", "eq37"]
    assert b["momentIds"] == ["eq31", "eq33", "eq35", "eq37"]
    assert not a["approvedAsCustomerItinerary"]
    assert not b["approvedAsCustomerItinerary"]
    assert not a["createsTransfer"]


@pytest.mark.parametrize("bad", [
    ["edge44", "edge49"],
    ["edge44", "edge46"],
    ["edge44", "edge999"],
    ["edge87"],
])
def test_rejects_disconnected_dependency_unknown_or_lifecycle_focus(equipment, bad):
    with pytest.raises(ResearchContractError):
        build_system_contract(equipment, build_system_v3(equipment),
                              focus_paths=[{"id": "bad", "sourceEdgeIds": bad}])


def test_rejects_fake_source_claim_on_visual_guide(equipment):
    projection = build_system_v3(equipment)
    projection.graph.edges[0].props["sourceEdgeIds"] = ["edge37"]
    with pytest.raises(ResearchContractError, match="falsely claims"):
        build_system_contract(equipment, projection)


def test_rejects_category_guide_promotion_to_passenger_travel(equipment):
    projection = build_system_v3(equipment)
    projection.graph.edges[0].props["traversable"] = True
    with pytest.raises(ResearchContractError, match="promoted"):
        build_system_contract(equipment, projection)


def test_rejects_stage_migration_even_when_source_edges_unchanged(equipment):
    projection = build_system_v3(equipment)
    projection.graph.nodes["eq31"].props["stageId"] = "stage-5"
    with pytest.raises(ResearchContractError, match="stage or category"):
        build_system_contract(equipment, projection)


def test_rejects_stage_boundary_overshoot(equipment):
    projection = build_system_v3(equipment)
    node = projection.graph.nodes["eq31"]
    node.coord = (1e9, node.coord[1])
    with pytest.raises(ResearchContractError, match="left its source stage"):
        build_system_contract(equipment, projection)


def test_rejects_duplicate_station_identity(equipment):
    projection = build_system_v3(equipment)
    projection.graph.nodes["eq31"].station_id = "eq32"
    with pytest.raises(ResearchContractError, match="canonical station IDs"):
        build_system_contract(equipment, projection)


def test_canonical_digest_is_independent_of_json_record_order(equipment):
    before = build_system_contract(equipment, build_system_v3(equipment))
    shuffled = copy.deepcopy(equipment)
    for name in ("moments", "connections", "layers", "stages"):
        shuffled[name].reverse()
    after = build_system_contract(shuffled, build_system_v3(shuffled))
    assert before["canonicalSemanticSha256"] == after["canonicalSemanticSha256"]
    assert before["canonical"]["relationships"] == after["canonical"]["relationships"]
    # Geometry may remain input-order sensitive in V3; certifying a semantic
    # source digest does not claim that those positions are layout-stable.


def test_cli_writes_research_contract_sidecar_with_native_svg(equipment, tmp_path):
    out = tmp_path / "system.svg"
    proc = subprocess.run([
        sys.executable, str(ROOT / "bin/mjourney-preview"), "--system-v3",
        "--source", str(EQUIPMENT), "--output", str(out),
        "--focus-path", "ae=edge44,edge48,edge49,edge50",
    ], capture_output=True, text=True, check=False, timeout=90)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(out.with_suffix(".research.json").read_text())
    audit = json.loads(out.with_suffix(".audit.json").read_text())
    assert payload["integrity"]["passed"]
    assert audit["researchContract"]["canonicalSemanticSha256"] == payload[
        "canonicalSemanticSha256"]
    assert audit["researchContract"]["categoryGuidesNavigable"] is False
    assert audit["render"]["researchNavigationImplemented"] is False
    assert out.exists()



def test_system_html_contains_canonical_inspector_and_not_a_passenger_trip_picker(tmp_path):
    out = tmp_path / "equipment.svg"
    proc = subprocess.run([
        sys.executable, str(ROOT / "bin/mjourney-preview"), "--system-v3",
        "--source", str(EQUIPMENT), "--html", "--output", str(out),
    ], capture_output=True, text=True, timeout=90)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    html = out.with_suffix(".html").read_text(encoding="utf-8")
    assert 'id="mjourney-research"' in html
    assert 'data-mjourney-inspector' in html
    assert "mj-moment-picker" in html
    assert "Incoming authored relationships" in html
    assert 'e.stopImmediatePropagation()' not in (ROOT / "bin/mjourney-preview").read_text()
    assert 'data-mjourney' in html
    assert 'if (!present && !isMJourney) buildPicking();' in html
    assert "Only real railway pages derive passenger adjacency" in html
    assert "Trains move along the lines" in html  # native fallback retained for rail maps
    audit = json.loads(out.with_suffix(".audit.json").read_text())
    assert audit["render"]["researchNavigationImplemented"] is True
    assert audit["render"]["internalTransitNetworkBuiltByUpstream"] is False
    assert audit["render"]["viewerModes"] == ["system"]
    import re
    embedded = re.search(
        r'<script id="mjourney-research" type="application/json">(.*?)</script>',
        html, re.S,
    )
    assert embedded
    contract = json.loads(embedded.group(1))
    assert len(contract["canonical"]["moments"]) == 67
    assert len(contract["canonical"]["relationships"]) == 87


def test_native_railway_viewer_keeps_original_trip_picker_separate():
    page = (ROOT / "src/schematic/page/page.html").read_text()
    assert 'if (!present && !isMJourney) buildPicking();' in page
    assert 'if (!isMJourney) {' in page
    assert 'return isMJourney ? null : setTrip(from, to);' in page
    assert 'Research journey schematic with ' in page
    assert "Trains move along the lines as the clock runs" in page



def test_empty_timetable_never_uses_railway_route_planner(equipment, monkeypatch):
    import datetime as dt
    from schematic import animate
    from schematic import render as svg_renderer

    def fail_if_called(*args, **kwargs):
        raise AssertionError("no trip planner may run for empty research timetable")

    monkeypatch.setattr(animate.RouteNetwork, "build", fail_if_called)
    projection = build_system_v3(equipment)
    frame = svg_renderer.render(projection.graph, width=1000)
    animation = animate.build(frame, projection.graph, [],
                              date=dt.date(2026, 11, 2))
    assert animation.trips == []
    assert animation.paths == []
