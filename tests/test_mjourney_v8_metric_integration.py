"""Full ten-stage metric adapter regression, independent from native optimization.

V8 P0b is an engineering proof on a V7 *diagnostic route* projection; the
product's final layer-line semantic contract remains separate and authoritative.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import runpy
import unittest

from schematic.mjourney_projection import to_solver_point, from_solver_point
from schematic.crs import to_mercator
from schematic.mjourney_source_integrity import build_source_manifest, validate_projection_graph
from schematic.linegraph import Edge, Line, LineGraph, Node

ROOT = Path(__file__).resolve().parents[1]


class TenStageMetricBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v7 = runpy.run_path(str(ROOT / "bin/mjourney-system-network"))
        cls.raw = (ROOT / "fixtures/mjourney/equipment-sanitized-v1.json").read_bytes()
        cls.source = json.loads(cls.raw)
        cls.seed = cls.v7["assemble"](cls.source)
        cls.manifest = build_source_manifest(cls.source, cls.v7["ROUTES"],
                                             source_bytes=cls.raw)

    def test_full_projection_source_integrity(self):
        report = validate_projection_graph(self.seed, self.manifest)
        self.assertTrue(report["passed"], report)
        self.assertEqual((len(self.seed.stations), len(self.seed.edges)), (59, 68))
        self.assertEqual(self.manifest["projectionCounts"]["lines"], 11)

    def test_exact_bridge_preserves_full_station_and_route_geometry(self):
        restored = self.v7["from_solver"](self.v7["to_solver"](self.seed))
        self.assertEqual(set(restored.nodes), set(self.seed.nodes))
        self.assertEqual([(e.src, e.dst, [l.id for l in e.lines],
                           e.props["sourceEdgeIds"])
                          for e in restored.edges],
                         [(e.src, e.dst, [l.id for l in e.lines],
                           e.props["sourceEdgeIds"])
                          for e in self.seed.edges])
        self.assertEqual([len(e.geometry) for e in restored.edges],
                         [len(e.geometry) for e in self.seed.edges])
        for n in self.seed.nodes:
            for got, expected in zip(restored.nodes[n].coord, self.seed.nodes[n].coord):
                self.assertAlmostEqual(got, expected, delta=1e-7)
        for after, before in zip(restored.edges, self.seed.edges):
            for actual, expected in zip(after.geometry, before.geometry):
                self.assertAlmostEqual(actual[0], expected[0], delta=1e-7)
                self.assertAlmostEqual(actual[1], expected[1], delta=1e-7)
        self.assertTrue(validate_projection_graph(restored, self.manifest)["passed"])

    def test_synthetic_metric_axes_remain_isotropic_across_all_ten_stages(self):
        xs = [n.coord[0] for n in self.seed.nodes.values()]
        ys = [n.coord[1] for n in self.seed.nodes.values()]
        x0,x1=min(xs),max(xs)
        y0,y1=min(ys),max(ys)
        self.assertGreater(x1-x0,2500)
        start=to_mercator(to_solver_point((x0,y0)))
        horiz=to_mercator(to_solver_point((x1,y0)))
        vert=to_mercator(to_solver_point((x0,y1)))
        unit=(horiz[0]-start[0])/(x1-x0)
        self.assertAlmostEqual((vert[1]-start[1])/(y1-y0),unit,delta=1e-7)

    def test_weighted_angle_gate_accepts_short_non_octilinear_noise(self):
        # Segment A: 1000 units exactly horizontal. Segment B: 1 unit
        # diagonal at 22.5 degrees. A segment-count gate would score 50%.
        graph=LineGraph(nodes={
            "a":Node("a",(0.0,0.0),station_id="a"),
            "b":Node("b",(1000.0,0.0),station_id="b")},
            edges=[Edge("a","b",[(0.0,0.0),(1000.0,0.0),
              (1000.0+math.cos(math.pi/8),math.sin(math.pi/8))],
              [Line("l","L")])])
        score=self.v7["poly_review"](graph)
        self.assertTrue(score["octilinear"],score)
        self.assertGreater(score["lengthWeightedFraction"],0.995)
        self.assertEqual(score["minimumAcceptedFraction"],0.995)

    def test_weighted_angle_gate_rejects_significant_wrong_angle(self):
        graph=LineGraph(nodes={
            "a":Node("a",(0.0,0.0),station_id="a"),
            "b":Node("b",(1000.0,0.0),station_id="b")},
            edges=[Edge("a","b",[(0,0),(1000,0),(1500,200)],
              [Line("l","L")])])
        score=self.v7["poly_review"](graph)
        self.assertFalse(score["octilinear"],score)

    def test_no_inverse_latitude_approximation_left_in_adapter(self):
        program=(ROOT/"bin/mjourney-system-network").read_text()
        self.assertNotIn("_LOCAL_LONGITUDE_SCALE",program)
        self.assertIn("graph.reproject(to_solver_point)",program)
        self.assertIn("graph.reproject(from_solver_point)",program)
        self.assertNotIn('min(dx,dy)>3',program)

    def test_no_native_attempt_from_projection_unit_suite(self):
        # Unit tests only validate exact geometry and source contracts.
        # They do not certify loom/octi, which runs in the dedicated native job.
        self.assertTrue(callable(self.v7["native_geometry"]))


if __name__=="__main__":
    unittest.main()
