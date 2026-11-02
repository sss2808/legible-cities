# M-Journey cartographic reference: LA Metro REA deep dive

**Date:** 2026-11-02  
**Status:** Browser-observed research and implementation guidance; **not** approval of a research route, new transit line, customer transfer, layout, or portfolio release.  
**Reference:** [Original Legible Cities LA Metro Rail](https://richc117.github.io/legible-cities/maps/la-metro-rail.html)  
**User evidence:** `rea-legible-deep-dive.zip`, supplied in the development conversation. The private archive contains seven JSON page observations and six corresponding PNG screenshots embedded in JSON. Screenshots are not committed to the public repo. SHA-256 for the relevant original first-party viewer script: `d7c45133fe5f0480d44fe3c8271b5eb343dc3fac023eeac7a6fa9b00251c3e91`. The script observed is 56,142 characters. Browser: Chrome 149, 1920 × 945 screenshot viewport.  
**Code baseline for implementation:** [Draft PR #3](https://github.com/sss2808/legible-cities/pull/3) (18-source-station native LOOM proof); [Draft PR #4](https://github.com/sss2808/legible-cities/pull/4) (23-source-station six-line diagnostic). Neither is merged into the product or portfolio.

## Executive assessment

The original LA Metro example is **sufficient for the next phase**. It demonstrates a central high-degree hub, six continuous line identities, shared tracks, 45-degree branches, intersections, single-line/multiple-line focus, a schematic map, a geographic alternative and a line-oriented Linear representation. It does **not** establish how to transform seven organizational workstreams into seven passenger-like routes or permit invented research transfers.

The owner correctly observed **real angular turns in the original**. A 45-degree corner is not intrinsically a defect. The priority is deliberate bend count, stable line identity, consistent joins and caps, spacing through shared corridors and junctions, station/label hierarchy, and camera framing. An optional radius treatment is a render-level design choice, not a mandate to override LOOM or fabricate paths.

**A second map with materially different topology is optional later**, e.g. an example with a genuine loop/ring and multiple competing transfer hubs if the equipment-derived cartographic network requires those motifs. Do not run REA on more maps as a prerequisite to fixing the semantic/cartographic adapter.

## Exact captured states and observed outcomes

These are six separately verified, 1-second REA Chrome DevTools Protocol observations. The recorded accessible button states confirm the actual route, label and mode selections, not merely the prompts the operator read.

| Evidence file | Verified view and button states | Direct visual observation | Implication |
| --- | --- | --- | --- |
| `01-schematic-all.json` | Schematic selected; labels on; six lines A, B, C, D, E, K pressed | Dense central interchange, broad branches and several shared or closely spaced corridors; angled labels and octilinear turns | This is the reference for the overview composition, not for forcing every element into a central trunk |
| `02-schematic-line-a.json` | Schematic; **only A pressed**; labels on | Non-A lines disappear; the remaining blue route occupies a meaningful map area and retains its own branches | Focus is visibility **plus content-relative reframing**, not darkening the entire map |
| `03-schematic-lines-a-b.json` | Schematic; **only A and B pressed**; labels on | Two lines simultaneously visible; central crossing and separate branches still legible | Support arbitrary line subsets and shared/crossing geometry, not just exclusive radio selection |
| `04-schematic-no-labels.json` | Schematic; **all six pressed**; **Labels pressed=false** | Full colored network remains visible; labels disappear; map uses tighter available geometry | **Valid labels-off capture**. Prior four-state packet's fourth screenshot was an invalid zero-line state; this new capture resolves it |
| `05-linear-all.json` | **Linear** selected; all six lines pressed; labels on | Distinct horizontal line rows, each preserving label/stop order. Vertical page height expands; the viewport shows only the upper part | Linear is an alternative arrangement of the same station IDs; do not confuse it with the System schematic or current portfolio chapter names |
| `06-geographic-all.json` | **Geographic** selected; all lines pressed; labels on | Same line families and research-equivalent stations occupy different, less strictly octilinear geometry | Preserve graph identity across coordinate representations; do **not** claim M-Journey has geographic/time data or ship an unimplemented Spatial view |

A screenshot record accompanies each of the six observed page states as `<basename>-screenshot.json`; each embeds a PNG for the 1920×945 viewport. This package also contains `07-script-evidence.json` with the original first-party viewer code.

### Relevant source implementation observed through REA

The following are **source-backed** descriptions from the 56,142-character original page script, not invented reimplementations:

- `mapXY` reads each station position from `#stations circle[data-node]`. Rendered SVG positions are the single reference for station/track/label transforms.
- `data.linear` provides per-line rows and stop memberships. The Linear view does not synthesize different stops or a separate research network.
- `trackD(t,m,g)` interpolates **the existing polyline vertices**, with geographic coordinates and line-row coordinates as alternative arrangements. Do not replace solved route polylines with per-edge elbows when changing views.
- `geometry(m,sf,g)` moves tracks, dots and text under one animation/geometry state, and `setBox(m)` adjusts their common SVG camera. Timetable/chart state exists but is inappropriate for M-Journey.
- `fitVisible()` measures visible line groups, stations and text via SVG `getBBox()`, and builds subset bounding boxes for line filters. Important: the fit is **content-relative**, not an unchanging full-network `viewBox`.
- `setBox(m)` explicitly handles `fullBox`, `data-viewbox-nolabels` (`tightBox`) and subset bounds. Therefore labels-off is not merely hiding text: its camera may tighten. Avoid multiple unrelated Fit/viewbox owners.
- `sizeStage()` allows wide networks on narrow screens to retain sufficient width for horizontal scrolling/panning rather than shrinking everything into an unreadable phone-width picture.
- The original script explicitly sets rounded **caps** on some dynamically drawn paths (e.g. `stroke-linecap="round"` for chart lines). This does **not** prove that original map polylines are Bezier-smoothed. The screenshot confirms angular octilinear turns. Separate stroke join/cap styling from underlying centerline geometry.

Only copy the schematic/geometry/camera principles. **Never** reintroduce the rail viewer's train count, clock, timetable, date slider, speed control, GTFS tracks, or customer-as-passenger metaphor.

## What this means for the current 23-station proof

1. **Fix the semantic/cartographic model before tuning dimensions.** The equipment fixture contains 67 research moments, 87 authored relations, 10 ordinal stages, 7 organizational workstreams, and only **two named vendor-selection pathway alternatives**. The other colored activity spurs in PR #4 are technical/financial/site/logistics branches, **not four additional personas**. Maintain separate fields for workstream, authored relationship kind, candidate continuous line membership and analytical overlay classification.
2. **Do not treat workstreams as transit lines automatically.** The visual needs a true interconnected *system* with deliberate continuity, splits, rejoin points, stage progression, and visible handoff/organizational transitions. The same research ID must survive every view.
3. **Retain native LOOM geometry and provenance.** The original 18-station test proved line occupancy and exact native polylines; the expanded 27-edge test lost `eq46→eq47` adjacency and was rejected; the reduced 25-edge test passed. Make adjacency and line identity proof a **non-negotiable gate**. A successful build with solver fallback does not satisfy the native geometry acceptance requirement.
4. **Expand the actual composed System network**, not just the number of stations. A single shared horizontal trunk with small down/up spurs remains a corridor illustration. The full 10-stage map may need an overview abstraction, with progressive zoom revealing secondary research connections without fictional merges.
5. **Use the source's layout logic for selected subsets.** On click, establish the set of visible lines; compute their line/station/label bounds from actual rendered SVG; resize and pan the camera to the subset. Unselected routes should be *omitted or strongly de-emphasized* according to an intentional mode, and the camera must fit active content rather than the all-line background.
6. **Support selection of multiple route families.** The REA A-only and A+B captures prove that an exclusive `Both / A / B` radio model is insufficient to reproduce the original. Decide whether product filter controls should be multiselect with All/None and preserve independent highlight states.
7. **Respect the existing portfolio control design.** `sss2808/P/src/portfolio.html` `.mj-controls` has compact, outlined 3px-radius buttons with 6px gaps and consistent `aria-pressed` states. Keep zoom, Fit and fullscreen inside the visualization at its right, and remove public-facing "cartographic proof", source totals, solver status and "no invented transfers" captions. That content belongs in audits, not the cinematic carousel.
8. **Fix view/label hierarchy.** Ten stage headings are not station labels. Major junction/decision names should read at overview scale, ordinary moments progressively reveal on zoom/selection, and diagonally placed labels must not collide with route tracks. A count of zero renderer-dropped labels is not proof of human legibility.
9. **Preserve angular routing but manage its appearance.** Keep 0°, 45° and 90° network centerlines, minimize gratuitous bend changes, give route stacks sufficient visual gap and use consistent line joins/caps. Apply corner-radius rendering only after testing shared-stroke offset behavior and source-polylines; never refit topology to satisfy a visual preference.
10. **Separate cartographic modes from carousel narrative.** The current standalone proof is **not** the full six-chapter M-Journey portfolio entry. Read the latest `P/AGENTS.md`, `P/docs/EDITORIAL_DESIGN_SYSTEM.md`, and live source before adding chapters or changing approved names. Do not invent a completed Spatial view.

## Proposed acceptance tests

| Gate | Criterion |
| --- | --- |
| Source | Exact research IDs; each drawn traversable connection maps to authorized directed source edges; no invented transfers |
| Geometry | Native LOOM polylines retained; consistent line identities and shared track ordering; station/line adjacency preserved |
| Stages | 10 stages for full map, ordered left to right; stages are **ordinal**, not durations |
| Focus | Single and multiple line subsets; bounds computed from actual visible track/station/label geometry |
| Labels | Overview station hierarchy; no visible overlaps at intended review resolutions; no clipped key names |
| Shape | Recognizable networks, not a narrow single corridor; deliberate 45° bends, readable hubs and convergences |
| Controls | Portfolio visual grammar, multi-select state clarity, zoom/Fit/fullscreen in map, keyboard focus |
| Responsive | 1440px desktop and ~390px mobile, native fullscreen; no forced phone-scale unreadability |
| UI truthfulness | No train/time/timetable controls; no decorative engineering claims or sample statistics in public-facing exhibit |
| Release | Side-by-side visual evidence; source audit; exact-head CI; approval before merges/deployment |

## Scope and evidentiary limits

The REA package is a **browser-state observation**. It does not include LOOM's intermediate C++ solver graph for LA Metro, and it does not disclose the mapping semantics or categorical structure of the M-Journey data. Screenshot shapes alone do not establish that one visualization supports graph-theoretic metrics, organization handoffs, or loops.

The captured DOM count includes invisible/dynamic SVG layers; it must **not** be misread as the number of canonical stations or research moments. The second captured JavaScript source appears as a separate injected/external script and should not be treated as the original metro mapping implementation.

The original geometry is deliberately angular in places. "No sharp edges" is **not** a faithful acceptance criterion. Use line continuity, bend purpose, label/geometry spacing and legibility instead.

### Decision on further REA

**No additional REA now.** LA Metro provides enough geometry and view-state behavior to correct the current adapter and move beyond a corridor. Study a single second reference **only when** the fuller equipment graph demonstrably requires a topology not covered here (ring/loop, multiple independent high-degree hubs, or substantially more complex shared-track crossings). If needed, choose from the original Legible Cities Atlas rather than gathering another generic screenshot set. The original atlas itself describes generated maps of many networks and differing quality; do not presume every map is a polished exemplar.

**Next engineering artifact:** source-backed full System cartographic model and a visual proof with more genuinely differentiated route structure, reviewed against these behavioral gates. Do not ship another 23-station corridor merely with more filters.
