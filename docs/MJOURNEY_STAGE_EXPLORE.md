# TM-01c optional desktop stage exploration

**Status:** fork-only experimental camera/framing proof; independent screenshot review pending, no semantic approval, no product/portfolio integration. [Tracking issue #442](https://github.com/sss2808/m-journey/issues/442).

**Dependency stack:** This branch deliberately stacks on [TM-01b fork PR #22](https://github.com/sss2808/legible-cities/pull/22) at `c1cb83188d8daf6a6434e9c7c94bd9a848f319b0`, which stacks on [responsive framing #21](https://github.com/sss2808/legible-cities/pull/21) and [geometry #20](https://github.com/sss2808/legible-cities/pull/20). None is merged; no parent source branch is edited. W373 [M-Journey register PR #431](https://github.com/sss2808/m-journey/pull/431) remains its own file owner.

## The visual problem and design choice

The 10-stage equipment map is panoramic. In the source-preserving 1440×900 screenshot with the research inspector open, the original Legible Cities SVG occupies a relatively shallow horizontal band. Stations, source-backed branch segments and labels become small in the full-frame view. The 950×520 compact viewer, in contrast, is constrained and already has a regression test proving every one of 67 source stations remains inside its fitted map viewport.

Rather than stretch the rails, change original native SVG viewBox, crop its default Fit or invent visual-only links, this experiment adds **optional desktop exploration**:

1. The initial **Fit-all** state is unchanged and still shows the complete authored journey.
2. An unobtrusive **Explore stages** button is positioned inside spare map space at desktop widths from 1200px. This applies a **uniform CSS scale of 1.65** to the existing native SVG, then pans its display so either the default documented vendor-selection branching region or the selected *source-authored operational stage* is centered. All source coordinates and native SVG viewBox remain byte-for-byte the same.
3. The existing **Stage** selector becomes a simple navigation mechanism while Explore is on. Stage highlighting still operates as before; the new camera changes its *presentation framing only*. Offscreen stage headings are hidden, rather than piling up at the viewport edges. A visible **Fit full journey** action always reverses the transform.
4. At smaller desktop/mobile widths below 1200px the control is hidden and any active exploration is reset to original Fit. The existing 950×520 no-clipped-source-station, seven-chip legend and inspector layout tests remain unchanged.
5. The selected-moment inspector, source-backed `eq31`/`eq37` branch and convergence rings, review-only handoff/return overlays, labels, native lines and category filters remain owned by the existing renderer and research modules. The new code does not create any second graph or station layout.

This mode intentionally shows **only part of the ten-stage map at once**. That is a user-selected exploration, not a replacement for the overview. The inspector/labels must retain source IDs when the camera pans; stage headings outside the viewport must not be represented as if visible. A source relationship leaving the explored viewport is allowed to exit the frame rather than being falsely joined to another moment.

## Exact ownership

| File | Change |
| --- | --- |
| `src/schematic/page/mjourney_stage_explore.js` | **New**, isolated opt-in source-stage CSS transform, bounded pan, reversible fit and header visibility |
| `bin/mjourney-preview` | **Bounded stack-only change**, style for the opt-in button and a script bootstrap after PR #22's semantic review script |
| `tests/browser/test_mjourney_stage_explore.py` | **New**, Chromium source/viewport/stage/label/inspector/reversibility checks at 1440×900 and 950×520, screenshot evidence |
| `.github/workflows/mjourney-stage-explore.yml` | **New**, source integrity, JavaScript syntax and Chromium screenshots plus inherited responsive and semantic regression |
| `docs/MJOURNEY_STAGE_EXPLORE.md` | **New**, scope, design rationale, limits, review and provenance |

No edit to M-Journey `AGENTS.md`, workstream register, canonical journey CSVs, original 67/87 source fixture, `mjourney.py`, core Legible Cities renderer, `mjourney_scene.js`, research contract, native corridor router, editor, app/portfolio, licensing or native simulation.

## Research and cartographic protections

- Original source: 67 research moments, 87 authored directed relationships, 7 colored category membership lines and their 60 **non-traversable** guide segments, 10 authored operational stages. These are unchanged.
- The stage selector's names/order are source facts, not proportional calendar distances. The CSS uniform scale preserves H/V/45° native geometry and original world coordinates; panning does **not** create a new source edge, transit transfer, multi-line membership, causal or chronological interpretation.
- Explicit source branch/convergence overlays and optional handoff/return review semantics remain separate from colored category guides. W375 [classification PR #435](https://github.com/sss2808/m-journey/pull/435) is unmerged and still awaiting independent research review.
- This is an **exploration viewport**, not the official default fully fitted overview, not an animated transition, and not a new M-Journey authoring/export schema.

## Verification and independent review

```bash
node --check src/schematic/page/mjourney_stage_explore.js
python bin/mjourney-preview --system-v3 --stage-demand-corridors --html \
  --focus-path ae=edge44,edge48,edge49,edge50 \
  --focus-path direct=edge45,edge51,edge52 \
  --output out/system-browser.svg
python tests/browser/test_mjourney_stage_explore.py
python tests/browser/test_mjourney_semantic_review.py
python tests/browser/test_mjourney_responsive_frame.py
```

The dedicated workflow checks the original frozen P0a source byte SHA; validates the 67/87/60 identities, native viewBox and 10 original stages; tests native branch focus preservation, stage selection, offscreen heading suppression, no document overflow, inspector with selected moment and return to Fit; then captures actual `stage-explore-fit-1440.png`, `stage-explore-vendor-1440.png`, `stage-explore-lifecycle-1440.png`, `stage-explore-native-fit-950.png`, and JSON metrics for human review.

**Review pending:** screenshot comparison for visual balance and stage-label clearance, exact-head CI and the inherited full suite. Native #20/#21 original broad suite has one known unrelated `test_site.py` page-description assertion; do not waive or conflate this with success of focused tests. PR remains draft, unmerged, undeployed; the fork's GPL-3.0 distribution boundary remains separate.
