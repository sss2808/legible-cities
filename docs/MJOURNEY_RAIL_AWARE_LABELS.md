# TM-01d rail-aware Moment label placement

**Status:** cartographic experiment in the native Legible Cities fork, draft and unmerged. [M-Journey TM-01d issue #446](https://github.com/sss2808/m-journey/issues/446). Dependent on [fork PR #23](https://github.com/sss2808/legible-cities/pull/23) exact base `31a39446b2bd829a869c55cdcf756c9be2bdf649`, itself stacked on semantic review PR #22, responsive framing #21 and category geometry #20. Shared M-Journey transit-map register remains W373/PR #431 owned.

## Problem and measured baseline

The existing System HTML label placer checks viewport bounds, the ten source stage headers, and label-to-label collisions. It does **not** inspect the 60 original colored category guides or the directed source relationship highlights drawn over them. This makes research Moment names appear on top of tracks, particularly around the documented Funding authorized → A&E/direct → Vendor selected alternatives.

A local real-Chromium baseline using the pinned 67-Moment public fixture, native fork HTML and the unchanged `Compare alternatives` option at **1440×900** found **14 visible key labels, 7 intersecting at least one visible source line or category guide**. The direct visual candidate measured **14 key labels, 2 intersecting a visible line**. This is an experimental before/after measurement, not a promise of zero intersections in all modes or an independent human acceptance.

The browser acceptance workflow reproduces the exact scenario from the current GitHub head and separately records the remaining collisions and map identities.

## Bounded implementation

Only the placement portion of `src/schematic/page/mjourney_labels.js` changes; it retains the original source candidate ordering, key/more density modes, exact canonical label text, chosen Moment IDs and maximum visible label counts. No source Moment coordinate or SVG viewBox changes.

1. **Read-only native rail obstacles.** Sample the displayed SVG paths under `#lines path[data-src][data-dst]` (original category guides) and `#mj-source-relationships path`/`#mj-semantic-review-edges path` (already-authored relation overlays). Ignore hidden category paths. Transform points into the existing stage's actual browser coordinate system; this includes optional desktop Explore transforms.
2. **Preserve original candidate positions.** Try the original four label anchors first, followed by six nearby offset anchors. For each that clears viewport, stage headings and other labels, score its native line intersections with a short visible-line margin. Directed highlight intersections carry stronger preference than guide intersections, but **neither becomes a source graph edge or transfer**.
3. **Prefer a clear nearby label.** Use the first zero-intersection candidate, otherwise the lowest-collision candidate. Preserve a label in its original source order rather than hiding it when the rail geometry is too dense. Record a per-label numeric `data-rail-clearance-score` for audit/debugging only; this is **not persisted research metadata or a ranking of station importance**.
4. **Keep semantics explicit.** The seven colored lines remain category/workstream guides; the focus strokes remain exact existing directed research relationships. A junction or overlap of drawn segments creates no authored transfer, customer pathway or new line membership.

### Changed files

| Path | Ownership and change |
| --- | --- |
| `src/schematic/page/mjourney_labels.js` | Bounded stacked modification to original label candidate placement; no scene/renderer geometry changes |
| `tests/browser/test_mjourney_label_clearance.py` | New independent live Chromium collision counter and before/after source checks |
| `.github/workflows/mjourney-label-clearance.yml` | New isolated original-fixture, native renderer and browser visual regression jobs |
| `docs/MJOURNEY_RAIL_AWARE_LABELS.md` | This review/interpretation record |

**No edit** to `mjourney.py`, stage/guide routing, native renderer, `mjourney_scene.js`, `mjourney_stage_explore.js`, source fixture, M-Journey product, importer/Editor, portfolio, GPL licensing, shared register or source relationships. This branch is stacked on but does not change any prior PR's branch.

## Evidence and tests

```bash
node --check src/schematic/page/mjourney_labels.js
python bin/mjourney-preview --system-v3 --stage-demand-corridors --html \
  --focus-path ae=edge44,edge48,edge49,edge50 \
  --focus-path direct=edge45,edge51,edge52 \
  --output out/system-browser.svg
python tests/browser/test_mjourney_label_clearance.py
python tests/browser/test_mjourney_browser.py
python tests/browser/test_mjourney_semantic_review.py
python tests/browser/test_mjourney_responsive_frame.py
python tests/browser/test_mjourney_stage_explore.py
```

The new browser test measures all 14 key labels at desktop Fit in Compare alternatives, asserts **no more than 3 label/rail intersections** compared with the independently measured 7 baseline, and requires no funding/vender-reconvergence label collision. It also checks zero label-label collisions, at least as many visible labels in More mode, source-only handoff overlays, dynamic Explore-stage redrawing, compact screen Fit and that the native world station coordinates, source IDs, 60 painted category guides, original viewBox and 87 directed records remain unchanged.

CI screenshots: `rail-labels-key-1440.png`, `rail-labels-more-1440.png`, `rail-labels-explore-1440.png`, `rail-labels-compact-950.png`, and `rail-labels-metrics.json`. All numbers apply to the tested browser and state; they are not a measure of source truth.

### Independent visual and semantic gates

- Even two remaining label/rail intersections in the dense A&E/direct interchange *visual* area deserve review; no extra conceptual interchange was created.
- Some stage headings and labels still appear small in a 10-stage overview. Desktop Explore remains an optional readability control, not an approved default map camera.
- Since each Moment has one primary layer and category guides remain non-traversable, this approach cannot manufacture a dense shared metro network. A future TM-02/TM-03 approved multi-membership or path contract is a separate decision, not inferred from geometry.
- Confirm source unchanged, run isolated and inherited exact-head tests, conduct human screenshot review, and review inherited general fork-suite `test_site.py` description-count issue separately.
- Fork GPL-3.0 distribution and any M-Journey/portfolio integration remain separate legal/product gates. This PR must remain draft and unmerged until reviewed.
