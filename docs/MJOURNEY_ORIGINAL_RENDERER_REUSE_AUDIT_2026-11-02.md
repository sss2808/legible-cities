# Reuse audit for the original Legible Cities renderer in M-Journey

**Date:** 2026-11-02  
**Status:** Source-reviewed implementation specification; **not** a visual approval, redesign, or code migration.  
**Scope:** Oriented label collision, multi-line offsets, SVG track/station identities, route focus, and content-aware framing.  
**Separate workstream:** LOOM \`topo\` nondeterminism and the topology-stage preservation policy are being investigated independently. Do not resolve them here. Exact Web Mercator corrections are on [draft PR #6](https://github.com/sss2808/legible-cities/pull/6). Do not duplicate or modify that work.

## Executive conclusion

**We already call the original \`schematic.render.render()\` to draw the M-Journey proofs.** That means the engine already solves static oriented label placements, shared-track offset geometry, station markers and emitted line groups. The current failure is **partially an integration/reuse problem**, not that none of these systems exists. The proof's custom HTML then bypasses other original capabilities: it hides most placed labels with CSS, uses an all-or-nothing label toggle, leaves route focus in a static full-map viewport, and implements Fit as a fixed \`viewBox\` reset. Also, stage headings are appended **after** static label placement and so are not obstacles considered by the label solver.

**Do not rewrite \`labels.py\`, \`offsets.py\`, \`build_tracks\`, or a second SVG path engine.** Use their existing contracts and tests; adapt the presentation/camera layer to M-Journey semantics, and add only the API extensions that the engine demonstrably lacks.

The renderer also **cannot invent legitimate network topology, choose customer journeys or automatically decide organizational-layer semantics**. Fixing its integration is necessary for polish, but will not turn the existing corridor into a multi-hub system. That modeling issue is separate.

## 1. Original sources inspected

All paths are relative to the upstream [\`richc117/legible-cities\`](https://github.com/richc117/legible-cities) repository; equivalent files are present in the fork.

| Mechanism | Authoritative implementation | Independent tests |
| --- | --- | --- |
| Oriented label placement | [\`src/schematic/labels.py\`](https://github.com/richc117/legible-cities/blob/main/src/schematic/labels.py), \`Quad\`, \`collide\`, \`candidates\`, \`place\`, \`polyline_quads\` | [\`tests/test_geometry.py\`](https://github.com/richc117/legible-cities/blob/main/tests/test_geometry.py), [\`tests/test_fonts.py\`](https://github.com/richc117/legible-cities/blob/main/tests/test_fonts.py) |
| Offset strokes on shared edges | [\`src/schematic/offsets.py\`](https://github.com/richc117/legible-cities/blob/main/src/schematic/offsets.py), \`offset_polyline\`, \`slot_offsets\`, \`track_offset\` | [\`tests/test_offsets.py\`](https://github.com/richc117/legible-cities/blob/main/tests/test_offsets.py), \`test_geometry.py\` |
| Native SVG tracks and groups | [\`src/schematic/render.py\`](https://github.com/richc117/legible-cities/blob/main/src/schematic/render.py), \`Projection.fit\`, \`TrackPath\`, \`RenderResult\`, \`build_tracks\`, \`render\` | [\`tests/test_line_order.py\`](https://github.com/richc117/legible-cities/blob/main/tests/test_line_order.py), [\`tests/test_colors.py\`](https://github.com/richc117/legible-cities/blob/main/tests/test_colors.py), \`test_fonts.py\` |
| Stable station source identity | [\`src/schematic/linegraph.py\`](https://github.com/richc117/legible-cities/blob/main/src/schematic/linegraph.py), \`Node.station_id\`, \`LineGraph.from_geojson\`, \`LineGraph.reproject\` | \`tests/test_line_order.py\` and pipeline stage/identity tests |
| Browser labels, camera and view focus | [\`src/schematic/page/page.html\`](https://github.com/richc117/legible-cities/blob/main/src/schematic/page/page.html), \`sizeStage\`, \`setBox\`, \`fitVisible\`, \`trackD\`, \`geometry\`, \`setRoutes\` | \`tests/test_fonts.py\`, \`tests/test_colors.py\` |
| Public embed seam and API | [\`docs/ARCHITECTURE.md\`](https://github.com/richc117/legible-cities/blob/main/docs/ARCHITECTURE.md), \`window.__present\` contract; [\`src/schematic/page/present.js\`](https://github.com/richc117/legible-cities/blob/main/src/schematic/page/present.js) | \`tests/test_colors.py\` checks seam methods; browser tests in \`tests/test_fonts.py\` |
| Visual reference data | [Six owner-supplied source SVGs](../references/legible-cities/README.md), particularly CDMX and SF Muni, and [LA Metro REA review](MJOURNEY_REA_LA_METRO_DEEP_DIVE_2026-11-02.md) | Side-by-side browser validation; SVG structural comparison |

### Upstream call chain, without train-time semantics

\`LineGraph\` (stations + edges + **ordered** \`edge.lines\`) → \`render.render()\` → \`Projection.fit\` → \`build_tracks\` / \`slot_offsets\` / \`offset_polyline\` → \`labels.place\` against marker+track obstacles → one SVG with \`#lines\`, \`#stations\`, \`#labels\`, normal \`viewBox\` and \`data-viewbox-nolabels\`.

The original page then uses **the same SVG coordinates** for \`mapXY\`, \`trackD\`, \`geometry\`, \`setBox\`, \`fitVisible\`, and route toggles. M-Journey should reuse these geometry/camera principles, **not** the unrelated \`animate.texts\` train clock, route planner, service-day times, GTFS or passenger controls.

## 2. Oriented label collision is already implemented

**Verified original behavior**

- \`labels.Quad\` stores four rotated corners and a cached axis-aligned envelope. \`collide(a,b,pad)\` first checks envelope overlap, then applies the **separating-axis theorem** to the actual rotated quadrilaterals. This avoids falsely rejecting adjacent 45° labels because their large axis-aligned boxes overlap.
- \`labels.candidates(offset, prefer_rotated)\` tests **six radial distances**, a preference order including 0°, ±45°, ±30° and ±60°, both anchors, plus centered above/below alternatives. Horizontal-track stations prefer rotated candidates instead of overlapping an entire baseline.
- \`labels.place\` sorts stations by descending \`Station.importance\`, which \`render.render\` currently derives from **the number of line labels at that node**. It tests against *hard blockers* (station markers and already placed labels), then *soft blockers* (actual offset track quads). A **second pass** allows last-resort placement over a colored track with an SVG text halo, preferable to silently dropping the label. This is a **greedy**, priority-ordered placement, not a global optimal labelling solver.
- \`render.render\` computes label clearance using the actual widest adjacent track bundle, accounting for per-line width/casing and \`style.line_gap\`; it measures text with \`label_measure\`. A bundled font (Inter or Atkinson Hyperlegible Next) can use glyph advances, whereas the default system font uses an estimated character width.
- \`RenderResult.dropped_labels\` names stations the solver could not place. **Zero dropped labels does not prove label readability at the user's Fit scale**; labels might all exist but render tiny, rotate into an awkward angle, be too dense, or collide with an overlay added after the solver.

**Current M-Journey bypasses and limitations**

- \`bin/mjourney-multiline-proof\` invokes native \`render(..., Style(label_size=15, label_offset=11, ...))\`, so it **already gets** collision-aware positions. Its custom CSS \`#metro #labels text {opacity:0}\` hides most of them and \`.all-labels\` shows all, bypassing controlled progressive disclosure.
- Selected “important” labels are pinned using CSS station IDs (\`eq31\`, etc.), but the static placer **did not know** those stations were narratively important: its priorities come from incident line count. They can be allotted suboptimal positions before CSS chooses what to show.
- \`svg_with_stages\` inserts ten-stage-style headings (five in this subset) **after** the engine has placed station labels. The original label solver does not know about stage headings; collision-free station labels may still collide with the headings.
- M-Journey's average research names are long. The engine's preferred rotations can place labels but do not automatically produce a useful **overview / zoom / detail semantic label hierarchy**.

**Reuse recommendation**

1. Make the **original \`render.render\` + \`labels.place\` the sole authority** for the static overview label positions. Preserve its rotation, text face, halo and collision boxes.
2. Define a **separate source-backed narrative priority** for major decisions, approved handoffs and true shared-station intersections, distinct from transit \`routes_at\`. Evaluate a minimal \`label_priority\` or station \`props\` hook in the renderer rather than external JS label rewrites. Review the priority before implementing; avoid fabricated transit semantics.
3. For stage headers, either reserve a header gutter outside the label-eligible drawing rectangle *before* placement or extend label placement with **explicit immutable external obstacle boxes**. Do not add headings over a solved label field and then compensate with CSS.
4. Use the original font/measurement approach when selecting a face. Preserve colors and station identities. On selected-route focus, measure the names that remain visible, not invisible text.
5. Build a **true label-level-of-detail plan**: key labels at overview, ordinary research names at higher zoom and on selection, detailed evidence in the inspector only. Hiding a label is a display choice; do not silently drop its record.

**Regression tests to reuse or extend:** \`test_geometry.py\` tests 45° labels that slide past each other and dense horizontal runs; \`test_fonts.py\` tests font measurements, rendered marker-label collisions, and fonts loaded before \`fitVisible\` recalculation. Add M-Journey tests for key-label priority, long names, stage-heading clearance, mobile zoom and semantic LOD.

## 3. Shared-line offsets, stroke widths and caps already exist

**Verified original behavior**

- LOOM outputs an **ordered \`lines[]\` array on each edge**. This is **across-edge slot order**, not merely the \`line_order\` argument to the renderer.
- \`build_tracks(graph, proj, style, strokes)\` walks the **optimized polyline of each edge**, computes each line's occupied slot width via \`slot_width\`, derives offsets from \`offsets.slot_offsets\`, and produces **one separate offset geometry per (line, edge)**.
- \`slot_offsets\` includes both the physical width of a line (\`LineStroke.width\`) and its casing (\`LineStroke.casing\`) so that a wide line displaces its neighbors correctly. Ordinary \`style.line_gap\` is a **multiplier** of \`style.line_width\`, not the actual gap in pixels; \`Style.spacing\` is the center-to-center separation. Mixing these two units can over-compress the routes.
- \`offset_polyline\` constructs **miter joins at centerline bends**, deduplicates coincident points and clamps excessive miter spikes (\`MAX_MITRE=4.0\`) at near-reversals. It does not re-run LOOM or replace optimized polylines.
- \`render.render\` emits \`<g id="lines" ... stroke-linecap="round" stroke-linejoin="round">\` **already**. Sharp 45° centerline turns and rounded stroke corners are compatible. The original LA Metro map genuinely contains angular bends.
- \`render.render\` supports **line-specific widths, casings and dash patterns** via \`LineStroke\`. Its original page reads actual stroke width/dash from drawn groups for visual controls. Its \`colors\` argument keeps stable literal hex line colors; the dark/light theme only changes map furniture.

**Critical M-Journey distinction**

- \`line_order=[...]\` is the **global painting order and preferred Linear-row order**. The per-edge \`edge.lines\` sequence from LOOM is the actual **track offset order**. Changing only \`line_order\` does **not** solve lane crossings or ordering through shared corridors.
- Our 23-station graph has six lines but the two primary pathway colors share many segments. If their individual strokes appear merged in a screenshot, first inspect **per-edge \`lines[]\` order**, \`Style(line_width=11,line_gap=1.45)\`, actual SVG group opacity, and zoom. Do not immediately hand-create new offset paths or widen all routes.
- In the screenshot one route filter was active, so unrelated lines were displayed at **7.5% opacity**. That low contrast makes the system look like a single faint trunk even if the underlying tracks are correctly separated. Diagnose the focus state before blaming LOOM.

**Reuse recommendation**

- Preserve **exact native LOOM polylines and across-edge \`lines[]\` order**. Use \`render.build_tracks\` and \`offsets.slot_offsets\` rather than coding offsets in the standalone HTML.
- Tune \`line_width\`, \`line_gap\`, \`LineStroke\` and line colors as a **single design system**, with matching station radii and label clearance. A thicker line with an unchanged marker size is not harmless.
- Audit whether two tracks are genuinely distinct at the **rendered Fit scale**, not only at SVG-unit scale. Test shared 2/3/4-route corridors and junctions at 1440px and mobile.
- Don't smooth LOOM centerlines just to reduce the visual impression of corners. SVG already uses round caps/joins. First count gratuitous bends and review line order; any radius treatment requires independent geometry, offsets, endpoint and source-integrity QA.
- Preserve primary semantic path highlighting separate from **organizational workstream** filters. A workstream tag is not an automatically traversable transit line.

**Original tests to reuse:** \`tests/test_offsets.py\`, \`tests/test_geometry.py\`, \`tests/test_line_order.py\`. The width/casing test explicitly asserts the slot positions -9.1 and +5.6 for a narrow/wide two-line example, and that ordinary-width maps retain exactly their previous offsets.

## 4. Track IDs are stable **within a stored layout**, not globally immutable

This distinction is vital to avoid a false claim of source-integrity guarantees.

**Original track contract**

- \`render.TrackPath\` represents one line on one optimized edge. \`RenderResult.tracks\` is keyed by \`(line.label, edge.src, edge.dst)\`, with \`result.track(label, src, dst)\` also checking reverse direction.
- \`build_tracks\` assigns an SVG \`id\` similar to \`t<edge-index>_<sanitized-line-label>\`, with a deterministic suffix if two labels sanitize to the same ID. \`render\` exposes the same internals via \`#lines g.line[data-line]\` and \`path[id][data-src][data-dst]\`.
- In the **same stored, unmodified optimized layout**, these identities let the original browser synchronize map tracks, geographic twin polylines, line focus and morphs. This solves an important *intra-layout* identity problem.
- BUT LOOM-generated **node IDs can be pointer-like, and graph edge ordering can change on a new solver run**. The \`t<edge-index>\` IDs are **not persistent research IDs**, nor a guarantee of stable IDs across independent LOOM runs or different inputs.
- \`Node.station_id\` survives as an externally meaningful station key. In our M-Journey context that must remain \`eq##\`, while connection provenance uses canonical \`sourceEdgeIds\`. Any geometry-only junction LOOM inserts is **not** an authored research station.

**Current M-Journey state**

- The current adapter successfully maps \`#stations [data-node]\` back to \`data-station-id\` for label selection, but other front-end logic still depends on \`data-line\` or transformed internal \`data-node\`.
- The demo's station selection and pathway list should use **canonical \`station_id\` and \`sourceEdgeIds\`**, not re-solve-dependent \`TrackPath.element_id\` or graph-node pointers.
- If a source connection is subdivided by a geometry junction into several visual edges, map all fragments back to its research provenance and distinguish cosmetic junctions from actual approved handoffs.
- The original renderer emits paths using its normalized internal labels and endpoint IDs. It **does not automatically emit \`data-source-edge-id\`**; any new marker must be designed as an extension or explicit companion lookup indexed against an immutable stored layout. Do not assert that today's markup has already solved cross-run source identity.

**Recommended contract for multi-view M-Journey**

\`\`\`text
Canonical source station: eq31
Canonical source relationship: edge44
Logical route membership: ae_epc_mediated
Stored layout revision: input+settings+LOOM-version fingerprint
Render track: t7_A_E_EPC_mediated   (local to this exact layout)
Mapping: {layout revision, render track} -> {source edge ID(s), route ID, canonical endpoints}
\`\`\`

The displayed route/pathway, evidence inspector, chapter transitions and zoomed labels must resolve through that mapping. **Never change the canonical source to match a visually convenient LOOM node ID.**

**Tests:** all track IDs unique within one SVG; track IDs and source relationship mappings repeatable from **the same stored layout**; equivalent station-line adjacency across solver runs; cross-view labels/selection refer to the same \`eq##\` stations; no inferred interchange at mere graphical crossings.

## 5. Content-aware camera/framing is already implemented, but not in the static \`render\` call

**Original static SVG**

- \`render.render\` computes its \`Projection.fit\` using **uniform scale in x and y**, preserving true 45° geometry. This is an SVG-coordinate projection, not a responsive camera fit.
- It calculates **network-only** bounds (tracks and markers) and **network + label** bounds separately. It exposes the latter as SVG \`viewBox\`, and the former as \`data-viewbox-nolabels\`. The no-label box is inert in a standalone SVG until the viewer deliberately uses it.
- Labelled canvas bounds include placements, allowing long diagonal names to extend past the track geometry without clipping.

**Original browser page**

- \`fitVisible()\` measures **actual visible SVG elements** using \`getBBox()\`: shown line groups, station dots and labels. It computes both map and Linear subset bounds, and optionally the geographic state when present, then pads by **3% of the larger dimension**.
- \`setBox(m)\` is the **single owner** of writes to the SVG \`viewBox\`, combining: full bounds, label-off tight bounds, route subset bounds, map↔Linear interpolation and optional frame aspect/safe margins. The source explicitly describes a previous bug caused by *multiple writers fighting over the viewBox*.
- \`setRoutes(keep)\` manages actual line visibility; when a subset is hidden, it runs \`fitVisible()\`. When all routes return, it clears subset bounds. **Single-route focus is a geometry/camera transition**, not only an opacity change.
- \`sizeStage()\` keeps a readable minimum width on small devices and allows horizontal panning, instead of compressing a high-aspect network into a tiny phone-width diagram.
- \`fitVisible()\` handles the case where a bundled font loads late; \`settle()\` waits for \`document.fonts\` and refits, so the bounding boxes reflect the real face.
- The browser's \`geometry(m,sf,g)\` changes tracks, station dots and label positions together. \`trackD\` uses each stored polyline's **own vertex count** to interpolate into Linear/Geographic coordinates; it does not rebuild arbitrary connections from scratch.

**Current M-Journey bypass**

- \`bin/mjourney-multiline-proof\` saves a static \`home\` from \`svg.viewBox.baseVal\`. Its \`fit()\` simply sets \`vb.x/y/width/height\` back to home. A single selected path remains a small streak inside the all-line canvas.
- Focus toggles CSS opacity: \`#metro.focus #lines g.line:not(.selected-line){opacity:.075}\`. The unrelated paths **remain present** and can be included in bounding measurements. The original focus *hides* other routes and recomputes subset framing.
- It uses a separate custom pan/wheel implementation, while the original page has its own \`setBox\` owner. Directly reusing full \`page.html\` is **not** the right answer: it contains trains, time, stringline, GTFS routing, and unrelated controls.
- The appended stage headings are outside the original source renderer's label-layout process. Any selected route's camera must consider whether headings are fixed to the viewport or part of the SVG, and whether hidden/secondary headings should contribute to Fit.

**Safe adaptation design**

Create a **minimal journey-specific camera/view controller** inspired by \`fitVisible\` and \`setBox\`, without importing passenger/timetable code:

1. Maintain one \`camera\` model for \`all\`, selected route subset, overview labels, detail labels, and (when genuinely implemented) Linear rows. One function alone is allowed to write the \`viewBox\`.
2. Compute the visible set from **source-backed route memberships**. Route focus should fully hide unrelated tracks and irrelevant labels in the route-only mode, with an explicit option for contextual de-emphasis when the user wants broader system context; don't conflate the two.
3. Measure rendered visible SVG paths/markers/**labels** plus stage headers deliberately with \`getBBox()\`. Do not include \`display:none\` or decorative text in the visible bounds; explicitly handle empty state.
4. Compute a target bounding box with intentional margins, aspect-ratio expansion rather than cropping, and optional interpolation between prior/current camera targets. Store a committed home Fit; recompute it only on source/viewport changes, not on every animation frame.
5. Wait until fonts are ready before the final Fit. Refit after font changes and resizing. Preserve the user's zoom intent where appropriate rather than unexpectedly resetting selection.
6. On mobile, use a **legible-width/pannable stage** or semantic subview; do not shrink ten stages and 67 moment labels to 390px.
7. Reserve space for portfolio-consistent controls inside the map. Keep controls out of SVG measurement and use the portfolio's \`.mj-controls\` design grammar.

This camera is still **new integration code**, but it replaces the current duplicate fixed viewBox/zoom/focus hacks with one tested controller. It is not wholesale reuse of the train viewer.

## 6. Work to delete, retain or extend

| Current implementation | Assessment | Action |
| --- | --- | --- |
| Native \`render(...)\` call | Correct foundation; already uses placements and offsets | **Keep** |
| Native \`build_tracks\` / \`slot_offsets\` / \`offset_polyline\` | Already solves offset geometry | **Reuse; no custom JS re-offsetting** |
| Native \`render.dropped_labels\` audit | Useful but incomplete | **Keep, add viewport legibility/collision tests** |
| \`#metro #labels text {opacity:0}\` plus hardcoded \`eq##\` labels | Display LOD without layout priority | **Replace with source-backed overview tiers and placement-aware priority** |
| Stage headings inserted after rendering | Bypass static label obstacles | **Reserve layout zone or extend solver obstacles; avoid collisions** |
| \`focus(name)\` only toggles opacity | Fails original focus/framing behavior | **Replace with actual visible route subset + content-aware Fit** |
| \`fit()\` restores fixed original \`home\` box | Ignores current line/labels/inspector, causes tiny diagram | **Replace with a single viewBox controller** |
| JS zoom/pan independent from Fit | Risks competing camera updates | **Integrate into single controller, retain user-initiated zoom** |
| Internal \`data-node\`/track ID used as permanent identity | Not source-stable across new LOOM runs | **Bridge to canonical station and source-edge IDs** |
| \`line_order\` used as if it solved per-edge line order | Semantically wrong | **Keep global paint order separate from LOOM \`edge.lines[]\` order** |
| Timetable/GTFS UI in original \`page.html\` | Not relevant to customer research | **Do not import** |
| Actual 67-moment/87-relationship graph and two named pathway alternatives | Research source of truth | **Preserve; unrelated to renderer audit** |

## 7. Proposed implementation sequence and acceptance gates

**Do this after the other agent's coordinate/topology work has stabilized the geometry baseline.** Avoid parallel edits to the LOOM pipeline or source route classifications.

### Phase A: Preserve baseline and prove existing renderer functionality

- Freeze exact native LOOM intermediate GeoJSON and layout ID. Run original tests \`test_geometry.py\`, \`test_offsets.py\`, \`test_line_order.py\`, \`test_fonts.py\`, \`test_colors.py\` where available and dependencies permit.
- For the 23-station source-safe graph, inspect \`RenderResult.tracks\`, \`RenderResult.dropped_labels\`, \`result.svg\` \`#lines g.line\`, actual \`edge.lines\` ordering, \`data-viewbox-nolabels\`, and \`viewBox\`.
- Compare default line gaps and rendered shared-stroke separability on CDMX and SF Muni, using [source SVG files](../references/legible-cities/README.md). No invention of new data edges.

### Phase B: Label priority and reserved stage gutters

- Write an acceptance example with a long horizontal run, an important junction, a 45° branch, ten stage headings, and long research names.
- Confirm original oriented collision results; then introduce the minimum necessary prioritization/external obstacles hook with targeted tests. No CSS positioning patches.
- At 1440×900 and 390×844, **key labels must not collide visibly** with another visible name, track, or stage heading. Hidden labels do not count as success.

### Phase C: One camera and map visibility semantics

- Replace \`focus\` and fixed \`fit\` with visible-content bounds and a single camera writer.
- Test All lines, single A&E/EPC, direct-customer, two selected lines together, and an activity-branch-only case. Measure actual bbox of displayed content after fonts settle.
- Verify labels-on vs labels-off bounds change deliberately, without clipping or excessive whitespace. Route focus must not leave a tiny network in the corner. Zoom/pan/fullscreen remain functional on desktop and mobile.
- Do not treat a hidden line as a route transfer or an erased source relationship; selection is purely a view filter.

### Phase D: System and carousel integration

- Inspect the **latest portfolio** \`AGENTS.md\` and source \`.mj-controls\` before matching control placement. Keep stage labels, map and narrative copy in their approved roles.
- Integrate into the six-chapter narrative **only after** the map network itself is source-backed and visually approved. No train/time widgets, no imaginary Spatial view.
- Research tooltip/inspector must always resolve \`eq##\` and \`edge##\` keys. Keep developer counts, solver status, source-provenance claims and evidence logs **out of public decorative copy**.

### Non-negotiable checks

| Gate | Minimum proof |
| --- | --- |
| Collision | Original SAT-based label boxes + stage-header obstacles; no visible key-label overlap at intended viewport |
| Lane fidelity | Native ordered \`edge.lines[]\`; shared corridors use the exact original offset engine |
| Source IDs | 67/87 canonical records unchanged; each visible stop and connection traceable; geometry-only nodes never become customer stations |
| Track IDs | IDs unique within stored layout; cross-layout identity uses research key/provenance, not \`t<edge-index>\` |
| Camera | One viewBox owner; content-based subset Fit for one or multiple lines and label states |
| Mobile | Useful readable and pannable network, not a 67-label postage stamp |
| Renderer | No duplicate offset/label engine, no timetable code, consistent caps/joins and color source |
| CI + QA | Exact-head unit tests, browser interaction tests and desktop/mobile screenshots; **visual approval separately required** |

## 8. Decision and boundaries

**High confidence, directly observed in upstream source:** native oriented collision, label candidate solver, per-edge shared-line slots and caps, SVG IDs within one layout, distinct network/no-label bounds, and original browser's content-aware route Fit.

**Proposed integration changes, not yet proven implemented:** a source-aware label priority hook, stage-header collision zone, extraction/adaptation of camera logic into a journey-only controller, source-to-render track identity mapping, and semantic label LOD.

**Not solved by these mechanisms:** defining valid transit-like line families from seven workstreams, inventing acceptable handoffs, enforcing all ten source-authored stages, or deciding whether customer research supports a broader multi-hub shape.

**Recommendation:** Make the renderer/camera integration the next focused engineering slice after geometry and semantic mapping work has stabilized. **Do not write new collision, offset or track geometry engines.** A new journey-only view controller is justified; the original time-based page is not.
