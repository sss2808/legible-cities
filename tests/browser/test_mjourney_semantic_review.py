"""Chromium acceptance for TM-01b research-only semantic review lens.

Run after:
  python bin/mjourney-preview --system-v3 --stage-demand-corridors --html \\
    --focus-path ae=edge44,edge48,edge49,edge50 \\
    --focus-path direct=edge45,edge51,edge52 \\
    --output out/system-browser.svg
The fork's original category guides, renderer and research contract stay intact.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
VIEWER = OUT / "system-browser.html"


def main():
    from playwright.sync_api import sync_playwright

    assert VIEWER.is_file(), "Generate out/system-browser.html first"
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    summary = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 950, "height": 520},
                                device_scale_factor=1)
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(VIEWER.as_uri(), wait_until="load")
        page.wait_for_function("!!window.__mjourneySemanticReview")
        counts = page.evaluate("window.__mjourneySemanticReview.counts()")
        assert counts == {
            "handoffs": 3, "crossLayerHandoffs": 2,
            "returns": 1, "stations": 67, "directedRelations": 87,
        }, counts
        assert page.locator("#line-toggles .chip").count() == 7
        assert page.locator("#stations [data-station-id]").count() == 67
        assert page.locator("#lines path[data-src][data-dst]").count() == 60
        assert page.locator("#mj-semantic-review-edges *").count() == 0
        assert page.locator("#mj-focus-select").input_value() == ""
        page.screenshot(path=str(OUT / "semantic-review-baseline-950.png"),
                        full_page=True)

        # Coexist with the pre-existing source-backed branch comparison.
        existing = page.locator("#mj-focus-select")
        existing.select_option("all")
        assert page.locator("#mj-source-relationships path").count() == 7
        assert page.locator("#mj-source-junctions circle").count() == 2
        page.screenshot(path=str(OUT / "semantic-review-branches-950.png"),
                        full_page=True)

        # Opt-in source-typed handoffs. They never become transport transfers,
        # and selecting them switches OFF the prior vendor-selection focus.
        review = existing
        review.select_option("review:handoffs")
        assert existing.input_value() == "review:handoffs"
        assert review.locator('option[value="review:handoffs"]').inner_text() == "Handoffs (review)"
        assert "not approved transit interchanges" in review.get_attribute("title")
        assert page.locator("#mj-source-relationships path").count() == 0
        assert page.locator("#mj-source-junctions circle").count() == 0
        paths = page.locator("#mj-semantic-review-edges path")
        assert paths.count() == 3
        audit = page.evaluate("""() => {
          const svg = document.querySelector('#stage svg');
          const markers = [...svg.querySelectorAll('#stations [data-station-id]')];
          const stations = new Map(markers.map(m => {
            let x = Number(m.getAttribute('cx')), y = Number(m.getAttribute('cy'));
            if (!Number.isFinite(x) || !Number.isFinite(y)) {
              const coords = (m.getAttribute('d') || '').match(
                /^M\\s*([-\\d.]+)[\\s,]+([-\\d.]+)/);
              if (coords) { x = Number(coords[1]); y = Number(coords[2]); }
            }
            return [m.getAttribute('data-station-id'), {x,y}];
          }));
          return [...document.querySelectorAll('#mj-semantic-review-edges path')]
            .map(p => {
              const numbers = (p.getAttribute('d') || '').match(
                /-?\\d+(?:\\.\\d+)?(?:e[-+]?\\d+)?/gi).map(Number);
              const start = stations.get(p.dataset.sourceFrom);
              const end = stations.get(p.dataset.sourceTo);
              return {id: p.dataset.sourceEdgeId,
                review: p.dataset.reviewStatus,
                crossLayer: p.dataset.crossLayer,
                fromId: p.dataset.sourceFrom, toId: p.dataset.sourceTo,
                startError: Math.hypot(numbers[0]-start.x, numbers[1]-start.y),
                endError: Math.hypot(numbers.at(-2)-end.x,
                  numbers.at(-1)-end.y)};
            });
        }""")
        assert [item["id"] for item in audit] == [
            "edge71", "edge78", "edge84"], audit
        assert [item["crossLayer"] for item in audit] == [
            "false", "true", "true"], audit
        assert all(item["review"] == "needs-research-review"
                   and item["startError"] < .06
                   and item["endError"] < .06 for item in audit), audit
        assert "not approved transit interchanges" in page.locator(
            "#mj-semantic-review-status").text_content()
        assert page.locator('#mj-semantic-review-edges [data-interchange]').count() == 0
        page.screenshot(path=str(OUT / "semantic-review-handoffs-950.png"),
                        full_page=True)

        # Lifecycle recurrence is represented by its REAL endpoints only.
        # Do not draw a giant fabricated rail across ten stage domains.
        review.select_option("review:returns")
        assert "not a transit route" in review.get_attribute("title")
        assert paths.count() == 0
        rings = page.locator("#mj-semantic-review-edges circle")
        assert rings.count() == 2
        source = rings.evaluate_all("""els => els.map(e => ({
          edge: e.dataset.sourceEdgeId, station: e.dataset.sourceMomentId,
          role: e.dataset.returnEndpoint
        }))""")
        assert source == [
            {"edge": "edge87", "station": "eq67", "role": "source"},
            {"edge": "edge87", "station": "eq01", "role": "target"},
        ], source
        assert "not a transit route" in page.locator(
            "#mj-semantic-review-status").text_content()
        page.locator("#mj-moment-picker").select_option("eq67")
        assert "edge87" in page.locator("#mj-inspector").inner_text()
        page.screenshot(path=str(OUT / "semantic-review-return-950.png"),
                        full_page=True)

        # A native focus choice restores ordinary relationship display.
        existing.select_option("ae")
        assert page.evaluate("window.__mjourneySemanticReview.state()") == ""
        assert rings.count() == 0
        assert page.locator("#mj-source-relationships path").count() == 4
        existing.select_option("")
        assert page.locator("#mj-source-relationships path").count() == 0

        page.set_viewport_size({"width": 1440, "height": 900})
        review.select_option("review:handoffs")
        page.screenshot(path=str(OUT / "semantic-review-handoffs-1440.png"),
                        full_page=True)
        frame = page.evaluate("""() => ({
          scrollWidth: document.documentElement.scrollWidth,
          scrollHeight: document.documentElement.scrollHeight,
          width: innerWidth, height: innerHeight,
          stations: document.querySelectorAll('#stations [data-station-id]').length,
          guides: document.querySelectorAll('#lines path[data-src][data-dst]').length,
          overlays: document.querySelectorAll('#mj-semantic-review-edges path').length,
          originalEdges: JSON.parse(document.querySelector(
            '#mjourney-research').textContent).canonical.relationships.length,
          canonicalTransfers: JSON.parse(document.querySelector(
            '#mjourney-research').textContent).presentation.approvedTransfers.length,
        })""")
        assert frame["scrollWidth"] <= frame["width"] + 1, frame
        assert frame["scrollHeight"] <= frame["height"] + 1, frame
        assert (frame["stations"], frame["guides"], frame["overlays"],
                frame["originalEdges"], frame["canonicalTransfers"]) == (
                    67, 60, 3, 87, 0), frame
        # Screenshot the same authored vendor alternatives beside the other
        # semantic modes, without falsely treating them as customer itineraries.
        existing.select_option("all")
        assert page.locator("#mj-source-relationships path").count() == 7
        assert page.locator("#mj-semantic-review-edges path").count() == 0
        page.screenshot(path=str(OUT / "semantic-review-branches-1440.png"),
                        full_page=True)
        assert not errors, errors
        summary = {
            "sourceCounts": counts, "handoffGeometry": audit,
            "returnEndpoints": source, "desktop": frame,
            "noInventedTransfer": True,
            "focusExclusivity": True,
            "originalCategoryAndResearchSourceUntouched": True,
            "visualApproval": "pending independent screenshot review",
        }
        browser.close()
    (OUT / "semantic-review-metrics.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("TM-01b semantic review Chromium PASS", json.dumps(summary))


if __name__ == "__main__":
    main()
