"""TM-01c true-browser proof for opt-in CSS exploration over native SVG.

The default Full/fit camera is never rewritten. The 10 authored stages merely
recenter a CSS-uniform zoom on the original rendered 67-station source map.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
VIEWER = OUT / "system-browser.html"


def main():
    from playwright.sync_api import sync_playwright

    assert VIEWER.is_file(), "Render out/system-browser.html first"
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900},
                                device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(VIEWER.as_uri(), wait_until="load")
        page.wait_for_function("!!window.__mjourneyStageExplore")
        original = page.evaluate("""() => ({
          camera: document.querySelector('#stage svg').getAttribute('viewBox'),
          stationIds: [...document.querySelectorAll(
            '#stations [data-station-id]')].map(el=>el.dataset.stationId),
          guides: [...document.querySelectorAll(
            '#lines path[data-src][data-dst]')].map(el=>
              el.dataset.src + '>' + el.dataset.dst),
          edges: JSON.parse(document.querySelector('#mjourney-research')
            .textContent).canonical.relationships.length,
          stageNames: document.querySelectorAll(
            '#mj-stage-strip .mj-stage-name').length,
          docW: document.documentElement.scrollWidth,
          docH: document.documentElement.scrollHeight,
        })""")
        assert len(original["stationIds"]) == len(set(original["stationIds"])) == 67
        assert len(original["guides"]) == 60
        assert original["edges"] == 87 and original["stageNames"] == 10
        assert original["docW"] <= 1441 and original["docH"] <= 901
        assert not page.evaluate("window.__mjourneyStageExplore.state().active")
        assert page.locator("#mj-stage-explore-toggle").is_visible()
        assert page.locator("#mj-stage-explore-toggle").get_attribute(
            "aria-pressed") == "false"
        page.screenshot(path=str(OUT / "stage-explore-fit-1440.png"),
                        full_page=True)

        # The original source-backed branch/convergence overlays are retained.
        page.locator("#mj-focus-select").select_option("all")
        page.locator("#mj-moment-picker").select_option("eq31")
        assert page.locator("#mj-source-relationships path").count() == 7
        assert page.locator("#mj-source-junctions circle").count() == 2
        button = page.locator("#mj-stage-explore-toggle")
        button.click()
        page.wait_for_function("window.__mjourneyStageExplore.state().active")
        page.wait_for_timeout(150)
        after = page.evaluate("""() => {
          const stage = document.querySelector('#stage').getBoundingClientRect();
          const svg = document.querySelector('#stage svg');
          const headers = [...document.querySelectorAll(
            '#mj-stage-strip .mj-stage-name')].map(el => {
            const r = el.getBoundingClientRect();
            return {name:el.textContent,
              id:el.dataset.stageId,
              visible:el.style.visibility !== 'hidden',
              left:r.left,right:r.right};
          });
          return {stageLeft:stage.left,stageRight:stage.right,
            svgTransform:svg.style.transform,
            viewBox:svg.getAttribute('viewBox'),
            docW:document.documentElement.scrollWidth,
            docH:document.documentElement.scrollHeight,
            width:innerWidth,height:innerHeight,
            visibleHeadings:headers.filter(x=>x.visible),
            hiddenHeadings:headers.filter(x=>!x.visible),
            originalSourceIDs: [...document.querySelectorAll(
              '#stations [data-station-id]')].map(el=>el.dataset.stationId),
            guidePairs: [...document.querySelectorAll(
              '#lines path[data-src][data-dst]')].map(el=>
                el.dataset.src + '>' + el.dataset.dst),
          };
        }""")
        assert after["viewBox"] == original["camera"]
        assert "scale(1.65)" in after["svgTransform"], after
        assert after["originalSourceIDs"] == original["stationIds"]
        assert after["guidePairs"] == original["guides"]
        assert after["docW"] <= 1441 and after["docH"] <= 901, after
        assert 1 <= len(after["visibleHeadings"]) < 10, after
        assert len(after["hiddenHeadings"]) >= 1, after
        assert all(after["stageLeft"] - 1 <= h["left"] <= h["right"] <=
                   after["stageRight"] + 1 for h in after["visibleHeadings"]), after
        visible = sorted(after["visibleHeadings"], key=lambda x:x["left"])
        assert all(visible[i]["right"] <= visible[i+1]["left"] + 1
                   for i in range(len(visible)-1)), after
        assert button.get_attribute("aria-pressed") == "true"
        assert page.locator("#mj-source-relationships path").count() == 7
        assert page.locator("#mj-source-junctions circle").count() == 2
        page.screenshot(path=str(OUT / "stage-explore-vendor-1440.png"),
                        full_page=True)

        # Existing source-stage dropdown is now an exploratory pan navigator.
        page.locator("#mj-stage-picker").select_option("stage-10")
        page.wait_for_function("""() => window.__mjourneyStageExplore.state()
          .selectedStage === 'stage-10'""")
        page.wait_for_timeout(150)
        later = page.evaluate("""() => ({
          transform: document.querySelector('#stage svg').style.transform,
          centers: [...document.querySelectorAll(
            '#stations [data-station-id="eq67"]')].map(el => {
              const p = document.querySelector('#stage svg').createSVGPoint();
              p.x = Number(el.getAttribute('cx'));
              p.y = Number(el.getAttribute('cy'));
              return p.matrixTransform(el.getScreenCTM()).x;
            }),
          stage: document.querySelector('#stage').getBoundingClientRect().toJSON(),
          viewBox: document.querySelector('#stage svg').getAttribute('viewBox'),
        })""")
        assert later["transform"] != after["svgTransform"], later
        assert later["viewBox"] == original["camera"]
        assert later["stage"]["left"] <= later["centers"][0] <= later["stage"]["right"], later
        page.screenshot(path=str(OUT / "stage-explore-lifecycle-1440.png"),
                        full_page=True)

        # Fit reverses the display-only transform, without touching a station.
        button.click()
        assert not page.evaluate("window.__mjourneyStageExplore.state().active")
        assert page.evaluate("""() =>
          document.querySelector('#stage svg').getAttribute('viewBox')""") == original["camera"]
        assert page.evaluate("""() =>
          document.querySelector('#stage svg').style.transform""") in ("", "none")
        assert page.locator("#mj-stage-explore-toggle").get_attribute(
            "aria-pressed") == "false"
        # The native heading strip must be measured *after* reset and not
        # inherit stale transformed x-coordinates from the explored map.
        page.wait_for_function("""() => {
          const stage = document.querySelector('#stage').getBoundingClientRect();
          const headers = [...document.querySelectorAll(
            '#mj-stage-strip .mj-stage-name')].map(e=>e.getBoundingClientRect());
          return headers.length === 10 &&
            headers[0].left >= stage.left - 1 &&
            headers[3].left > stage.left + 150 &&
            headers[6].left > headers[3].left + 150;
        }""")

        # Compact frames never receive the camera, even if user was exploring.
        page.set_viewport_size({"width": 950, "height": 520})
        page.wait_for_timeout(150)
        assert not button.is_visible()
        assert not page.evaluate("window.__mjourneyStageExplore.state().active")
        assert page.evaluate("""() =>
          document.querySelector('#stage svg').getAttribute('viewBox')""") == original["camera"]
        assert page.locator("#line-toggles .chip").count() == 7
        assert page.locator("#stations [data-station-id]").count() == 67
        assert page.locator("#lines path[data-src][data-dst]").count() == 60
        # Regression: after zoom + stage-10 focus + Fit + viewport resize,
        # all compact stage headings must return to their *native* positions.
        # The previous implementation packed all ten at the left margin.
        page.wait_for_function("""() => {
          const stage = document.querySelector('#stage').getBoundingClientRect();
          const labels = [...document.querySelectorAll(
            '#mj-stage-strip .mj-stage-name')];
          const boxes = labels.map(e => e.getBoundingClientRect());
          return labels.length === 10 &&
            labels[0].textContent === '01' &&
            labels[9].textContent === '10' &&
            boxes[0].left >= stage.left - 1 &&
            boxes[9].right <= stage.right + 1 &&
            boxes[9].left > stage.left + 650 &&
            boxes.every((box,i) => i === 0 ||
              box.left >= boxes[i-1].left + 18);
        }""")
        page.screenshot(path=str(OUT / "stage-explore-native-fit-950.png"),
                        full_page=True)
        assert not errors, errors
        metrics = {
          "originalSourceIDsPreserved": len(original["stationIds"]),
          "originalDirectedRelations": original["edges"],
          "originalGuidesPreserved": len(original["guides"]),
          "originalStages": original["stageNames"],
          "nativeViewBoxPreserved": original["camera"],
          "uniformExploreScale": 1.65,
          "visibleStageNamesInEnlargedViewport": [x["id"] for x in visible],
          "responsiveCompactFitRetained": True,
          "approvedInterchanges": 0,
          "researchMeaningChanged": False,
          "visualApproval": "pending independent screenshot review",
        }
        OUT.mkdir(exist_ok=True)
        (OUT / "stage-explore-metrics.json").write_text(
            json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        print("TM-01c stage exploration Chromium PASS", json.dumps(metrics))
        browser.close()


if __name__ == "__main__":
    main()
