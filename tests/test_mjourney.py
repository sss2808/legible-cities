"""Contract tests for the M-Journey research-to-transit projection.

These tests assert identity and provenance, not owner approval of layout.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
from pathlib import Path

import pytest

from schematic import animate
from schematic import mjourney
from schematic import render as svg_renderer
from schematic.linegraph import LineGraph

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/mjourney/equipment-sanitized-v1.json"


@pytest.fixture
def source():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_complete_public_fixture_retained(source):
    out = mjourney.build_projection(source)
    assert len(source["moments"]) == 67
    assert len(source["connections"]) == 87
    assert len(source["stages"]) == 10
    assert len(source["layers"]) == 7
    assert len(out.graph.nodes) == 28
    assert len(out.graph.labels) == 7
    assert out.audit["canonical"]["momentCount"] == 67
    assert out.audit["canonical"]["connectionCount"] == 87
    assert out.audit["projection"]["transfers"] == []
    assert all("Stage " not in s["shortName"] for s in out.stages)


def test_guide_continuity_does_not_invent_source_edges(source):
    out = mjourney.build_projection(source)
    edges = {e["id"]: e for e in source["connections"]}
    moments = {m["id"]: m for m in source["moments"]}
    for edge in out.graph.edges:
        assert len(edge.lines) == 1
        assert moments[edge.src]["layerId"] == moments[edge.dst]["layerId"]
        assert edge.props["layerId"] == moments[edge.src]["layerId"]
        refs = edge.props["sourceEdgeIds"]
        if refs:
            assert len(refs) == 1
            original = edges[refs[0]]
            assert (original["fromId"], original["toId"]) == (edge.src, edge.dst)
            assert original["kind"] in {"sequence", "branch", "convergence", "handoff"}
            assert edge.props["traversable"] is True
        else:
            assert edge.props["traversable"] is False
            assert edge.props["projectionRole"] == "non-traversable-organizational-guide"
    assert out.audit["projection"]["nonTraversableGuides"] > 0


def test_editorial_source_path_candidates_not_silently_approved(source):
    reports = mjourney.audit_editorial_paths(source)
    assert len(reports) == 24
    assert all(r["directedChain"] for r in reports)
    assert all(not r["approvedForRendering"] for r in reports)
    assert any("dependency is not route travel" in p
               for r in reports for p in r["problems"])
    assert any("lifecycle return needs separate treatment" in p
               for r in reports for p in r["problems"])


def test_rejects_bad_moment_and_connection_ids(source):
    invalid = copy.deepcopy(source)
    invalid["connections"][0]["toId"] = "fictitious"
    with pytest.raises(mjourney.ProjectionError, match="missing endpoint"):
        mjourney.build_projection(invalid)
    invalid = copy.deepcopy(source)
    invalid["moments"].append(dict(invalid["moments"][0]))
    with pytest.raises(mjourney.ProjectionError, match="duplicate moment"):
        mjourney.build_projection(invalid)
    invalid = copy.deepcopy(source)
    invalid["curatedStationIds"].append("unknown")
    with pytest.raises(mjourney.ProjectionError, match="unknown curated moments"):
        mjourney.build_projection(invalid)


def test_generated_linegraph_roundtrip_preserves_identity_and_classification(source):
    out = mjourney.build_projection(source)
    # The public model serializes and parses the same FeatureCollection.
    graph = LineGraph.from_geojson(out.graph.to_geojson())
    assert set(graph.nodes) == set(out.graph.nodes)
    assert len(graph.edges) == len(out.graph.edges)
    assert graph.labels == out.graph.labels
    assert [e.props["projectionRole"] for e in graph.edges] == [
        e.props["projectionRole"] for e in out.graph.edges
    ]


def test_original_fork_renderer_and_empty_timetable_can_read_projection(source):
    out = mjourney.build_projection(source)
    order = [l["name"] for l in out.layers]
    render = svg_renderer.render(out.graph, width=1650, line_order=order)
    assert "<svg" in render.svg
    assert render.tracks
    assert set(render.colors) == set(order)
    anim = animate.build(render, out.graph, [], date=dt.date(2026, 11, 2),
                         line_order=order)
    data = anim.to_json()
    assert data["trips"] == []
    assert data["paths"] == []
    assert len(data["linear"]["lines"]) == 7
    # Timetable controls and route finding still require a dedicated no-service
    # viewer mode. Do not deploy this generated test page in the portfolio.



def test_source_connected_full_network_is_octilinear_and_has_no_invented_edges(source):
    out = mjourney.build_network_projection(source, full=True)
    originals = {e["id"]: e for e in source["connections"]}
    assert len(out.graph.nodes) == 67
    assert len(out.graph.edges) == 83
    assert len(out.graph.labels) == 7
    assert out.audit["projection"]["crossLayerConnectionCount"] == 61
    assert out.audit["projection"]["inferredConnections"] == 0
    assert len(out.audit["projection"]["excludedConnections"]) == 4
    for edge in out.graph.edges:
        assert len(edge.props["sourceEdgeIds"]) == 1
        original = originals[edge.props["sourceEdgeIds"][0]]
        assert (edge.src, edge.dst) == (original["fromId"], original["toId"])
        assert original["kind"] in {"sequence", "branch", "convergence", "handoff"}
        assert edge.props["projectionRole"] == "authored-directed-journey-connection"
        assert edge.props["crossLayer"] == (
            out.graph.nodes[edge.src].props["layerId"] !=
            out.graph.nodes[edge.dst].props["layerId"]
        )
        assert edge.geometry[0] == out.graph.nodes[edge.src].coord
        assert edge.geometry[-1] == out.graph.nodes[edge.dst].coord
        for a, b in zip(edge.geometry, edge.geometry[1:]):
            dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
            assert dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-6


def test_source_connected_focused_network_still_has_real_cross_swimlane_routes(source):
    out = mjourney.build_network_projection(source)
    selected = set(out.audit["projection"]["renderedEdgeIds"])
    assert len(selected) < 83
    assert len(out.graph.nodes) >= 40
    assert out.audit["projection"]["crossLayerConnectionCount"] >= 30
    for edge in out.graph.edges:
        assert edge.props["sourceEdgeIds"][0] in selected
        assert edge.props["traversable"] is True
    assert not any(e.props.get("sourceKind") in {"dependency", "lifecycle_return"}
                   for e in out.graph.edges)


def test_native_dark_compatible_viewer_removes_timetable_affordances(source):
    # The HTML is still the original Legible Cities interactive Schematic/Linear
    # viewer. The mode-specific presentation only hides train/passenger controls.
    script = Path(__file__).resolve().parents[1] / "bin/mjourney-preview"
    # Extensionless script can be loaded with a SourceFileLoader.
    import importlib.util
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader("mjourney_preview", str(script))
    mod_spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(mod_spec)
    loader.exec_module(module)
    out = mjourney.build_network_projection(source)
    result = svg_renderer.render(out.graph, width=1850,
                                 style=svg_renderer.Style(themed=True,
                                                          background="#1f1915",
                                                          label_color="#f2ede6"))
    anim = animate.build(result, out.graph, [], date=dt.date(2026, 11, 2))
    html = module.viewer_for_journey(animate.texts(
        anim, result.svg, stem="mjourney", title="M-Journey",
    )["mjourney.html"])
    assert 'data-mjourney' in html
    assert 'id="view-map"' in html
    assert 'id="view-linear"' in html
    assert 'id="line-toggles"' in html
    assert 'id="labels-toggle"' in html
    assert 'header .bar:nth-of-type(2)' in html
    assert 'e.stopImmediatePropagation()' in html
    assert not anim.trips
