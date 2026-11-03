"""Chromium smoke and screenshots for isolated fork System research viewer.

Run only after generating out/system-browser.html; not imported by normal pytest.
All assertions target sanitized public data, no private Dovetail calls.
"""
from __future__ import annotations
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[2]
VIEWER = ROOT / "out/system-browser.html"
OUT = ROOT / "out"


def main():
    from playwright.sync_api import sync_playwright  # browser CI only; pytest collection needs no browser
    assert VIEWER.is_file(), "Generate out/system-browser.html first"
    issues = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 950, "height": 520}, device_scale_factor=1)
        page.on("pageerror", lambda err: issues.append(str(err)))
        page.goto(VIEWER.as_uri(), wait_until="load")
        picker = page.locator("#mj-moment-picker")
        picker.wait_for(timeout=12000)
        assert picker.locator("option").count() == 68, "67 moments plus placeholder"
        assert not page.locator("#view-linear").is_visible()
        assert not page.locator("header .back").is_visible()
        assert page.locator("#line-count").inner_text() == "7 of 7"
        category_chips = page.locator("#line-toggles .chip")
        assert category_chips.count() == 7
        category_chips.first.click()
        assert page.locator("#line-count").inner_text() == "6 of 7"
        category_chips.first.click()
        assert page.locator("#line-count").inner_text() == "7 of 7"
        # The System scene has ten original stage headings aligned to the
        # native station geometry, without any elapsed-month presentation.
        headings = page.locator("#mj-stage-strip .mj-stage-name")
        assert headings.count() == 10
        stage_boxes = headings.evaluate_all(
            "(nodes) => nodes.map(n => ({id: n.dataset.stageId, x: n.getBoundingClientRect().x, w: n.getBoundingClientRect().width}))")
        assert len(set(item["id"] for item in stage_boxes)) == 10
        assert [item["x"] for item in stage_boxes] == sorted(
            item["x"] for item in stage_boxes)
        assert all(item["w"] >= 38 for item in stage_boxes)
        assert "Stage 1:" in headings.first.get_attribute("aria-label")
        assert not any("Month" in (n.inner_text()) for n in headings.all())
        # Small viewports show ordinal headers, while the full source-backed
        # stage names remain in the selector, title and accessible labels.
        page.wait_for_function("""() => document.querySelector('#mj-stage-strip .mj-stage-name').textContent === '01'""")
        stage_select = page.locator("#mj-stage-picker")
        assert stage_select.locator("option").count() == 11
        assert "Authorization" in stage_select.locator('option[value="stage-4"]').inner_text()
        before_moments = page.evaluate("""() => [...window.__mjourneyResearchViewer.positions].map(([id, xy]) => [id, xy.x, xy.y])""")
        stage_select.select_option("stage-4")
        assert page.locator('.mj-stage-name[data-stage-id="stage-4"]').get_attribute("class").find("mj-stage-active") >= 0
        assert page.locator("#mj-stage-focus rect").evaluate("(e) => e.style.display !== 'none'")
        # A source projection's pre-render x bounds are not native SVG x
        # coordinates. The highlighted rectangle must contain exactly the
        # selected stage's actual rendered stations, not a later stage.
        stage_bounds = page.evaluate("""() => {
          const model = window.__mjourneyResearchViewer, id = 'stage-4';
          const xs = stageId => model.data.canonical.moments
            .filter(m => m.stageId === stageId).map(m => model.positions.get(m.id).x);
          const selected = xs(id), next = xs('stage-5');
          const rect = document.querySelector('#mj-stage-focus rect');
          const x = Number(rect.getAttribute('x'));
          const right = x + Number(rect.getAttribute('width'));
          return {x, right, min: Math.min(...selected), max: Math.max(...selected),
                  nextMin: Math.min(...next)};
        }""")
        assert stage_bounds["x"] <= stage_bounds["min"], stage_bounds
        assert stage_bounds["right"] >= stage_bounds["max"], stage_bounds
        assert stage_bounds["right"] < stage_bounds["nextMin"], stage_bounds
        page.wait_for_function("window.__mjourneyLabels.currentStageId() === 'stage-4'")
        page.wait_for_function("window.__mjourneyLabels.visibleIds().includes('eq31')")
        after_moments = page.evaluate("""() => [...window.__mjourneyResearchViewer.positions].map(([id, xy]) => [id, xy.x, xy.y])""")
        assert after_moments == before_moments, "stage attention cannot move a canonical moment"
        page.screenshot(path=str(OUT / "system-stage-950.png"), full_page=True)
        stage_select.select_option("")
        assert not page.locator("#mj-stage-focus rect").evaluate("(e) => e.style.display !== 'none'")
        assert page.locator("#mj-stage-strip .mj-stage-active").count() == 0
        # Optional focus edges must all exist in the canonical directed graph.
        focus_select = page.locator("#mj-focus-select")
        assert focus_select.locator("option").count() == 4
        assert page.locator("#mj-source-relationships path").count() == 0
        assert page.locator("#mj-source-junctions circle").count() == 0
        junctions = page.evaluate("window.__mjourneyScene.junctionRoles()")
        assert len(junctions) == 2, junctions
        assert {(j["momentId"], j["role"]) for j in junctions} == {
            ("eq31", "branch-origin"), ("eq37", "reconvergence")}
        assert {j["momentId"]: j["edgeIds"] for j in junctions} == {
            "eq31": ["edge44", "edge45"],
            "eq37": ["edge50", "edge52"]}
        assert page.evaluate("window.__mjourneyScene.subduableShortcutCount()") == 1
        frame = page.evaluate("""() => ({
            width: document.documentElement.scrollWidth,
            height: document.documentElement.scrollHeight,
            viewportHeight: window.innerHeight,
            stageHeight: document.querySelector("#stage").getBoundingClientRect().height
        })""")
        assert frame["width"] <= 951
        assert frame["height"] <= frame["viewportHeight"] + 1, frame
        assert frame["stageHeight"] >= 200
        # Key labels are readable HTML callouts bound to the exact same source
        # station coordinates. Visible label rectangles must not overlap.
        page.wait_for_function("window.__mjourneyLabels && window.__mjourneyLabels.visibleIds().length >= 5")
        labels = page.locator("#mj-readable-labels .mj-readable-label")
        key_count = labels.count()
        assert 5 <= key_count <= 14, key_count
        assert page.locator("#mj-label-controls button[aria-pressed='true']").inner_text() == "Key labels"
        boxes = labels.evaluate_all("""items => items.map(el => {
          const r = el.getBoundingClientRect(), s = getComputedStyle(el);
          return {id: el.dataset.momentId, l:r.left, t:r.top, r:r.right, b:r.bottom,
                  size: parseFloat(s.fontSize)};
        })""")
        assert all(b["size"] >= 11 for b in boxes)
        for i, one in enumerate(boxes):
            for two in boxes[i + 1:]:
                assert not (one["l"] < two["r"] + 3 and one["r"] + 3 > two["l"]
                            and one["t"] < two["b"] + 3 and one["b"] + 3 > two["t"]), (one, two)
        page.screenshot(path=str(OUT / "system-key-labels-950.png"), full_page=True)
        page.get_by_role("button", name="More labels").click()
        page.wait_for_function("window.__mjourneyLabels.currentDensity() === 'more'")
        page.wait_for_function("document.querySelector('#mj-readable-labels').dataset.visibleCount !== null")
        assert labels.count() >= key_count
        page.screenshot(path=str(OUT / "system-more-labels-950.png"), full_page=True)
        page.get_by_role("button", name="Key labels").click()
        page.wait_for_function("window.__mjourneyLabels.currentDensity() === 'key'")
        page.screenshot(path=str(OUT / "system-overview-950.png"), full_page=True)
        focus_select.select_option("ae")
        assert page.locator("#mj-source-relationships path").count() == 4
        assert page.locator("#mj-source-junctions circle").count() == 2
        assert page.locator('#mj-source-junctions [data-moment-id="eq31"]').get_attribute("data-junction-role") == "branch-origin"
        assert page.locator('#mj-source-junctions [data-moment-id="eq37"]').get_attribute("data-junction-role") == "reconvergence"
        assert page.locator("#lines path.mj-subdued-category-shortcut").count() == 1
        assert set(page.locator("#mj-source-relationships path").evaluate_all(
            "(xs) => xs.map(x => x.dataset.sourceEdgeId)")) == {
                "edge44", "edge48", "edge49", "edge50"}
        focus_select.select_option("direct")
        assert page.locator("#mj-source-relationships path").count() == 3
        focus_select.select_option("all")
        page.wait_for_function("window.__mjourneyLabels.visibleIds().includes('eq31')")
        assert page.locator('#mj-readable-labels [data-moment-id="eq31"]').count() == 1
        highlighted_ids = page.locator("#mj-source-relationships path").evaluate_all(
            "(xs) => xs.map(x => x.dataset.sourceEdgeId)")
        assert len(highlighted_ids) == len(set(highlighted_ids)) == 7
        assert "edge45" in highlighted_ids and "edge52" in highlighted_ids
        # Constrained routing is computed on *native* station coordinates.
        # Every step is octilinear and endpoints equal the original moment;
        # no additional station or original research edge has been introduced.
        corridor = page.evaluate("""() => ({
          paths: window.__mjourneyScene.corridorRoutes(),
          stats: window.__mjourneyScene.corridorStats(),
          intact: window.__mjourneyScene.corridorRoutes().every(route => {
            const pos = window.__mjourneyResearchViewer.positions;
            const same = (a, b) => Math.hypot(a.x-b.x,a.y-b.y) < .00001;
            return window.MJourneyCorridorRouter.isOctilinear(route.points)
              && same(route.points[0], pos.get(route.fromId))
              && same(route.points.at(-1), pos.get(route.toId));
          })
        })""")
        assert corridor["intact"], corridor
        assert len(corridor["paths"]) == 7
        assert {e["id"] for e in corridor["paths"]} == set(highlighted_ids)
        assert corridor["stats"]["routeCount"] == 7
        assert corridor["stats"]["maxClearanceViolationCount"] == 0, corridor
        assert corridor["stats"]["totalBends"] < 30, corridor
        assert all(e["minStationClearance"] is None or
                   e["minStationClearance"] >= 13 for e in corridor["paths"]), corridor
        # Before corridor routing, the eq35→eq37 direct vertical overlay
        # crossed an unrelated station eq34. The chosen corridor must avoid it.
        obstacle = page.evaluate("""() => {
          const pos = window.__mjourneyResearchViewer.positions;
          const api = window.MJourneyCorridorRouter;
          const direct = api.distancePointSegment(
              pos.get("eq34"), pos.get("eq35"), pos.get("eq37"));
          const planned = window.__mjourneyScene.corridorRoutes()
              .find(r => r.id === "edge52");
          return {old: direct, new: planned.minStationClearance,
                  bends: planned.bends, path: planned.path};
        }""")
        assert obstacle["old"] < 13, obstacle
        assert obstacle["new"] >= 13, obstacle
        report = {
            "schema": "mjourney-corridor-geometry-diagnostic/v1",
            "sourceFixture": "equipment-sanitized-v1",
            "canonicalStationCount": 67,
            "canonicalAuthoredEdgeCount": 87,
            "selectedSourceEdgeIds": sorted(e["id"] for e in corridor["paths"]),
            "totals": corridor["stats"],
            "originalEdge52NonincidentStationClearance": obstacle["old"],
            "routedEdge52MinStationClearance": obstacle["new"],
            "sourceRoutes": corridor["paths"],
            "sourceOrStageGeometryChanged": False,
            "categoryGuideTracksAltered": False,
            "artisticAcceptanceClaimed": False,
        }
        (OUT / "system-corridor-metrics.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("CORRIDOR ROUTING METRICS",
              json.dumps({"totals": report["totals"],
                          "edge52": obstacle,
                          "routes": [{"id": e["id"], "bends": e["bends"],
                                      "guideCrossings": e["guideCrossings"],
                                      "clearance": e["minStationClearance"]}
                                     for e in corridor["paths"]]}))
        selected_route_paths = {
            e["id"]: e["path"] for e in corridor["paths"]
        }
        assert page.locator("#mj-source-relationships path").evaluate_all(
            "(els) => els.every(e => e.dataset.corridorScore && e.dataset.corridorBends)")
        # Bigger rings require verified source branching and convergence.
        # Crossings and intermediate stations remain ordinary markers.
        ring_ids = page.locator("#mj-source-junctions circle").evaluate_all(
            "(xs) => xs.map(x => x.dataset.momentId)")
        assert sorted(ring_ids) == ["eq31", "eq37"]
        assert page.locator('#mj-source-junctions [data-moment-id="eq32"]').count() == 0
        page.screenshot(path=str(OUT / "system-corridors-950.png"), full_page=True)
        page.screenshot(path=str(OUT / "system-junctions-950.png"), full_page=True)
        page.screenshot(path=str(OUT / "system-focus-950.png"), full_page=True)

        description = page.locator("#map-description").inner_text()
        assert "67 unique moments" in description
        assert "not directed research connections" in description
        assert "Trains move" not in description
        assert page.evaluate("window.__present.setTrip('eq31', 'eq37')") is None
        assert page.locator("#trip").count() == 0, "no passenger trip widget"

        picker.select_option("eq31")
        assert page.locator("#mj-inspector-heading").inner_text() == "Funding authorized"
        detail = page.locator(".mj-inspector-body").inner_text()
        assert "edge44" in detail and "edge45" in detail
        assert "Stage: Authorization" in detail
        assert "Source graph role: branch origin" in detail
        assert "not a transit interchange" in detail
        assert not page.locator("#mj-inspector").evaluate("(el) => el.hidden")
        assert page.locator("#mj-research-workspace").count() == 1
        # At carousel width the details occupy an actual bottom strip, not
        # map area: source station labels/lines remain unoccluded.
        dock = page.evaluate("""() => {
          const stage = document.querySelector('#stage').getBoundingClientRect();
          const panel = document.querySelector('#mj-inspector').getBoundingClientRect();
          return {stageBottom: stage.bottom, stageHeight: stage.height,
                  panelTop: panel.top, panelRight: panel.right,
                  documentHeight: document.documentElement.scrollHeight,
                  viewportHeight: window.innerHeight,
                  panelPosition: getComputedStyle(document.querySelector('#mj-inspector')).position};
        }""")
        assert dock["panelPosition"] == "relative", dock
        assert dock["stageBottom"] <= dock["panelTop"] + 1, dock
        assert dock["stageHeight"] >= 175, dock
        assert dock["panelRight"] <= 951, dock
        assert dock["documentHeight"] <= dock["viewportHeight"] + 1, dock
        page.screenshot(path=str(OUT / "system-research-950.png"), full_page=True)

        # Research inspector can be dismissed with the keyboard.
        page.keyboard.press("Escape")
        assert page.locator("#mj-inspector").evaluate("(el) => el.hidden")
        assert page.evaluate("document.activeElement.id") == "mj-moment-picker"
        picker.select_option("eq01")
        assert "edge01" in page.locator(".mj-inspector-body").inner_text()

        # Pointer selection uses the same canonical station IDs as the dropdown.
        coords = page.evaluate("""() => {
            const svg = document.querySelector("#stage svg");
            const el = svg.querySelector('#stations [data-station-id="eq31"]');
            const point = svg.createSVGPoint();
            point.x = Number(el.getAttribute("cx"));
            point.y = Number(el.getAttribute("cy"));
            const screen = point.matrixTransform(svg.getScreenCTM());
            return {x: screen.x, y: screen.y};
        }""")
        assert coords and coords["x"] >= 0 and coords["y"] >= 0
        assert coords["x"] <= 950 and coords["y"] <= 520
        page.mouse.click(coords["x"], coords["y"])
        assert page.locator("#mj-inspector-heading").inner_text() == "Funding authorized"

        # Same generated research source, larger viewport and native Fit.
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_function("document.querySelector('#mj-inspector').getBoundingClientRect().left > document.querySelector('#stage').getBoundingClientRect().left")
        side = page.evaluate("""() => {
          const stage = document.querySelector('#stage').getBoundingClientRect();
          const panel = document.querySelector('#mj-inspector').getBoundingClientRect();
          return {stageRight: stage.right, stageWidth: stage.width,
                  panelLeft: panel.left, panelWidth: panel.width,
                  panelBottom: panel.bottom,
                  viewportHeight: innerHeight,
                  documentHeight: document.documentElement.scrollHeight};
        }""")
        assert side["stageRight"] <= side["panelLeft"] + 1, side
        assert 280 <= side["panelWidth"] <= 360, side
        assert side["stageWidth"] >= 900, side
        assert side["panelBottom"] <= side["viewportHeight"] + 1, side
        assert side["documentHeight"] <= side["viewportHeight"] + 1, side
        assert page.locator("#mj-stage-strip .mj-stage-name").count() == 10
        assert page.locator("#mj-source-relationships path").count() == 7
        page.wait_for_function("""() => document.querySelector('#mj-stage-strip .mj-stage-name').textContent === 'Business need'""")
        stage_select.select_option("stage-5")
        assert page.locator('.mj-stage-name[data-stage-id="stage-5"]').inner_text() == "Vendor selection"
        assert page.locator("#mj-stage-focus rect").evaluate("(e) => e.style.display !== 'none'")
        page.screenshot(path=str(OUT / "system-stage-1440.png"), full_page=True)
        page.evaluate("window.__mjourneyScene.redrawStages()")
        y_gap = page.evaluate("""() => {
          const model = window.__mjourneyResearchViewer;
          const svg = model.svg, ctm = svg.getScreenCTM();
          const ys = [...model.positions.values()].map(p => {
            const pt = svg.createSVGPoint();
            pt.x = p.x; pt.y = p.y;
            return pt.matrixTransform(ctm).y;
          });
          return Math.min(...ys) -
            document.querySelector("#mj-stage-strip").getBoundingClientRect().top;
        }""")
        assert 35 <= y_gap <= 110, y_gap
        page.screenshot(path=str(OUT / "system-corridors-1440.png"), full_page=True)
        page.screenshot(path=str(OUT / "system-junctions-1440.png"), full_page=True)
        page.screenshot(path=str(OUT / "system-focus-1440.png"), full_page=True)
        page.screenshot(path=str(OUT / "system-research-1440.png"), full_page=True)
        focus_select.select_option("")
        assert page.locator("#mj-source-junctions circle").count() == 0
        assert page.locator("#lines path.mj-subdued-category-shortcut").count() == 0
        assert page.locator("#mj-source-relationships path").count() == 0
        assert {e["id"]: e["path"] for e in page.evaluate(
            "window.__mjourneyScene.corridorRoutes()")} == selected_route_paths
        assert not issues, "Browser page errors: " + "; ".join(issues)
        browser.close()
    print("Chromium M-Journey inspector and source-route isolation smoke PASS")


if __name__ == "__main__":
    main()
