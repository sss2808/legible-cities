"""Chromium acceptance for source-preserving Moment labels clear of transit rails.

The source fixture and native SVG geometry are frozen. This test measures
browser-space line/label intersections independently of the placer scoring.
"""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
PAGE = OUT / "system-browser.html"

AUDIT_JS = r"""() => {
  const svg = document.querySelector('#stage svg');
  const labels = [...document.querySelectorAll(
    '#mj-readable-labels .mj-readable-label')];
  const tracks = [...svg.querySelectorAll(
    '#lines path[data-src][data-dst], #mj-source-relationships path,' +
    ' #mj-semantic-review-edges path')].filter(x => x.getClientRects().length);
  const collisions = [];
  const boxes = labels.map(x => x.getBoundingClientRect());
  for (let i = 0; i < labels.length; i++) {
    const box = boxes[i], intersected = new Set();
    for (const path of tracks) {
      const len = path.getTotalLength(), ctm = path.getScreenCTM();
      if (!(len > 0) || !ctm) continue;
      const n = Math.max(1, Math.ceil(
        len * Math.hypot(ctm.a, ctm.b) / 3));
      for (let p = 0; p <= n; p++) {
        const s = path.getPointAtLength(len * p / n)
          .matrixTransform(ctm);
        if (s.x >= box.left - 2 && s.x <= box.right + 2 &&
            s.y >= box.top - 2 && s.y <= box.bottom + 2) {
          intersected.add(path.getAttribute('data-source-edge-id') ||
            path.getAttribute('data-src') + '>' +
            path.getAttribute('data-dst'));
          break;
        }
      }
    }
    if (intersected.size) collisions.push({
      id: labels[i].dataset.momentId,
      pathIds: [...intersected],
    });
  }
  const labelOverlap = [];
  for (let i = 0; i < boxes.length; i++)
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      if (a.left < b.right + 3 && a.right + 3 > b.left &&
          a.top < b.bottom + 3 && a.bottom + 3 > b.top)
        labelOverlap.push([labels[i].dataset.momentId,
          labels[j].dataset.momentId]);
    }
  return {
    visible: labels.length,
    collided: collisions.length,
    conflicts: collisions,
    labelOverlaps: labelOverlap,
    ids: labels.map(x => x.dataset.momentId),
    scores: labels.map(x => x.getAttribute('data-rail-clearance-score')),
    guideCount: document.querySelectorAll(
      '#lines path[data-src][data-dst]').length,
    sourceEdgeCount: JSON.parse(document.querySelector(
      '#mjourney-research').textContent).canonical.relationships.length,
    sourceStationCount: document.querySelectorAll(
      '#stations [data-station-id]').length,
  };
}"""


def main():
    assert PAGE.is_file(), "Generate out/system-browser.html first"
    errors = []
    with sync_playwright() as engine:
        browser = engine.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900},
                                device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(PAGE.as_uri(), wait_until="load")
        page.wait_for_function("!!window.__mjourneyLabels")
        before = page.evaluate("""() => ({
          stationPositions:[...window.__mjourneyResearchViewer.positions]
            .map(([id,p])=>[id,p.x,p.y]),
          guidePaths:[...document.querySelectorAll(
            '#lines path[data-src][data-dst]')].map(p=>[p.dataset.src,
              p.dataset.dst,p.getAttribute('d')]),
          originalViewBox:document.querySelector('#stage svg')
            .getAttribute('viewBox'),
        })""")
        assert len(before["stationPositions"]) == 67
        assert len(before["guidePaths"]) == 60

        # Compare the same source-authored alternatives as original PR #20.
        page.locator("#mj-focus-select").select_option("all")
        page.wait_for_function("""() => document.querySelectorAll(
          '#mj-source-relationships path').length === 7""")
        page.wait_for_timeout(120)
        overview = page.evaluate(AUDIT_JS)
        assert overview["visible"] == 14, overview
        assert overview["guideCount"] == 60 and overview["sourceEdgeCount"] == 87
        assert overview["sourceStationCount"] == 67
        assert not overview["labelOverlaps"], overview
        assert all(s is not None for s in overview["scores"]), overview
        assert overview["collided"] <= 3, overview
        # Both main authored junction labels should be readable without a
        # colored category guide or directed edge crossing the label text.
        assert not {"eq31", "eq37"}.intersection(
            c["id"] for c in overview["conflicts"]), overview
        page.screenshot(path=str(OUT / "rail-labels-key-1440.png"),
                        full_page=True)

        # Other modes still use the same native renderer and source IDs.
        page.locator("#mj-label-controls [data-label-density='more']").click()
        page.wait_for_function("""() => window.__mjourneyLabels
          .currentDensity() === 'more'""")
        page.wait_for_timeout(120)
        more = page.evaluate(AUDIT_JS)
        assert more["visible"] >= overview["visible"], more
        assert not more["labelOverlaps"], more
        page.screenshot(path=str(OUT / "rail-labels-more-1440.png"),
                        full_page=True)

        page.locator("#mj-focus-select").select_option("review:handoffs")
        page.wait_for_timeout(120)
        handoffs = page.evaluate(AUDIT_JS)
        assert not handoffs["labelOverlaps"], handoffs
        assert page.locator("#mj-semantic-review-edges path").count() == 3

        # Desktop stage exploration must recompute in displayed coordinates.
        page.locator("#mj-label-controls [data-label-density='key']").click()
        page.locator("#mj-focus-select").select_option("all")
        page.locator("#mj-stage-explore-toggle").click()
        page.locator("#mj-stage-picker").select_option("stage-4")
        page.wait_for_timeout(180)
        zoom = page.evaluate(AUDIT_JS)
        assert zoom["guideCount"] == 60 and zoom["sourceEdgeCount"] == 87
        assert not zoom["labelOverlaps"], zoom
        assert all(s is not None for s in zoom["scores"]), zoom
        page.screenshot(path=str(OUT / "rail-labels-explore-1440.png"),
                        full_page=True)

        page.locator("#mj-stage-explore-toggle").click()
        page.set_viewport_size({"width": 950, "height": 520})
        page.wait_for_timeout(180)
        compact = page.evaluate(AUDIT_JS)
        assert 5 <= compact["visible"] <= 14
        assert not compact["labelOverlaps"], compact
        assert compact["guideCount"] == 60
        assert page.locator("#mj-stage-explore-toggle").is_hidden()
        assert not page.evaluate("window.__mjourneyStageExplore.state().active")
        page.screenshot(path=str(OUT / "rail-labels-compact-950.png"),
                        full_page=True)

        after = page.evaluate("""() => ({
          stationPositions:[...window.__mjourneyResearchViewer.positions]
            .map(([id,p])=>[id,p.x,p.y]),
          guidePaths:[...document.querySelectorAll(
            '#lines path[data-src][data-dst]')].map(p=>[p.dataset.src,
              p.dataset.dst,p.getAttribute('d')]),
          viewBox:document.querySelector('#stage svg')
            .getAttribute('viewBox'),
        })""")
        assert after["stationPositions"] == before["stationPositions"]
        assert after["guidePaths"] == before["guidePaths"]
        assert after["viewBox"] == before["originalViewBox"]
        assert not errors, errors
        report = {
          "baselineSameSourcePriorToChange": {
            "scenario": "1440x900 key labels; Compare alternatives",
            "visibleLabels": 14,
            "intersectedLabels": 7,
            "method": "independent local baseline Chromium visual audit",
        },
          "after": overview, "more": more,
          "handoffs": handoffs, "explore": zoom, "compact": compact,
          "canonicalMoments": 67, "authoredRelations": 87,
          "categoryGuides": 60, "nativeViewBoxPreserved": True,
          "visualApproval": "pending independent cartographic review",
        }
        OUT.mkdir(exist_ok=True)
        (OUT / "rail-labels-metrics.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("TM-01d native rail-aware labels Chromium PASS",
              json.dumps({"before": 7, "after": overview["collided"],
                          "keyLabels": overview["visible"],
                          "afterExplore": zoom["visible"]}))
        browser.close()


if __name__ == "__main__":
    main()
