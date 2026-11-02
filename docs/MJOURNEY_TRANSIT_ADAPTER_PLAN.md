# M-Journey adapter for the forked Legible Cities renderer

**Status:** proposed architecture and acceptance gates; no renderer or adapter implementation has been merged. Owner direction recorded 2026-11-02. **This fork is GPL-3.0**, derived from [richc117/legible-cities](https://github.com/richc117/legible-cities); preserve upstream attribution, existing LICENSE and notices. Do not copy this source wholesale into the separate unlicensed portfolio bundle without a licensing assessment.

## Decision

**Make this fork the one transit renderer.** The portfolio currently has a separate hand-coded graph + colored-guide renderer in `sss2808/P/src/portfolio.html`. It is not visually or semantically adequate and must not become the M-Journey product's permanent second map engine. Replace its map canvas with an instance of the **fork's original Legible Cities renderer**, preserving its transit tracks, station markers, label algorithm, schematic/linear morphs, line selection and compact controls.

The portfolio owns case copy, six chapter navigation, Back/Skip navigation and presentation context. The fork owns map geometry, animation, station labels, route toggles, selection, camera, map styles and accessible details. The product later supplies its canonical graph and interaction callbacks to that one viewer. **Do not recreate a second transit viewer in the portfolio.**

## Source exploration already completed

- `docs/ARCHITECTURE.md`: one renderer drives the site, essay, export and desktop; browser driver `window.__present`. Pipeline: GTFS -> LOOM `gtfs2graph` -> `topo` -> `loom` -> `octi` -> render -> animate -> write. **M-Journey has no GTFS**; bypass feed and timetable ingestion.
- `src/schematic/linegraph.py`: public model is GeoJSON FeatureCollection: station `Point` features with `properties.id/station_id/station_label`; connection `LineString` features with `properties.from/to/lines:[{id,label,color}]`. Edge `lines[]` express actual line occupancy.
- `src/schematic/render.py` / `offsets.py`: exact source for station and interchange markers, line offsets, line casing/strokes and route colors.
- `src/schematic/labels.py`: line- and collision-aware label candidates, oriented quads and priority. Preserve the original engine first and improve collisions after visual review.
- `src/schematic/linear.py`: a line's connectivity drives its spine and side branches; it does **not** automatically make a sequence of arbitrary same-layer points a real traversable route.
- `src/schematic/animate.py`: `build(render, graph, trips, date, geo=None, ...)` already constructs `linear` and `routing` from a `LineGraph`; `trips=[]` is a useful **testable starting option**, not yet verified in a browser. `texts` serializes the self-contained viewer. Remove/hide timetable, time mode, speed/play clock if there are no valid trips.
- `src/schematic/page/page.html`: existing compact icon view switcher and collapsible Lines/Labels controls, plus `window.__present.showView/setView/setRoutes/setLabels/setFrame`. `present.js` implements the source transformations. Preserve these components and gestures rather than rebuild them with portfolio buttons.

## 1. Data interface and fidelity

Input is a **privacy-reviewed, source-traced** JSON envelope, not an invented GTFS feed:

```ts
type MJourneyTransitInput = {
  journeyId: string;
  stages: { id:string; order:number; name:string; shortName:string; phaseId?:string }[];
  grouping: { dimensionId:string; label:string;
    values: { id:string; name:string; color:string; order:number }[] };
  stations: { id:string; name:string; stageId:string;
    groupId:string; order:number; evidenceRefPresent:boolean }[];
  connections: { id:string; fromId:string; toId:string;
    kind:string; routeId:string; sourceRefPresent:boolean }[];
  transit: {
    lines: { id:string; label:string; groupValueId:string; color:string;
      stationIds:string[]; validatedEdgeIds:string[] }[];
    interchangeMoments: { momentId:string; involvedLineIds:string[]; sourceEdgeIds:string[] }[];
    connectionDisposition: { connectionId:string;
      display:'track'|'interchange'|'detail-only'|'lifecycle-return' }[];
  };
}
```

This is a **proposed adapter contract**, not a schema to impose on M-Journey's existing CSVs. Keep stage/layer/moment/edge IDs from the source; never treat LineGraph's geometry-only helper nodes as researched journey moments. The stage dimension is **authored semantic time/order**, not physical geography or measured duration.

**Critical distinction:** The canonical connection graph and the transit network projection are **different views of the same research**, with explicit provenance. Not every graph edge is transit track. In the sanitized equipment example, 67 moments/87 connections have **23 same-layer edges and 64 cross-layer edges**; 76 edges have kind `sequence`, only three are `handoff`, three `dependency`, two `branch`, two `convergence`, one `lifecycle_return`. Turning all 64 cross-layer edges into visible interchanges produces a false, unusable metro network. **Every transit line must have an approved ordered stop sequence**, and only a source-validated transfer is drawn as an interchange. Other dependencies remain in the station detail and/or purpose-built analysis mode.

**Configurable line identity:** Typically one line per current authored layer (workstreams for the equipment demo). If another journey authors its layers as channels, line identities represent the named channels. Additional user-selected groupings may be supported later only when source metadata contains the dimension and the corresponding line topology is validated. Do not silently infer a traversable line from all moments sharing a category.

**Stage labels:** Use the **real ten operational stage short names** in the equipment data rather than meaningless `01`–`10`; reveal full stage labels by hover/focus and accessible name. Preserve stage-column boundaries in both Schematic and Linear views, but let them remain quiet relative to the routes.

**Fork reference fixtures:**
- sanitized equipment journey `sss2808/P/src/portfolio.html` `mjSample` (67 moments, 87 edges; 22-station early preview and a 67-station full fixture);
- exact authoring semantics in `sss2808/m-journey/src/app/journeys/gsa-hardware/stages.json`, `lanes.json`, `Connections.csv`, `manifest.json`;
- no second "standard journey" fixture until a valid separate source has been identified, sanitized and reviewed.

## 2. Source-compatible implementation path

1. **Create adapter and tests in this GPL fork** (e.g. `src/schematic/mjourney.py`, `tests/test_mjourney.py`) that validate stable station IDs, source stages, configured grouping, directed edges, transfer dispositions and record provenance. Generate a `LineGraph` GeoJSON, with `station_id` matching the sanitized canonical moment ID and `Line` carrying the verified current grouping/route. Avoid GTFS and any invented trip timestamps.
2. **Build a 20–30 station editorial fixture first**, then the full 67. Use exact source labels, approved route line membership and meaningful real junctions; no unlabeled chosen stops or fake crossovers. Validate no orphaned nodes and no transfer absent from author-approved graph provenance. Preserve all other canonical connections in inspector data, not as 87 drawn tracks.
3. **Adapt geometry constraints** so Schematic preserves approximate left-to-right operational stage progression while `octi` optimizes legibility. LOOM input coordinates may be seeded from `stage × grouping`, but **LOOM's solution is not guaranteed to preserve stage columns**. Explicitly validate and repair stage-domain constraints after layout (or implement a stage-constrained geometry stage in this fork). Keep track order and branch topology stable. Retain upstream line casing, station rendering and label implementation.
4. **Generate two views with the existing renderer.** Schematic = route map; Linear = one row per route with true branches, preserving stage order. If two requirements conflict, flag an overconstrained input rather than fabricate track connectivity. Do not create a separate portfolio SVG/JS engine.
5. **No-schedule mode:** empty trips, no clock, speed, train count or Time view, with a reader-driven chapter control exposed by the portfolio. Use the existing `window.__present` interface for view and route focus. Inspect page assumptions for empty paths before treating `animate.build(..., trips=[])` as complete.
6. **Interactions:** route chips, Labels, Schematic/Linear, keyboard station selection, tooltip/title, source context callbacks, responsive camera, reduced-motion snap, clear visual focus, and optional selected-moment inspector. Keep main portfolio Back link outside the inner viewer and accessible; avoid an inner “Back to Atlas” dead link.
7. **Style:** keep original fork geometry, motion/labels, high-contrast route color, marker hierarchy and compact UI as the baseline. Adapt minimally to six portfolio palettes and M-Journey semantics *after* seeing the unmodified appearance first.
8. **Integration:** emit a versioned standalone viewer HTML and its provenance JSON. Embed as a child page/iframe from the portfolio, with a small, documented `postMessage` protocol **only** if required for chapters, selection and chapter skip. Match `origin`, validate message types, respect isolated GPL notices and privacy. Do not weave GPL viewer source into the unlicensed portfolio HTML without an explicit licensing decision. Later replace the M-Journey primary Viewer surface behind a feature flag, keeping System/Editor, imports, analysis, evidence and controls unchanged.

## 3. Six-chapter portfolio choreography

1. **Network:** stations scattered on a clear, empty field. No grid, no spaghetti edges.
2. **Structure:** vertical + horizontal guide grid **draws in** while station positions remain unchanged; **colored Legible Cities-style routes** develop and attach to the stations, with real source-validated transfers. **Never reveal all 87 edges as thin crisscrossing lines.**
3. **Journey:** the same station IDs transform into the readable schematic, organized with authored stage-column headings and line/layer names. One renderer throughout.
4. **Perspectives:** compact original icon view switcher animates Schematic ↔ Linear; line chips and Labels live in the fork's collapsible controls. Data/insight-focused alternate modes are introduced **contextually**, not as a large external button strip.
5. **Personas/Present:** guided presentation along actual verified route choices; source-valid role/persona identification only. Play/Stop/Step controls replace GTFS clocks. The portfolio owner may choose “Present” as chapter title later.
6. **Evidence:** selection opens a compact station detail with research-reference metadata. Cross-journey Insights value is explained in the external case narrative, never fabricated from a single 67-station dataset.

## 4. Separate portfolio navigation and shell contract

The outer portfolio controls remain its own case history and navigation. Provide **Skip visualization** which jumps past the sticky `660svh` section into the following reading section; keep the Back button above the pinned map on laptop/mobile. Remove redundant “M-Journey” logo from the exhibit, numeric stage tokens, evidence-coverage QA slogans, and duplicate Schematic/Linear/Workstreams button strips. The map itself contains the real transit controls, kept readable at the 950×520 carousel view and responsive container sizes.

## 5. Visual and functional acceptance

- **Fidelity:** an author reviewing screenshot/video would recognize Legible Cities' original renderer, line weight, transit marker/interchange hierarchy, labels, compact segmented view switch, route focus and smooth spatial morphs. The first POC should not ship with hand-drawn approximations.
- **Semantics:** zero fabricated station/transfer/line connectivity; actual provenance audit for every displayed route and interchange; 100% original stage, layer, moment, source-edge and evidence IDs addressable somewhere in the M-Journey product, even if only a subset appears as transit tracks.
- **Readability:** no illegible station names or false interchanges; browser-measured label/track/marker collisions; readable size without panning on desktop; genuine compact/mobile alternative. Test all six palettes and reduced motion.
- **Navigation:** skip from first to final post-carousel section, preserved Back, direct chapter jumps, no scrolling to recover controls, station inspector not shrinking map.
- **Motion:** network/structure nodes fixed, valid route drawing onto them; seamless map-to-linear view morph from the original fork renderer; interruption/reverse and selected station identity stable.
- **Scope:** no private quotes, IDs, Dovetail source content or fake metrics in public portfolio. Cross-map Insights is a distinct product capability, not purportedly computed by the single-map demo.
- **CI:** pass fork unit tests including custom adapter/linegraph validation, product fixture tests, and portfolio source/build/inventory/exact-head Chrome screenshot checks **before** merge or claim of release.

## 6. Licensing and release

Forking a GPL repository **does not remove its copyleft**. Direct use/modification of the fork is possible under GPL-3.0 terms, including preservation of licensing and notices and applicable source availability on conveyance. Running the modified Python generator locally and publishing the generated SVG is different from bundling the GPL browser application. A separate embedded viewer can reduce coupling but is **not automatically an exemption** from license obligations. Verify third-party LOOM and font licenses and perform review before making the standalone page public or combining it with the currently `UNLICENSED` portfolio. No claim that the license is incompatible in all circumstances: it depends on how source is combined and distributed.

## 7. Immediate implementation milestones

- **Fork P0:** reproduce original LA Metro map controls and view morph in a local browser, unchanged.
- **Fork P1:** source-accurate M-Journey `LineGraph` adapter + stage labels + provenance fixture, with no timetable.
- **Fork P2:** real source-validated interchanges and constrained stage schematic in the original renderer, passing labels and mobile QA.
- **Portfolio P3:** integrate the fork viewer in the existing six-chapter portfolio shell; delete/archive the old hybrid renderer's rendered layer/edge code **after** parity, not before.
- **Product P4:** only after portfolio owner approves the two-view experience, design the M-Journey feature-flagged integration and legacy editor compatibility. No application default switch now.

**Do not** treat current portfolio V87's independently hand-coded, spaghetti-edged source view as the reference for the new viewer. It is a rejected prototype kept solely for history and temporary navigation.
