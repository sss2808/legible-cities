"""Stage-differential tests with controlled source-graph mutations.

These tests use the V7 diagnostic *fixture*, not a live research package.
LOOM runs separately in the exact-head CI native job.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import runpy
import unittest

from schematic.mjourney_source_integrity import build_source_manifest
from schematic.linegraph import LineGraph

ROOT=Path(__file__).resolve().parents[1]


class StageDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v7=runpy.run_path(str(ROOT/"bin/mjourney-system-network"))
        cls.diff=runpy.run_path(str(ROOT/"bin/mjourney-native-stage-diff"))
        src=(ROOT/"fixtures/mjourney/equipment-sanitized-v1.json").read_bytes()
        cls.source=json.loads(src)
        cls.seed=cls.v7["assemble"](cls.source)
        cls.manifest=build_source_manifest(cls.source,cls.v7["ROUTES"],source_bytes=src)

    def analyze(self,loom,octi):
        return self.diff["analyze"](self.source,self.seed,self.manifest,
                                    self.seed,loom,octi,self.v7)

    def test_identical_frozen_snapshots_have_no_stage_failure(self):
        report=self.analyze(copy.deepcopy(self.seed),copy.deepcopy(self.seed))
        self.assertIsNone(report["firstHardGateFailure"],report)
        self.assertTrue(report["nativeAccepted"],report)
        for name in ("input","loom","octi"):
            self.assertTrue(report["stages"][name]["perLineAdjacencyPreserved"])
            self.assertTrue(report["stages"][name]["stageOrder"]["preserved"])
            self.assertTrue(report["stages"][name]["semanticAudit"]["passed"])

    def test_detects_first_adjacency_change_in_loom_not_octi(self):
        bad=copy.deepcopy(self.seed)
        target=next(e for e in bad.edges
                    if e.props.get("sourceEdgeIds")==["edge01"])
        target.dst="eq67"  # an unauthorized endpoint change
        target.geometry[-1]=bad.nodes["eq67"].coord
        report=self.analyze(bad,copy.deepcopy(bad))
        self.assertEqual(report["firstHardGateFailure"],"loom",report)
        self.assertTrue(report["stages"]["input"]["perLineAdjacencyPreserved"])
        self.assertFalse(report["stages"]["loom"]["perLineAdjacencyPreserved"])
        self.assertTrue(report["transitions"]["inputToLoom"]["perLineAdjacencyChanged"])

    def test_detects_first_adjacency_change_in_octi(self):
        changed=copy.deepcopy(self.seed)
        target=next(e for e in changed.edges
                    if e.props.get("sourceEdgeIds")==["edge01"])
        target.dst="eq67"
        target.geometry[-1]=changed.nodes["eq67"].coord
        report=self.analyze(copy.deepcopy(self.seed),changed)
        self.assertEqual(report["firstHardGateFailure"],"octi",report)
        self.assertFalse(report["transitions"]["inputToLoom"]["perLineAdjacencyChanged"])
        self.assertTrue(report["transitions"]["loomToOcti"]["perLineAdjacencyChanged"])

    def test_stage_boundary_overlap_detected(self):
        changed=copy.deepcopy(self.seed)
        # Move one canonical stage-5 station far into stage-4 in an otherwise
        # source-adjacency-preserving graph; this is NOT permitted acceptance.
        mid=next(n.id for n in changed.stations if n.props.get("stageId")=="stage-5")
        x,y=changed.nodes[mid].coord
        changed.nodes[mid].coord=(950.0,y)
        report=self.analyze(changed,changed)
        self.assertEqual(report["firstHardGateFailure"],"loom")
        self.assertTrue(report["stages"]["loom"]["perLineAdjacencyPreserved"])
        self.assertFalse(report["stages"]["loom"]["stageOrder"]["preserved"])

    def test_line_order_difference_is_reported_without_fabricating_source_edge(self):
        swapped=copy.deepcopy(self.seed)
        edge=next(e for e in swapped.edges if len(e.lines)>1)
        edge.lines.reverse()
        report=self.analyze(swapped,copy.deepcopy(swapped))
        self.assertIsNone(report["firstHardGateFailure"],report)
        self.assertTrue(report["stages"]["loom"]["semanticAudit"]["passed"])
        self.assertTrue(report["transitions"]["inputToLoom"]["directStationEdgeOrderChanges"])

    def test_coordinate_roundtrip_keeps_all_station_identities(self):
        transformed=self.v7["from_solver"](self.v7["to_solver"](self.seed))
        report=self.analyze(transformed,transformed)
        self.assertIsNone(report["firstHardGateFailure"],report)
        self.assertEqual(report["stages"]["loom"]["stations"],59)
        self.assertEqual(report["stages"]["loom"]["graphEdges"],68)
        self.assertEqual(report["stages"]["octi"]["lineIds"],sorted(self.v7["LINES"]))


if __name__=="__main__":
    unittest.main()
