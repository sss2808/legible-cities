"""P0a source-identity and negative-provenance regression tests.

No C++ LOOM is run by this suite. Native candidate acceptance is P0b/P0c.
"""
import copy
import json
from pathlib import Path
import runpy
import unittest

from schematic.linegraph import Edge, Line, Node
from schematic.mjourney_source_integrity import (
    build_source_manifest, fingerprint, validate_projection_graph,
    verify_source_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


class SourceCertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_path = ROOT / "fixtures/mjourney/equipment-sanitized-v1.json"
        cls.raw = cls.fixture_path.read_bytes()
        cls.source = json.loads(cls.raw)
        cls.v7 = runpy.run_path(str(ROOT / "bin/mjourney-system-network"))
        cls.routes = cls.v7["ROUTES"]
        cls.manifest = build_source_manifest(cls.source, cls.routes,
                                             source_bytes=cls.raw)
        cls.seed = cls.v7["assemble"](cls.source)

    def test_frozen_source_lock_matches_exact_baseline(self):
        lock=json.loads((ROOT/"fixtures/mjourney/equipment-source-certificate-lock-v7.json").read_text())
        self.assertEqual(lock["sourceBytesSha256"], self.manifest["sourceBytesSha256"])
        self.assertEqual(lock["sourceSemanticSha256"], self.manifest["semanticSha256"])
        self.assertEqual(lock["canonicalCounts"], self.manifest["canonicalCounts"])
        self.assertEqual(lock["projectionCounts"], self.manifest["projectionCounts"])

    def test_full_canonical_source_and_selected_projection(self):
        self.assertEqual(self.manifest["canonicalCounts"],
                         {"moments": 67, "relations": 87, "stages": 10, "layers": 7})
        self.assertEqual(self.manifest["projectionCounts"],
                         {"moments": 59, "relations": 68, "lines": 11})
        self.assertEqual(set(self.manifest["projection"]["routes"]), set(self.routes))
        self.assertEqual(self.manifest["schema"], "mjourney-source-certificate/v1")
        handoffs = sorted(e["sourceEdgeId"] for e in self.manifest["projection"]["edges"]
                          if e["kind"] == "handoff")
        self.assertEqual(handoffs, ["edge71", "edge78", "edge84"])
        self.assertNotIn("edge87", [e["sourceEdgeId"] for e in
                                   self.manifest["projection"]["edges"]])
        self.assertEqual([r for r in self.manifest["canonical"]["layers"]
                          if r["id"] == "layer-0"][0]["order"], 0)

    def test_source_manifest_fingerprint_independent_of_dictionary_order(self):
        reordered = copy.deepcopy(self.source)
        reordered["moments"].reverse()
        reordered["connections"].reverse()
        reordered["layers"].reverse()
        reordered["stages"].reverse()
        variant = build_source_manifest(reordered, self.routes)
        self.assertEqual(variant["semanticSha256"], self.manifest["semanticSha256"])
        self.assertEqual(fingerprint({"b": 2, "a": 1}),
                         fingerprint({"a": 1, "b": 2}))

    def test_approved_fixture_and_seed_are_certified(self):
        review = verify_source_manifest(self.source, self.manifest, self.routes,
                                        source_bytes=self.raw)
        self.assertTrue(review["passed"], review)
        cert = validate_projection_graph(self.seed, self.manifest)
        self.assertTrue(cert["passed"], cert)
        self.assertTrue(cert["sourceEdgeProvenanceVerified"], cert)
        self.assertEqual(cert["stationCount"], 59)
        self.assertEqual(cert["lineCount"], 11)

    def test_changed_directed_relation_fails_source_review(self):
        altered = copy.deepcopy(self.source)
        altered["connections"][0]["fromId"], altered["connections"][0]["toId"] = (
            altered["connections"][0]["toId"], altered["connections"][0]["fromId"])
        report = verify_source_manifest(altered, self.manifest, self.routes)
        self.assertFalse(report["passed"])

    def test_changed_stage_or_layer_fails_source_review(self):
        altered = copy.deepcopy(self.source)
        altered["moments"][0]["stageId"] = "stage-2"
        self.assertFalse(verify_source_manifest(altered, self.manifest, self.routes)["passed"])
        altered = copy.deepcopy(self.source)
        altered["moments"][0]["layerId"] = "layer-2"
        self.assertFalse(verify_source_manifest(altered, self.manifest, self.routes)["passed"])

    def test_changed_route_membership_fails_source_review(self):
        altered = copy.deepcopy(self.routes)
        altered["technical_feasibility"].pop()
        report = verify_source_manifest(self.source, self.manifest, altered)
        self.assertFalse(report["passed"], report)

    def test_nontraversable_source_edge_cannot_become_route(self):
        altered = copy.deepcopy(self.routes)
        altered["technical_feasibility"].append("edge87")
        with self.assertRaises(ValueError):
            build_source_manifest(self.source, altered)

    def test_duplicate_canonical_moment_rejected(self):
        altered = copy.deepcopy(self.source)
        altered["moments"].append(copy.deepcopy(altered["moments"][0]))
        with self.assertRaisesRegex(ValueError, "repeated identity"):
            build_source_manifest(altered, self.routes)

    def test_missing_station_graph_fails(self):
        graph = copy.deepcopy(self.seed)
        del graph.nodes["eq01"]
        report = validate_projection_graph(graph, self.manifest)
        self.assertFalse(report["passed"], report)
        self.assertIn("missing stations", " ".join(report["errors"]))

    def test_duplicated_station_identity_graph_fails(self):
        graph = copy.deepcopy(self.seed)
        original = graph.nodes["eq01"]
        graph.nodes["temporary-helper"] = Node(id="temporary-helper",
             coord=original.coord, station_id=original.station_id,
             station_label=original.station_label, props=dict(original.props))
        report = validate_projection_graph(graph, self.manifest)
        self.assertFalse(report["passed"], report)
        self.assertIn("duplicate canonical station_id", report["errors"])

    def test_dropped_source_connection_fails(self):
        graph = copy.deepcopy(self.seed)
        graph.edges = [e for e in graph.edges
                       if e.props.get("sourceEdgeIds") != ["edge01"]]
        report = validate_projection_graph(graph, self.manifest)
        self.assertFalse(report["passed"], report)
        self.assertTrue(any("missing" in e for e in report["errors"]), report)

    def test_unapproved_transfer_fails_even_if_both_stations_exist(self):
        graph = copy.deepcopy(self.seed)
        graph.edges.append(Edge(
            src="eq01", dst="eq67", geometry=[graph.nodes["eq01"].coord,
                                             graph.nodes["eq67"].coord],
            lines=[Line("direct_customer_led", "Direct customer-led")],
            props={"sourceEdgeIds": ["invented-transfer"], "sourceKind": "handoff"}))
        review = validate_projection_graph(graph, self.manifest)
        self.assertFalse(review["passed"], review)
        self.assertTrue(any("unapproved" in e for e in review["errors"]), review)

    def test_changed_line_membership_fails(self):
        graph = copy.deepcopy(self.seed)
        edge = next(e for e in graph.edges
                    if e.props.get("sourceEdgeIds") == ["edge01"])
        edge.lines = [l for l in edge.lines if l.id != "direct_customer_led"]
        report = validate_projection_graph(graph, self.manifest)
        self.assertFalse(report["passed"], report)
        self.assertIn("per-edge route membership changed", " ".join(report["errors"]))

    def test_changed_stage_or_layer_on_projected_graph_fails(self):
        graph = copy.deepcopy(self.seed)
        graph.nodes["eq01"].props["stageId"] = "stage-7"
        report = validate_projection_graph(graph, self.manifest)
        self.assertFalse(report["passed"], report)
        self.assertIn("incorrect stageId", " ".join(report["errors"]))
        graph = copy.deepcopy(self.seed)
        graph.nodes["eq01"].props["sourceLayerId"] = "layer-6"
        report = validate_projection_graph(graph, self.manifest)
        self.assertFalse(report["passed"], report)
        self.assertIn("incorrect sourceLayerId", " ".join(report["errors"]))

    def test_spoofed_relation_kind_fails(self):
        graph = copy.deepcopy(self.seed)
        edge = next(e for e in graph.edges
                    if e.props.get("sourceEdgeIds") == ["edge01"])
        edge.props["sourceKind"] = "handoff"
        report = validate_projection_graph(graph, self.manifest)
        self.assertFalse(report["passed"], report)
        self.assertIn("source relationship kind changed", " ".join(report["errors"]))

    def test_reversed_cartographic_source_endpoint_fails(self):
        graph = copy.deepcopy(self.seed)
        edge = next(e for e in graph.edges
                    if e.props.get("sourceEdgeIds") == ["edge01"])
        edge.src, edge.dst = edge.dst, edge.src
        report = validate_projection_graph(graph, self.manifest)
        self.assertFalse(report["passed"], report)
        self.assertIn("directed source endpoints changed", " ".join(report["errors"]))

    def test_transient_node_ids_do_not_change_semantic_graph_fingerprint(self):
        original = validate_projection_graph(self.seed, self.manifest)
        graph = copy.deepcopy(self.seed)
        rename = {nid: f"pointer-{i:04d}" for i, nid in enumerate(graph.nodes)}
        graph.nodes = {rename[nid]: Node(id=rename[nid], coord=node.coord,
                       station_id=node.station_id, station_label=node.station_label,
                       props=dict(node.props)) for nid,node in graph.nodes.items()}
        for edge in graph.edges:
            edge.src, edge.dst = rename[edge.src], rename[edge.dst]
        review = validate_projection_graph(graph, self.manifest)
        self.assertTrue(review["passed"], review)
        self.assertEqual(review["graphSemanticSha256"],
                         original["graphSemanticSha256"])

    def test_geometry_only_helper_is_accepted_as_post_solver_track(self):
        graph = copy.deepcopy(self.seed)
        original = validate_projection_graph(graph, self.manifest)
        edge = graph.edges.pop(0)
        p0, p1 = graph.nodes[edge.src].coord, graph.nodes[edge.dst].coord
        mid = ((p0[0]+p1[0])/2, (p0[1]+p1[1])/2)
        helper = "opaque-geom-vertex-123"
        graph.nodes[helper] = Node(id=helper, coord=mid)
        graph.edges.extend([
            Edge(src=edge.src, dst=helper, geometry=[p0, mid],
                 lines=list(edge.lines)),
            Edge(src=helper, dst=edge.dst, geometry=[mid, p1],
                 lines=list(edge.lines)),
        ])
        result = validate_projection_graph(graph, self.manifest,
                                           require_source_edge_ids=False)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["graphSemanticSha256"],
                         original["graphSemanticSha256"])
        self.assertFalse(result["sourceEdgeProvenanceVerified"])
        self.assertEqual(result["directedSourceAuthority"], "frozen_manifest_only")
        self.assertTrue(result["warnings"])

    def test_label_change_does_not_change_stable_route_id(self):
        graph = copy.deepcopy(self.seed)
        for edge in graph.edges:
            edge.lines = [Line(l.id, "Display title changed", l.color)
                          for l in edge.lines]
        result = validate_projection_graph(graph, self.manifest)
        self.assertTrue(result["passed"], result)


if __name__ == "__main__":
    unittest.main()
