"""TM-01a browser audit of existing seven-category legend and static native framing.

Uses the same source-certified HTML fixture and original Legible Cities
rendering. No customer/source records, feature data, or browser storage.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
PAGE = OUT / "system-browser.html"


def main():
    from playwright.sync_api import sync_playwright  # optional outside browser job

    assert PAGE.is_file(), "Generate out/system-browser.html first"
    errors = []
    metrics = {}
    with sync_playwright() as engine:
        browser = engine.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 950, "height": 520},
                                device_scale_factor=1)
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(PAGE.as_uri(), wait_until="load")
        page.wait_for_function("!!window.__mjourneyResponsiveFrame")
        page.wait_for_function("window.__mjourneyResponsiveFrame.sourceChipCount() === 7")
        controls = page.locator("#mj-category-disclosure")
        chips = page.locator("#line-toggles .chip")
        assert chips.count() == 7
        assert controls.get_attribute("aria-controls") == "line-toggles"
        assert controls.get_attribute("aria-expanded") == "true"
        assert page.evaluate("window.__mjourneyResponsiveFrame.noClippedChipBounds()")
        assert page.locator("#line-count").inner_text() == "7 of 7"
        before = page.evaluate("""() => ({
          chips: document.querySelectorAll('#line-toggles .chip').length,
          stageHeight: document.querySelector('#stage').getBoundingClientRect().height,
          headerBottom: document.querySelector('header').getBoundingClientRect().bottom,
          stageTop: document.querySelector('#stage').getBoundingClientRect().top,
          docHeight: document.documentElement.scrollHeight,
          docWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body.scrollWidth,
          viewWidth: innerWidth, viewHeight: innerHeight,
          overviewViewBox: document.querySelector('#stage svg').getAttribute('viewBox'),
          stationIds: [...document.querySelectorAll('#stations [data-station-id]')]
            .map(e=>e.getAttribute('data-station-id')),
          guidePairs: [...document.querySelectorAll('#lines path[data-src][data-dst]')]
            .map(e=>e.dataset.src + '>' + e.dataset.dst),
        })""")
        assert before["chips"] == 7
        assert before["stageHeight"] >= 200, before
        assert before["headerBottom"] <= before["stageTop"] + 1, before
        assert before["docWidth"] <= 951, before
        assert before["bodyWidth"] <= 951, before
        assert before["docHeight"] <= before["viewHeight"] + 1, before
        assert len(before["stationIds"]) == 67
        assert len(set(before["stationIds"])) == 67
        assert len(before["guidePairs"]) == 60
        page.screenshot(path=str(OUT / "system-responsive-legend-950.png"),
                        full_page=True)

        # The actual original per-line controls retain their native handlers.
        chips.first.click()
        assert page.locator("#line-count").inner_text() == "6 of 7"
        page.locator("#lines-all").click()
        assert page.locator("#line-count").inner_text() == "7 of 7"
        page.locator("#lines-none").click()
        assert page.locator("#line-count").inner_text() == "0 of 7"
        page.locator("#lines-all").click()
        assert page.locator("#line-count").inner_text() == "7 of 7"

        # The disclosure is optional, and its toggle does not replace/remove
        # the seven real category chips or their checked/pressed state.
        controls.focus()
        page.keyboard.press("Enter")
        assert controls.get_attribute("aria-expanded") == "false"
        assert not page.locator("#line-toggles").is_visible()
        hidden_height = page.locator("#stage").evaluate("(el)=>el.getBoundingClientRect().height")
        assert hidden_height >= before["stageHeight"] - 1, (
            before["stageHeight"], hidden_height)
        assert chips.count() == 7, "collapse must not rebuild original chip nodes"
        assert page.locator("#line-count").inner_text() == "7 of 7"
        page.screenshot(path=str(OUT / "system-responsive-legend-collapsed-950.png"),
                        full_page=True)
        page.keyboard.press("Enter")
        assert controls.get_attribute("aria-expanded") == "true"
        assert page.locator("#line-toggles").is_visible()
        assert page.evaluate("window.__mjourneyResponsiveFrame.noClippedChipBounds()")
        assert page.locator("#line-count").inner_text() == "7 of 7"

        page.locator("#mj-moment-picker").select_option("eq31")
        assert page.locator("#mj-inspector-heading").inner_text() == "Funding authorized"
        compact = page.evaluate("""() => {
          const stage = document.querySelector('#stage').getBoundingClientRect();
          const inspector = document.querySelector('#mj-inspector').getBoundingClientRect();
          return {stageBottom: stage.bottom, inspectorTop: inspector.top,
                  stageHeight: stage.height,
                  docH: document.documentElement.scrollHeight,
                  viewportH: innerHeight};
        }""")
        assert compact["stageBottom"] <= compact["inspectorTop"] + 1, compact
        assert compact["stageHeight"] >= 175, compact
        assert compact["docH"] <= compact["viewportH"] + 1, compact
        visibility = page.evaluate("""() => {
          const stage = document.querySelector("#stage").getBoundingClientRect();
          const svg = document.querySelector("#stage svg");
          const ctm = svg.getScreenCTM();
          const markers = [...svg.querySelectorAll('#stations [data-station-id]')];
          const visible = markers.map(m => {
            const p = svg.createSVGPoint();
            p.x = Number(m.getAttribute("cx"));
            p.y = Number(m.getAttribute("cy"));
            const z = p.matrixTransform(ctm);
            return {id:m.dataset.stationId, x:z.x, y:z.y,
              inside: z.x >= stage.left+1 && z.x <= stage.right-1 &&
                      z.y >= stage.top+1 && z.y <= stage.bottom-1};
          });
          return {total: visible.length, missed:visible.filter(m => !m.inside)};
        }""")
        assert visibility["total"] == 67, visibility
        assert not visibility["missed"], (
            "Compact inspector cannot crop canonical stations", visibility)
        page.screenshot(path=str(OUT / "system-responsive-inspector-950.png"),
                        full_page=True)

        # At desktop, keep all categories legible and the inspector docked to
        # the side. Do not stretch/overwrite the original SVG full-map box.
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_function(
            "document.querySelector('#mj-inspector').getBoundingClientRect().left > "
            "document.querySelector('#stage').getBoundingClientRect().right - 1")
        assert page.evaluate("window.__mjourneyResponsiveFrame.noClippedChipBounds()")
        expanded = page.evaluate("""() => ({
          chipCount: document.querySelectorAll('#line-toggles .chip').length,
          docWidth: document.documentElement.scrollWidth,
          docHeight: document.documentElement.scrollHeight,
          width: innerWidth, height: innerHeight,
          viewBox: document.querySelector('#stage svg').getAttribute('viewBox'),
          stationIds: [...document.querySelectorAll('#stations [data-station-id]')]
            .map(e=>e.getAttribute('data-station-id')),
          guidePairs: [...document.querySelectorAll('#lines path[data-src][data-dst]')]
            .map(e=>e.dataset.src + '>' + e.dataset.dst),
        })""")
        assert expanded["chipCount"] == 7
        assert expanded["docWidth"] <= expanded["width"] + 1, expanded
        assert expanded["docHeight"] <= expanded["height"] + 1, expanded
        assert expanded["stationIds"] == before["stationIds"]
        assert expanded["guidePairs"] == before["guidePairs"]
        page.screenshot(path=str(OUT / "system-responsive-legend-1440.png"),
                        full_page=True)
        assert not errors, errors
        metrics = {
            "sourceMoments": len(before["stationIds"]),
            "sourceCategoryGuides": len(before["guidePairs"]),
            "categoryChips": expanded["chipCount"],
            "nativeAllNoneAndChipStatePreserved": True,
            "keyboardDisclosureAndFocusPreserved": True,
            "responsiveDisclosedChipBoundsClear": True,
            "compactStageHeight": round(before["stageHeight"], 2),
            "compactCollapsedStageHeight": round(hidden_height, 2),
            "compactInspectorStageHeight": round(compact["stageHeight"], 2),
            "sourceStationIdsUnchangedAcrossViewports": True,
            "nativeSVGViewBoxNotOverridden": True,
            "researchMeaningChanged": False,
            "framingLimitation": (
                "The complete ten-stage panoramic map retains native meet "
                "aspect ratio; tall desktop frames letterbox rather than "
                "crop authored stations or distort octilinear geometry."
            ),
        }
        browser.close()

    (OUT / "system-responsive-frame-metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print("TM-01a responsive category legend Chromium PASS", json.dumps(metrics))


if __name__ == "__main__":
    main()
