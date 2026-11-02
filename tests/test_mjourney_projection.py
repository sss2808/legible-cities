"""Regression tests for M-Journey's exact Web Mercator / LOOM bridge.

The canonical research map is ordinal, not geographic. These tests check
geometry without running the C++ binaries; the workflow separately runs LOOM
and rejects any unexpected station-line adjacency or stage-order changes.
"""
from __future__ import annotations

import math
import unittest

from schematic.crs import R, to_mercator
from schematic.linegraph import Edge, Line, LineGraph, Node
from schematic.mjourney_projection import from_solver_point, to_solver_point


class MercatorBridgeTests(unittest.TestCase):
    def test_diagram_to_solver_roundtrip(self):
        for point in [
            (0.0, 0.0), (150.0, 465.0), (2450.0, 650.0),
            (2170.0, 260.0), (-1600.0, -2300.0), (8000.0, 6000.0),
        ]:
            with self.subTest(point=point):
                result = from_solver_point(to_solver_point(point))
                for actual, expected in zip(result, point):
                    self.assertAlmostEqual(actual, expected, delta=1e-7)

    def test_metric_axes_are_isotropic_even_over_large_vertical_extents(self):
        start = to_mercator(to_solver_point((300, 400)))
        horiz = to_mercator(to_solver_point((1100, 400)))
        diag = to_mercator(to_solver_point((1100, 1200)))
        xmetres = horiz[0] - start[0]
        ymetres = diag[1] - horiz[1]
        self.assertAlmostEqual(xmetres, ymetres, delta=1e-6)
        self.assertAlmostEqual(diag[0] - horiz[0], 0, delta=1e-6)

    def test_no_false_geographic_meaning(self):
        anchor = to_solver_point((0, 0))
        self.assertAlmostEqual(anchor[0], 8.0, places=10)
        self.assertAlmostEqual(anchor[1], 48.0, places=10)

    def test_roundtrip_retains_lines_and_intermediate_polyline_vertices(self):
        nodes = {
            "n1": Node(id="n1", coord=(200, 400), station_id="eq31",
                       station_label="Funding authorized"),
            "n2": Node(id="n2", coord=(750, 500), station_id="eq37",
                       station_label="Vendor selected"),
        }
        a=Line("a","A&E / EPC","#ef6394")
        b=Line("b","Direct customer-led","#36c9dc")
        graph=LineGraph(nodes,[Edge(src="n1",dst="n2",
                        geometry=[(200,400),(400,400),(500,500),(750,500)],
                        lines=[a,b],props={"sourceEdgeIds":["edge44"]})])
        converted=graph.reproject(to_solver_point).reproject(from_solver_point)
        self.assertEqual({x.station_id for x in converted.stations},{"eq31","eq37"})
        self.assertEqual([line.id for line in converted.edges[0].lines],["a","b"])
        self.assertEqual(converted.edges[0].props["sourceEdgeIds"],["edge44"])
        self.assertEqual(len(converted.edges[0].geometry),4)
        for got,want in zip(converted.edges[0].geometry,graph.edges[0].geometry):
            self.assertAlmostEqual(got[0],want[0],delta=1e-7)
            self.assertAlmostEqual(got[1],want[1],delta=1e-7)

    def test_legacy_latitude_approximation_had_measurable_metric_drift(self):
        # Old coordinate bridge was lon=8+x/(2500*cos48), lat=48+y/2500.
        x,y=(1200,650)
        legacy=(8+x/(2500*math.cos(math.radians(48))),48+y/2500)
        origin=to_mercator((8,48))
        unit=(math.pi*R/180)/(2500*math.cos(math.radians(48)))
        legacy_y=(to_mercator(legacy)[1]-origin[1])/unit
        fixed_y=from_solver_point(to_solver_point((x,y)))[1]
        self.assertGreater(abs(legacy_y-y),1.0)
        self.assertLess(abs(fixed_y-y),1e-7)


if __name__=="__main__":
    unittest.main()
