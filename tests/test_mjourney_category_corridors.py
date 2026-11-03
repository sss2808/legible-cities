"""Source-authoritative stage-demand category-guide cartography tests.

No source moment/relationship changes are permitted. Intercategory source
relationships are spacing demand, never implied transit routes or transfers.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from schematic.mjourney import build_system_v3
from schematic.mjourney_category_corridors import (
    centered_step, guide_metrics, is_octilinear,
)

ROOT = Path(__file__).resolve().parents[1]
EQUIPMENT = ROOT / "fixtures/mjourney/equipment-sanitized-v1.json"
STARTER = ROOT / "fixtures/mjourney/b2b-starter-v1.json"


@pytest.fixture
def equipment():
    return json.loads(EQUIPMENT.read_text(encoding="utf-8"))


def test_original_system_v3_remains_unchanged_without_opt_in(equipment):
    default = build_system_v3(equipment)
    explicit = build_system_v3(equipment, stage_demand_corridors=False)
    assert default.audit == explicit.audit
    assert default.graph.to_geojson() == explicit.graph.to_geojson()
    assert default.audit["projection"]["categoryCorridorMode"] == "legacy-v3"


def test_category_corridor_mode_keeps_research_topology_and_station_stage_x(equipment):
    original = build_system_v3(equipment)
    adapted = build_system_v3(equipment, stage_demand_corridors=True)
    assert len(original.graph.nodes) == len(adapted.graph.nodes) == 67
    assert len(original.graph.edges) == len(adapted.graph.edges) == 60
    assert [e.src for e in original.graph.edges] == [e.src for e in adapted.graph.edges]
    assert [e.dst for e in original.graph.edges] == [e.dst for e in adapted.graph.edges]
    for mid, node in adapted.graph.nodes.items():
        old = original.graph.nodes[mid]
        assert node.coord[0] == old.coord[0], mid
        assert node.station_id == old.station_id
        assert node.station_label == old.station_label
        assert node.props == old.props
    assert any(adapted.graph.nodes[mid].coord[1] != old.coord[1]
               for mid, old in original.graph.nodes.items())
    for before, after in zip(original.graph.edges, adapted.graph.edges):
        assert before.props == after.props
        assert before.lines == after.lines
        assert before.geometry[0] == original.graph.nodes[before.src].coord
        assert after.geometry[0] == adapted.graph.nodes[after.src].coord
        assert after.geometry[-1] == adapted.graph.nodes[after.dst].coord
        assert is_octilinear(after.geometry), (after.src, after.dst, after.geometry)
        assert after.props["traversable"] is False
        assert after.props["projectionRole"] == "non-traversable-category-guide"
    assert adapted.audit["projection"]["categoryCorridorMode"] == "stage-demand"
    assert adapted.audit["projection"]["categoryCorridorMetrics"]["guideCount"] == 60
    assert adapted.audit["projection"]["categoryCorridorMetrics"][
        "crossCategoryGuideIntersections"] == 0
    assert not adapted.audit["projection"]["categoryCorridorMetrics"][
        "nonincidentStationClearanceViolationsUnder30"]


def test_spatial_budgets_are_fixed_and_source_demand_changes_clearance(equipment):
    projection = build_system_v3(equipment, stage_demand_corridors=True)
    report = projection.audit["projection"]["categoryCorridorStageDemand"]
    assert len(report) == 10
    assert all(len(row["gaps"]) == 6 for row in report)
    assert all(abs(row["overallGapSpan"] - 624) < .001 for row in report)
    assert all(71 <= row["minGap"] <= row["maxGap"] <= 137 for row in report)
    assert any(max(row["gaps"]) - min(row["gaps"]) > 10 for row in report)
    assert max(row["crossCategoryDemand"][0] for row in report) >= 2
    assert {row["pressureBand"] for row in report} == {
        "low", "typical", "high"}
    assert {row["stageShift"] for row in report} == {-20, 0, 20}
    assert all(row["crossCategoryEdgeCount"] >= 0 for row in report)
    # Outer rails must have genuinely stage-varying vertical locations: the
    # initial fixed-height gap allocator made these paths artificially straight.
    outer = "layer-0"
    stage_ys = {
        round(node.coord[1], 4) for node in projection.graph.nodes.values()
        if node.props["layerIds"] == [outer]
    }
    assert len(stage_ys) >= 3, stage_ys


def test_demand_stage_layout_is_deterministic_and_independent_of_relation_order(equipment):
    a = build_system_v3(equipment, stage_demand_corridors=True)
    shuffled = copy.deepcopy(equipment)
    shuffled["connections"].reverse()
    b = build_system_v3(shuffled, stage_demand_corridors=True)
    assert a.graph.to_geojson() == b.graph.to_geojson()
    assert a.audit["projection"]["categoryCorridorStageDemand"] == b.audit["projection"][
        "categoryCorridorStageDemand"]


@pytest.mark.parametrize("a,b", [
    ((0, 0), (80, 30)), ((0, 0), (30, 80)),
    ((100, 100), (20, 20)), ((0, 10), (100, 10)),
    ((0, 100), (0, 10)), ((0, 0), (45, 45)),
])
def test_centered_stepped_guides_are_octilinear_and_keep_endpoints(a, b):
    points = centered_step(a, b)
    assert points[0] == a and points[-1] == b
    assert is_octilinear(points)
    assert len(points) <= 4


def test_three_channel_starter_uses_same_source_ordered_contract():
    source = json.loads(STARTER.read_text(encoding="utf-8"))
    projection = build_system_v3(source, stage_demand_corridors=True)
    assert len(projection.graph.nodes) == 19
    assert len(projection.graph.edges) == 16
    assert len(projection.audit["projection"]["categoryCorridorStageDemand"]) == 5
    assert all(len(r["gaps"]) == 2 for r in
               projection.audit["projection"]["categoryCorridorStageDemand"])
    assert all(abs(r["overallGapSpan"] - 208) < .001 for r in
               projection.audit["projection"]["categoryCorridorStageDemand"])
    assert all(is_octilinear(e.geometry) for e in projection.graph.edges)


def test_cli_staged_variant_writes_native_svg_with_integrity_certificate(tmp_path):
    out = tmp_path / "category-corridors.svg"
    cmd = [sys.executable, str(ROOT / "bin/mjourney-preview"),
           "--system-v3", "--stage-demand-corridors",
           "--source", str(EQUIPMENT), "--output", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    audit = json.loads(out.with_suffix(".audit.json").read_text())
    contract = json.loads(out.with_suffix(".research.json").read_text())
    assert audit["projection"]["categoryCorridorMode"] == "stage-demand"
    assert audit["projection"]["categoryCorridorMetrics"]["guideCount"] == 60
    assert contract["integrity"]["stationCount"] == 67
    assert contract["integrity"]["sourceRelationshipCount"] == 87
    assert contract["integrity"]["guideCount"] == 60
    assert not contract["presentation"]["categoryGuidesNavigable"]
    assert out.is_file()
