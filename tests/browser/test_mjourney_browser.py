"""Chromium smoke and screenshots for isolated fork System research viewer.

Run only after generating out/system-browser.html; not imported by normal pytest.
All assertions target sanitized public data, no private Dovetail calls.
"""
from __future__ import annotations
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
VIEWER = ROOT / "out/system-browser.html"
OUT = ROOT / "out"


def main():
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
        # Optional focus edges must all exist in the canonical directed graph.
        focus_select = page.locator("#mj-focus-select")
        assert focus_select.locator("option").count() == 4
        assert page.locator("#mj-source-relationships path").count() == 0
        frame = page.evaluate("""() => ({
            width: document.documentElement.scrollWidth,
            height: document.documentElement.scrollHeight,
            viewportHeight: window.innerHeight,
            stageHeight: document.querySelector("#stage").getBoundingClientRect().height
        })""")
        assert frame["width"] <= 951
        assert frame["height"] <= frame["viewportHeight"] + 1, frame
        assert frame["stageHeight"] >= 200
        page.screenshot(path=str(OUT / "system-overview-950.png"), full_page=True)
        focus_select.select_option("ae")
        assert page.locator("#mj-source-relationships path").count() == 4
        assert set(page.locator("#mj-source-relationships path").evaluate_all(
            "(xs) => xs.map(x => x.dataset.sourceEdgeId)")) == {
                "edge44", "edge48", "edge49", "edge50"}
        focus_select.select_option("direct")
        assert page.locator("#mj-source-relationships path").count() == 3
        focus_select.select_option("all")
        highlighted_ids = page.locator("#mj-source-relationships path").evaluate_all(
            "(xs) => xs.map(x => x.dataset.sourceEdgeId)")
        assert len(highlighted_ids) == len(set(highlighted_ids)) == 7
        assert "edge45" in highlighted_ids and "edge52" in highlighted_ids
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
        assert not page.locator("#mj-inspector").evaluate("(el) => el.hidden")
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
        assert page.locator("#mj-stage-strip .mj-stage-name").count() == 10
        assert page.locator("#mj-source-relationships path").count() == 7
        page.screenshot(path=str(OUT / "system-focus-1440.png"), full_page=True)
        page.screenshot(path=str(OUT / "system-research-1440.png"), full_page=True)
        assert not issues, "Browser page errors: " + "; ".join(issues)
        browser.close()
    print("Chromium M-Journey inspector and source-route isolation smoke PASS")


if __name__ == "__main__":
    main()
