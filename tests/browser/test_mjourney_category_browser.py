"""Chromium comparison of source-demand category guides against legacy System V3.

The fork's original SVG engine still renders both. This checks *presentation*
coordinate changes with immutable research IDs and zero guide crossings, not
that source graph relationships magically become transit interchanges.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"


def main() -> None:
    from playwright.sync_api import sync_playwright  # optional in normal pytest
    legacy = json.loads((OUT / "system-browser.audit.json").read_text())
    demand = json.loads((OUT / "system-stage-demand.audit.json").read_text())
    original_nodes = legacy["projection"]["stationCoords"]
    new_nodes = demand["projection"]["stationCoords"]
    legacy_contract = json.loads((OUT / "system-browser.research.json").read_text())
    demand_contract = json.loads((OUT / "system-stage-demand.research.json").read_text())
    assert legacy_contract["canonicalSemanticSha256"] == demand_contract[
        "canonicalSemanticSha256"]
    assert legacy_contract["canonical"] == demand_contract["canonical"]
    assert legacy_contract["presentation"]["categoryGuides"] == demand_contract[
        "presentation"]["categoryGuides"]
    assert len(original_nodes) == len(new_nodes) == 67
    assert set(original_nodes) == set(new_nodes)
    assert all(original_nodes[k][0] == new_nodes[k][0] for k in original_nodes)
    assert sum(original_nodes[k][1] != new_nodes[k][1]
               for k in original_nodes) >= 10
    assert demand["projection"]["categoryCorridorMode"] == "stage-demand"
    metrics = demand["projection"]["categoryCorridorMetrics"]
    assert metrics["guideCount"] == 60
    assert metrics["crossCategoryGuideIntersections"] == 0
    assert not metrics["nonincidentStationClearanceViolationsUnder30"]
    assert metrics["minimumNonincidentStationClearance"] >= 30
    assert all(abs(r["overallGapSpan"] - 624) < .001 for r in
               demand["projection"]["categoryCorridorStageDemand"])

    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Capture the legacy geometry with exactly the same visitor choices:
        # both focus sequences, canonical Funding authorized inspector, Key
        # labels, and the same two physical viewports.
        baseline_page = browser.new_page(viewport={"width": 950, "height": 520})
        baseline_page.on("pageerror", lambda e: errors.append("baseline: " + str(e)))
        baseline_page.goto((OUT / "system-browser.html").as_uri(), wait_until="load")
        baseline_picker = baseline_page.locator("#mj-moment-picker")
        baseline_picker.wait_for(timeout=15000)
        baseline_page.locator("#mj-focus-select").select_option("all")
        baseline_picker.select_option("eq31")
        assert baseline_page.locator("#mj-source-relationships path").count() == 7
        baseline_page.screenshot(
            path=str(OUT / "system-demand-baseline-selected-950.png"),
            full_page=True)
        baseline_page.set_viewport_size({"width": 1440, "height": 900})
        baseline_page.screenshot(
            path=str(OUT / "system-demand-baseline-selected-1440.png"),
            full_page=True)
        baseline_page.close()
        page = browser.new_page(viewport={"width": 950, "height": 520})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto((OUT / "system-stage-demand.html").as_uri(), wait_until="load")
        picker = page.locator("#mj-moment-picker")
        picker.wait_for(timeout=15000)
        page.wait_for_function("!!window.__mjourneyScene && !!window.__mjourneyLabels")
        assert picker.locator("option").count() == 68
        assert page.locator("#line-count").inner_text() == "7 of 7"
        assert page.locator("#mj-stage-strip .mj-stage-name").count() == 10
        assert page.locator("#mj-source-relationships path").count() == 0
        assert page.locator("#mj-source-junctions circle").count() == 0
        assert page.locator("#mj-readable-labels .mj-readable-label").count() >= 5

        frame = page.evaluate("""() => {
          const r = document.querySelector("#stage").getBoundingClientRect();
          return {docW: document.documentElement.scrollWidth,
                  docH: document.documentElement.scrollHeight,
                  viewportH: innerHeight,
                  stageH: r.height};
        }""")
        assert frame["docW"] <= 951, frame
        assert frame["docH"] <= frame["viewportH"] + 1, frame
        assert frame["stageH"] >= 200, frame
        page.screenshot(path=str(OUT / "system-demand-overview-950.png"), full_page=True)

        select = page.locator("#mj-focus-select")
        select.select_option("all")
        picker.select_option("eq31")
        assert page.locator("#mj-source-relationships path").count() == 7
        assert page.locator("#mj-source-junctions circle").count() == 2
        assert page.locator("#mj-inspector-heading").inner_text() == "Funding authorized"
        overlays = page.evaluate("""() => {
          const routes = window.__mjourneyScene.corridorRoutes();
          const pos = window.__mjourneyResearchViewer.positions;
          const oct = window.MJourneyCorridorRouter.isOctilinear;
          return {n:routes.length, minClearance:
            Math.min(...routes.filter(r=>r.minStationClearance != null)
                              .map(r=>r.minStationClearance)),
            bends: routes.reduce((a,r)=>a+r.bends,0),
            crossings: routes.reduce((a,r)=>a+r.guideCrossings,0),
            authentic: routes.every(r=>r.id && oct(r.points) &&
              Math.hypot(r.points[0].x-pos.get(r.fromId).x,
                         r.points[0].y-pos.get(r.fromId).y) < .001 &&
              Math.hypot(r.points.at(-1).x-pos.get(r.toId).x,
                         r.points.at(-1).y-pos.get(r.toId).y) < .001)
          };
        }""")
        assert overlays["n"] == 7 and overlays["authentic"], overlays
        assert overlays["minClearance"] >= 13, overlays
        page.screenshot(path=str(OUT / "system-demand-focus-950.png"), full_page=True)

        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_function("""() => document.querySelector('#mj-stage-strip .mj-stage-name').textContent === 'Business need'""")
        page.screenshot(path=str(OUT / "system-demand-focus-1440.png"), full_page=True)

        # Canonical station membership/position is unchanged by focus controls.
        rendered = page.evaluate("""() => ({
          nodes: window.__mjourneyResearchViewer.positions.size,
          lines: window.__mjourneyResearchViewer.data.canonical.categories.length,
          relations: window.__mjourneyResearchViewer.relationships.length
        })""")
        assert rendered == {"nodes": 67, "lines": 7, "relations": 87}
        assert not errors, errors
        browser.close()

    report = {
        "mode": "stage-demand-category-corridors",
        "originalSource": "equipment-sanitized-v1",
        "sourceMomentCount": 67,
        "sourceDirectedRelationshipCount": 87,
        "sourceGuideCount": metrics["guideCount"],
        "xCoordinatesChanged": 0,
        "yCoordinatesRearranged": sum(original_nodes[k][1] != new_nodes[k][1]
                                      for k in original_nodes),
        "guideMetrics": metrics,
        "selectedRelationshipMetrics": overlays,
        "viewport": frame,
        "nativeRendererReplaced": False,
        "verifiedCustomerTransferCount": 0,
        "visualDesignApproved": False,
    }
    (OUT / "system-demand-metrics.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("STAGE DEMAND CORRIDOR METRICS", json.dumps(report))
    print("Chromium category lane comparison PASS")


if __name__ == "__main__":
    main()
