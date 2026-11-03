"""W382 fork-only Chromium visual gate for the original native Legible Cities renderer.

Before running, generate out/system-browser.html with --system-v3,
--stage-demand-corridors, --html and the two authored focus-path arguments.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "out"
PAGE = OUT / "system-browser.html"


def main() -> None:
    from playwright.sync_api import sync_playwright

    assert PAGE.is_file(), "Generate out/system-browser.html first"
    errors: list[str] = []
    records: dict[str, object] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 950, "height": 520},
                                device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(PAGE.as_uri(), wait_until="load")
        page.wait_for_function("!!window.__mjourneyCartography")
        source = json.loads((OUT / "system-browser.research.json").read_text(
            encoding="utf-8"))
        # A visible explanatory note may not paint over research Moments.
        # This is a painted-geometry check, not just SVG stage containment.
        def check_note_clearance(width: int, inspector_open: bool) -> None:
            measured = page.evaluate("""() => {
              const note = document.querySelector('#mj-static-cartography-note');
              const inspector = document.querySelector('#mj-inspector');
              const svg = document.querySelector('#stage svg');
              const noteRect = note.getBoundingClientRect();
              const style = getComputedStyle(note);
              const painted = !note.hidden && style.display !== 'none' &&
                style.visibility !== 'hidden' && noteRect.width > 0 &&
                noteRect.height > 0;
              const box = r => ({left:r.left,top:r.top,right:r.right,bottom:r.bottom});
              const clash = (a,b,m=2) => a.left < b.right + m &&
                a.right + m > b.left && a.top < b.bottom + m &&
                a.bottom + m > b.top;
              const labels = [...document.querySelectorAll(
                '#mj-readable-labels .mj-readable-label')]
                .filter(el => el.getClientRects().length &&
                              getComputedStyle(el).visibility !== 'hidden');
              const tags = [...document.querySelectorAll(
                '#mj-cartography-terminus-labels .mj-cartography-tag')]
                .filter(el => el.getClientRects().length);
              const noteBox = box(noteRect), ctm = svg.getScreenCTM();
              const discHits = [...document.querySelectorAll(
                '#mj-cartographic-markers circle[data-source-moment-ref], ' +
                '#mj-cartographic-source-branch circle[data-source-junction-ref]')]
                .filter(el => getComputedStyle(el.parentElement).display !== 'none')
                .map(el => {
                  const p = svg.createSVGPoint();
                  p.x = Number(el.getAttribute('cx'));
                  p.y = Number(el.getAttribute('cy'));
                  const pos = p.matrixTransform(ctm);
                  const r = Number(el.getAttribute('r')) *
                    Math.hypot(ctm.a,ctm.b) + 2;
                  const dx = Math.max(noteBox.left-pos.x,0,pos.x-noteBox.right);
                  const dy = Math.max(noteBox.top-pos.y,0,pos.y-noteBox.bottom);
                  return {id:el.dataset.sourceMomentRef ||
                    el.dataset.sourceJunctionRef,hit:dx*dx+dy*dy < r*r};
                }).filter(x=>x.hit).map(x=>x.id);
              const visibleOnScreen = noteRect.left >= 0 &&
                noteRect.right <= innerWidth + 1 &&
                noteRect.top >= 0 && noteRect.bottom <= innerHeight + 1;
              const inspectorRect = inspector.getBoundingClientRect();
              return {
                painted, text:note.textContent, host:note.parentElement.id,
                noteBox, visibleOnScreen,
                insideInspector:noteRect.left >= inspectorRect.left &&
                  noteRect.right <= inspectorRect.right &&
                  noteRect.top >= inspectorRect.top &&
                  noteRect.bottom <= inspectorRect.bottom,
                labelHits:labels.filter(el =>
                  clash(noteBox,box(el.getBoundingClientRect())))
                  .map(el=>el.textContent.trim()),
                tagHits:tags.filter(el =>
                  clash(noteBox,box(el.getBoundingClientRect())))
                  .map(el=>el.textContent.trim()),
                stageHeadingHits:[...document.querySelectorAll(
                  '#mj-stage-strip .mj-stage-name')]
                  .filter(el=>clash(noteBox,box(el.getBoundingClientRect())))
                  .map(el=>el.dataset.visibleStage),
                discHits,
              };
            }""")
            assert measured["painted"], measured
            assert "not transit transfers" in measured["text"], measured
            assert measured["visibleOnScreen"], measured
            assert not measured["labelHits"], measured
            assert not measured["tagHits"], measured
            assert not measured["stageHeadingHits"], measured
            assert not measured["discHits"], measured
            if width <= 1080 and inspector_open:
                assert measured["host"] == "mj-inspector", measured
                assert measured["insideInspector"], measured
            else:
                assert measured["host"] == "stage", measured

        assert len(source["canonical"]["moments"]) == 67
        assert len(source["canonical"]["relationships"]) == 87
        assert len(source["canonical"]["categories"]) == 7
        assert len(source["presentation"]["categoryGuides"]) == 60
        expected = [edge for f in source["focusSequences"]
                    for edge in f["sourceEdgeIds"]]
        assert len(expected) == 7
        assert set(expected) == {"edge44", "edge45", "edge48", "edge49",
                                 "edge50", "edge51", "edge52"}

        for width, height in [(950, 520), (1440, 900)]:
            page.set_viewport_size({"width": width, "height": height})
            page.wait_for_function(
                "() => window.__mjourneyCartography.markerCount() === 67")
            page.wait_for_timeout(250)
            result = page.evaluate("""() => {
              const cart = window.__mjourneyCartography;
              const source = window.__mjourneyResearchViewer;
              const stage = document.querySelector('#stage').getBoundingClientRect();
              const original = [...document.querySelectorAll('#stations [data-station-id]')]
                .map(el => el.dataset.stationId);
              const marks = [...document.querySelectorAll(
                '#mj-cartographic-markers [data-source-moment-ref]')]
                .map(el => el.dataset.sourceMomentRef);
              const links = [...document.querySelectorAll(
                '#mj-cartographic-source-branch path[data-source-edge-id]')]
                .map(el => ({id:el.dataset.sourceEdgeId,from:el.dataset.sourceFrom,
                             to:el.dataset.sourceTo,notTransfer:
                               el.dataset.researchLinkNotTransfer === 'true'}));
              const headings = [...document.querySelectorAll(
                '#mj-stage-strip .mj-stage-name')].map(el => ({
                  id:el.dataset.stageId,
                  name:el.dataset.visibleStage,
                  original:el.textContent,
                  width:el.getBoundingClientRect().width,
                  painted:getComputedStyle(el, '::after').content
                }));
              const box = el => {
                const r = el.getBoundingClientRect();
                return {left:r.left,top:r.top,right:r.right,bottom:r.bottom};
              };
              const tags = [...document.querySelectorAll(
                '#mj-cartography-terminus-labels .mj-cartography-tag')].map(box);
              const labels = [...document.querySelectorAll(
                '#mj-readable-labels .mj-readable-label')]
                .map(el => ({...box(el), id:el.dataset.momentId}));
              const stationDiscs = [...document.querySelectorAll(
                '#mj-cartographic-markers circle[data-source-moment-ref], ' +
                '#mj-cartographic-source-branch circle[data-source-junction-ref]')]
                .map(el => {
                  const point = source.svg.createSVGPoint();
                  point.x = Number(el.getAttribute('cx'));
                  point.y = Number(el.getAttribute('cy'));
                  const screen = point.matrixTransform(source.svg.getScreenCTM());
                  const ctm = source.svg.getScreenCTM();
                  return {id:el.dataset.sourceMomentRef || el.dataset.sourceJunctionRef,
                    x:screen.x,y:screen.y,
                    r:Number(el.getAttribute('r'))*Math.hypot(ctm.a,ctm.b)+2};
                });
              const note = document.getElementById('mj-static-cartography-note');
              return {sourceMomentCount:source.moments.size,
                authoredRelations:source.relationships.length,
                categories:source.data.canonical.categories.length,
                stationIds:original, markerIds:marks,
                guideCount:cart.categoryGuideCount(),
                links, headings, tags, labels, stationDiscs,
                defaultFocusText:document.querySelector(
                  '#mj-focus-select option:checked').textContent.trim(),
                branchLegend:note.textContent, branchLegendVisible:!note.hidden,
                visibleLabelCount:labels.length,
                branchVisible:getComputedStyle(document.querySelector(
                  '#mj-cartographic-source-branch')).display !== 'none',
                inspectorHidden:document.querySelector('#mj-inspector').hidden,
                docWidth:document.documentElement.scrollWidth,
                docHeight:document.documentElement.scrollHeight,
                stageWidth:stage.width, stageHeight:stage.height};
            }""")
            assert result["sourceMomentCount"] == 67, result
            assert result["authoredRelations"] == 87, result
            assert result["categories"] == 7, result
            assert result["guideCount"] == 60, result
            assert result["stationIds"] == result["markerIds"], result
            assert len(set(result["stationIds"])) == 67, result
            assert sorted(item["id"] for item in result["links"]) == sorted(expected)
            assert all(item["notTransfer"] for item in result["links"])
            assert all(any(r["id"] == edge["id"] and
                           r["fromId"] == edge["from"] and
                           r["toId"] == edge["to"] for r in
                           source["canonical"]["relationships"]) for edge in
                           result["links"])
            assert result["branchVisible"]
            assert result["defaultFocusText"] == "A&E/direct overview", result
            assert result["branchLegendVisible"]
            assert "authored relationships" in result["branchLegend"]
            assert "not transit transfers" in result["branchLegend"]
            assert result["inspectorHidden"]
            assert result["docWidth"] <= width + 1, result
            assert result["docHeight"] <= height + 1, result
            check_note_clearance(width, inspector_open=False)
            assert len(result["headings"]) == 10
            assert [h["name"] for h in result["headings"]] == [
                s["name"] for s in source["canonical"]["stages"]]
            assert all(h["width"] >= 38 for h in result["headings"]), result
            assert result["visibleLabelCount"] >= (10 if width < 1100 else 18)
            # The measured label engine owns the main label collision rule.
            for i, a in enumerate(result["labels"]):
                for b in result["labels"][i + 1:]:
                    assert not (a["left"] < b["right"] + 3 and
                                a["right"] + 3 > b["left"] and
                                a["top"] < b["bottom"] + 3 and
                                a["bottom"] + 3 > b["top"]), (a, b)
            for tag in result["tags"]:
                for label in result["labels"]:
                    assert not (tag["left"] < label["right"] + 4 and
                                tag["right"] + 4 > label["left"] and
                                tag["top"] < label["bottom"] + 4 and
                                tag["bottom"] + 4 > label["top"]), (tag, label)
            # Every readable label must clear unrelated rendered stations and
            # source endpoint rings, with a genuine 2px measured margin.
            for label in result["labels"]:
                for station in result["stationDiscs"]:
                    if label["id"] == station["id"]:
                        continue
                    dx = max(label["left"] - station["x"], 0,
                             station["x"] - label["right"])
                    dy = max(label["top"] - station["y"], 0,
                             station["y"] - label["bottom"])
                    assert dx * dx + dy * dy >= station["r"] ** 2, (
                        label, station)
            # Existing compact DOM remains numbered for legacy navigation
            # tests and accessible names; CSS renders actual source names.
            if width == 950:
                assert result["headings"][0]["original"] == "01", result
                assert all(h["painted"] == json.dumps(h["name"]) for h in
                           result["headings"]), result
            else:
                assert result["headings"][0]["original"] == "Business need"
                assert all(h["painted"] == "none" for h in
                           result["headings"]), result
            page.screenshot(path=str(OUT / f"cartography-w382-{width}.png"),
                            full_page=True)
            records[f"{width}x{height}"] = {
                "momentCount": 67, "relationshipCount": 87,
                "guideCount": 60, "layerCount": 7,
                "sourceOverlayEdges": expected,
                "visibleMomentLabels": result["visibleLabelCount"],
                "guideTerminusLabels": len(result["tags"]),
                "sourceStageNames": [h["name"] for h in result["headings"]],
                "noOverlap": True, "noViewportOverflow": True,
            }

        # Viewer remains fully interactive and the same research path never
        # appears twice when a focused or review-only overlay is selected.
        focus = page.locator("#mj-focus-select")
        focus.select_option("all")
        assert not page.locator("#mj-cartographic-source-branch").is_visible()
        assert page.locator("#mj-source-relationships path").count() == 7
        page.screenshot(path=str(OUT / "cartography-w382-fork-1440.png"),
                        full_page=True)
        focus.select_option("review:handoffs")
        assert not page.locator("#mj-cartographic-source-branch").is_visible()
        assert page.locator("#mj-semantic-review-edges path").count() == 3
        focus.select_option("")
        assert page.locator("#mj-cartographic-source-branch").is_visible()
        page.locator("#mj-moment-picker").select_option("eq31")
        assert page.locator("#mj-inspector-heading").inner_text() == (
            "Funding authorized")
        assert page.locator("#mj-inspector").is_visible()
        # The native SVG viewBox must remain intact and all 67 Moment centers
        # remain inside the *actual docked inspector* map at BOTH viewports.
        for width, height in [(1440, 900), (950, 520)]:
            page.set_viewport_size({"width": width, "height": height})
            page.wait_for_timeout(350)
            inspector = page.evaluate("""() => {
              const stage = document.querySelector('#stage').getBoundingClientRect();
              const svg = document.querySelector('#stage svg');
              const ctm = svg.getScreenCTM();
              const visible = [...document.querySelectorAll(
                '#mj-cartographic-markers circle[data-source-moment-ref]')]
                .filter(mark => {
                  const p = svg.createSVGPoint();
                  p.x = Number(mark.getAttribute('cx'));
                  p.y = Number(mark.getAttribute('cy'));
                  const q = p.matrixTransform(ctm);
                  return q.x >= stage.left && q.x <= stage.right &&
                         q.y >= stage.top && q.y <= stage.bottom;
                }).length;
              return {visible, sourceViewBox:svg.getAttribute('viewBox'),
                inspectorOpen:!document.querySelector('#mj-inspector').hidden};
            }""")
            assert inspector["visible"] == 67, inspector
            assert inspector["inspectorOpen"]
            assert inspector["sourceViewBox"], inspector
            check_note_clearance(width, inspector_open=True)
            page.screenshot(path=str(OUT / f"cartography-w382-inspector-{width}.png"),
                            full_page=True)
        page.keyboard.press("Escape")
        assert page.locator("#mj-inspector").is_hidden()
        assert page.locator("#line-toggles .chip").count() == 7
        assert not errors, errors
        browser.close()

    (OUT / "cartography-w382-metrics.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print("W382 static cartography Chromium PASS", json.dumps(records))


if __name__ == "__main__":
    main()
