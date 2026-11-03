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
import tempfile
from unittest.mock import patch

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

    def test_grid_variant_review_cannot_auto_accept_invalid_station_adjacency(self):
        probe=runpy.run_path(str(ROOT/"bin/mjourney-octi-constraint-probe"))
        candidate=copy.deepcopy(self.seed)
        original=probe["review"]("seed",candidate,self.seed,self.source,
                                 self.manifest,self.v7)
        self.assertTrue(original["accepted"],original)
        edge=next(e for e in candidate.edges
                  if e.props.get("sourceEdgeIds")==["edge01"])
        edge.dst="eq67"
        edge.geometry[-1]=candidate.nodes["eq67"].coord
        rejected=probe["review"]("tampered",candidate,self.seed,self.source,
                                 self.manifest,self.v7)
        self.assertFalse(rejected["accepted"],rejected)
        self.assertFalse(rejected["perLineAdjacencyPreserved"])

    def test_grid_variant_review_rejects_stage_order_regression(self):
        probe=runpy.run_path(str(ROOT/"bin/mjourney-octi-constraint-probe"))
        candidate=copy.deepcopy(self.seed)
        mid=next(n.id for n in candidate.stations
                 if n.props.get("stageId")=="stage-5")
        _,y=candidate.nodes[mid].coord
        candidate.nodes[mid].coord=(950.0,y)
        rejected=probe["review"]("invalid stage",candidate,self.seed,self.source,
                                 self.manifest,self.v7)
        self.assertFalse(rejected["accepted"],rejected)
        self.assertTrue(rejected["perLineAdjacencyPreserved"])
        self.assertFalse(rejected["stageOrderPreserved"])

    def test_line_order_only_mode_accepts_source_preserving_graph_without_octi(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(self.v7["loom"],"run",
                return_value=self.v7["to_solver"](self.seed).to_geojson()) as runner:
                graph,status=self.v7["native_line_order_geometry"](
                    self.seed,self.source,Path(td)/"line",30,self.manifest)
            runner.assert_called_once()
            self.assertEqual(runner.call_args.args[0],"loom")
            self.assertTrue(status["lineOrderUsed"],status)
            self.assertFalse(status["used"])
            self.assertFalse(status["octiAttempted"])
            self.assertEqual(self.v7["adjacency"](graph),self.v7["adjacency"](self.seed))

    def test_line_order_only_mode_falls_back_on_fabricated_track(self):
        bad=copy.deepcopy(self.seed)
        edge=next(e for e in bad.edges if e.props.get("sourceEdgeIds")==["edge01"])
        edge.dst="eq67"
        edge.geometry[-1]=bad.nodes["eq67"].coord
        with tempfile.TemporaryDirectory() as td:
            with patch.object(self.v7["loom"],"run",
                return_value=self.v7["to_solver"](bad).to_geojson()):
                graph,status=self.v7["native_line_order_geometry"](
                    self.seed,self.source,Path(td)/"line",30,self.manifest)
            self.assertFalse(status["lineOrderUsed"])
            self.assertFalse(status["used"])
            self.assertFalse(status["adjacencyPreserved"])
            self.assertEqual(self.v7["adjacency"](graph),self.v7["adjacency"](self.seed))

    def source_track_svg_with_solver_pointers(self):
        """Build the frozen diagnostic line-track matrix with volatile node IDs."""
        import xml.etree.ElementTree as ET
        ns="{http://www.w3.org/2000/svg}"
        root=ET.Element(ns+"svg")
        pointer_by_moment={n.station_id:f"0x{i+1:08x}"
                           for i,n in enumerate(self.seed.stations)}
        by_pointer={v:k for k,v in pointer_by_moment.items()}
        edges={e["id"]:e for e in self.source["connections"]}
        for lid,chain in self.v7["ROUTES"].items():
            group=ET.SubElement(root,ns+"g",{
                "class":"line","data-line":self.v7["LINES"][lid].label})
            for eid in chain:
                edge=edges[eid]
                ET.SubElement(group,ns+"path",{
                    "data-src":pointer_by_moment[edge["fromId"]],
                    "data-dst":pointer_by_moment[edge["toId"]]})
        return root,by_pointer

    def test_line_order_svg_restores_all_108_unique_source_line_memberships(self):
        root,by_pointer=self.source_track_svg_with_solver_pointers()
        count=self.v7["restore_line_order_track_provenance"](
            root,self.source,by_pointer)
        self.assertEqual(count,sum(len(chain) for chain in self.v7["ROUTES"].values()))
        edges={e["id"]:e for e in self.source["connections"]}
        ns="{http://www.w3.org/2000/svg}"
        seen=set()
        for group in root.iter(ns+"g"):
            lid=next(lid for lid,line in self.v7["LINES"].items()
                     if line.label==group.get("data-line"))
            for path in group.findall(ns+"path"):
                eid=path.get("data-source-edge-id")
                edge=edges[eid]
                self.assertEqual(path.get("data-line-id"),lid)
                self.assertEqual(path.get("data-source-from-id"),edge["fromId"])
                self.assertEqual(path.get("data-source-to-id"),edge["toId"])
                self.assertEqual((path.get("data-src"),path.get("data-dst")),
                                 (edge["fromId"],edge["toId"]))
                self.assertNotIn("0x",path.get("data-src"))
                self.assertNotIn("0x",path.get("data-dst"))
                self.assertNotIn((lid,eid),seen)
                seen.add((lid,eid))
        self.assertEqual(len(seen),count)

    def test_line_order_svg_keeps_authored_direction_when_drawn_reversed(self):
        root,by_pointer=self.source_track_svg_with_solver_pointers()
        ns="{http://www.w3.org/2000/svg}"
        path=next(root.iter(ns+"path"))
        a,b=path.get("data-src"),path.get("data-dst")
        path.set("data-src",b)
        path.set("data-dst",a)
        self.v7["restore_line_order_track_provenance"](root,self.source,by_pointer)
        self.assertEqual((path.get("data-src"),path.get("data-dst")),("eq02","eq01"))
        self.assertEqual((path.get("data-source-from-id"),
                          path.get("data-source-to-id")),("eq01","eq02"))
        self.assertEqual(path.get("data-source-edge-id"),"edge01")

    def test_line_order_svg_rejects_unknown_pointer_or_invented_track(self):
        ns="{http://www.w3.org/2000/svg}"
        root,by_pointer=self.source_track_svg_with_solver_pointers()
        path=next(root.iter(ns+"path"))
        path.set("data-src","0xnot_a_station")
        with self.assertRaisesRegex(ValueError,"lacks canonical Moment"):
            self.v7["restore_line_order_track_provenance"](
                root,self.source,by_pointer)

        root,by_pointer=self.source_track_svg_with_solver_pointers()
        path=next(root.iter(ns+"path"))
        eq67_pointer=next(pointer for pointer,mid in by_pointer.items()
                          if mid=="eq67")
        path.set("data-dst",eq67_pointer)
        with self.assertRaisesRegex(ValueError,"unmatched or repeated"):
            self.v7["restore_line_order_track_provenance"](
                root,self.source,by_pointer)

    def test_line_order_svg_rejects_duplicated_track_membership(self):
        ns="{http://www.w3.org/2000/svg}"
        root,by_pointer=self.source_track_svg_with_solver_pointers()
        paths=list(root.iter(ns+"path"))
        paths[1].set("data-src",paths[0].get("data-src"))
        paths[1].set("data-dst",paths[0].get("data-dst"))
        with self.assertRaisesRegex(ValueError,"unmatched or repeated"):
            self.v7["restore_line_order_track_provenance"](
                root,self.source,by_pointer)


    def test_coordinate_roundtrip_keeps_all_station_identities(self):
        transformed=self.v7["from_solver"](self.v7["to_solver"](self.seed))
        report=self.analyze(transformed,transformed)
        self.assertIsNone(report["firstHardGateFailure"],report)
        self.assertEqual(report["stages"]["loom"]["stations"],59)
        self.assertEqual(report["stages"]["loom"]["graphEdges"],68)
        self.assertEqual(report["stages"]["octi"]["lineIds"],sorted(self.v7["LINES"]))


if __name__=="__main__":
    unittest.main()
