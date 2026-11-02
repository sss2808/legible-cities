# M-Journey V8 architecture and cartography plan

**Status:** planning only, 2026-11-02. This document is prepared on a separate documentation branch from V7 draft PR #5. It is **not** a code change, sign-off, merge, or deployment. Its purpose is to integrate evidence from upstream Legible Cities, the successful coordinate audit in PR #6, and the original REA / six-map reference research before other agents implement V8.

## Source evidence reviewed

7. [Draft PR #7](https://github.com/sss2808/legible-cities/pull/7) and [LOOM topology source-integrity audit](https://github.com/sss2808/legible-cities/blob/docs/loom-topology-source-integrity-2026-11-02/docs/LOOM_TOPOLOGY_NONDETERMINISM_SOURCE_INTEGRITY_2026-11-02.md), plus [PR #6 follow-up comment](https://github.com/sss2808/legible-cities/pull/6#issuecomment-6590200990). PR #7 is a **documentation-only**, independent branch based on PR #6, not an implementation already integrated into V7 or V8.
8. [Upstream CONTRIBUTING.md](https://github.com/richc117/legible-cities/blob/main/CONTRIBUTING.md), particularly the actual environment and skip-prone CI testing scope.
9. Upstream staged examples: [02_build_line_graph.ipynb](https://github.com/richc117/legible-cities/blob/main/notebooks/02_build_line_graph.ipynb), [03_schematize.ipynb](https://github.com/richc117/legible-cities/blob/main/notebooks/03_schematize.ipynb) and [04_render_svg.ipynb](https://github.com/richc117/legible-cities/blob/main/notebooks/04_render_svg.ipynb). These are *executable illustrative examples* without stored cell outputs in the reviewed files; their printed values must not be invented or reported as V8 results.
10. [Upstream LOOM issue #44](https://github.com/ad-freiburg/loom/issues/44) and the [maintainer confirmation](https://github.com/ad-freiburg/loom/issues/44#issuecomment-5681272160). The upstream report observed semantic-topology variation for macOS native runs; eight Linux control runs were stable. Neither observation proves repeatability on every platform.


1. [Upstream Legible Cities architecture](https://github.com/richc117/legible-cities/blob/main/docs/ARCHITECTURE.md), including the layout store, nondeterminism, CRS, render/labels/offsets, viewer controls, and export rules. Fetched upstream blob `a27fa09aa73cf46694572e358be084121d3b5183` on 2026-11-02.
2. [Exact-head Actions run 41537372455](https://github.com/sss2808/legible-cities/actions/runs/41537372455), with both source-seed and real native C++ LOOM jobs passing on PR #6 head `8e3fce120dbdb7b392813b354051995c9f5c770b`. The native log asserts accepted optimized geometry rather than an unrecognized fallback.
3. [Specific PR #4 comment 6590112859](https://github.com/sss2808/legible-cities/pull/4#issuecomment-6590112859), which summarizes the exact coordinate correction, its residual constraints, and detailed native audit.
4. [Draft PR #6](https://github.com/sss2808/legible-cities/pull/6), particularly `src/schematic/mjourney_projection.py`, `tests/test_mjourney_projection.py`, and the 18/23-station proof changes.
5. [V7 draft PR #5](https://github.com/sss2808/legible-cities/pull/5) and [V7 review](https://github.com/sss2808/legible-cities/blob/feature/mjourney-system-network-v7/docs/mjourney-system-v7-review.md): 59 source moments / 68 directed source edges projected over ten stages with 11 visual route identities; the latest V7 native optimizer was previously rejected in favor of seed geometry. Source and Chromium interaction checks are **not** geometric approval.
6. [LA Metro REA deep dive](https://github.com/sss2808/legible-cities/blob/feature/mjourney-rea-multiline-proof/docs/MJOURNEY_REA_LA_METRO_DEEP_DIVE_2026-11-02.md), [six-network shape audit](https://github.com/sss2808/legible-cities/blob/feature/mjourney-rea-multiline-proof/docs/MJOURNEY_ATLAS_SHAPE_REFERENCE_AUDIT_2026-11-02.md) and [original reference SVG index](https://github.com/sss2808/legible-cities/tree/feature/mjourney-rea-multiline-proof/references/legible-cities). These provide layout/interaction examples, not permission to infer customer transfers or copy the maps as M-Journey source data.

**Important scope distinction:** PR #6 is green for the **23-station, 25-source-edge, six-line, five-stage** proof. It does not validate the **59-station, 68-edge, 11-route, ten-stage** V7 composition. V7 still contains `_LOCAL_LONGITUDE_SCALE=cos(48°)`, hand-written `to_solver/from_solver`, and its own `poly_review` in `bin/mjourney-system-network`. V8 must integrate the PR #6 solution deliberately and rerun native QA at V8's actual graph size.

## Architectural decisions

### A. Three independent forms of correctness

Maintain separate release gates and audit fields:

- **Source/semantic integrity:** canonical research moment IDs, ordered stages, authored directed relationships, source-layer membership and validated handoffs; no manufactured stations, customer paths, roles, dates, transfer semantics or lifecycle loops.
- **Optimization/projection integrity:** exact metric-to-WGS84 bridge, preserved line IDs and station IDs, no lost/gained per-line adjacency, stable stage ordering, and verified weighted octilinearity on optimized polylines. A workflow may pass while native geometry is rejected only if the audit reports that fact explicitly; it is **not** native-geometry approval.
- **Cartographic and viewer quality:** intentional line continuity, low redundant-bend count, clean co-route offsets, readable labels and stage headings, appropriate aspect and whitespace, useful multi-route filtering, predictable Fit/zoom/fullscreen, and accessible Schematic/Linear views. Native solver acceptance is necessary but insufficient.

No success label may collapse these three gates into one green check.

### B. Adopt PR #6's exact metric bridge, not a new approximation

- Reuse `schematic.mjourney_projection.to_solver_point` and `from_solver_point` in the ten-stage script after an explicit compare/cherry-pick/rebase plan. Do not fork their equations in a third file.
- The input axes are **synthetic ordinal display coordinates** only. Neither +8° / +48° nor returned GeoJSON claims a physical research location.
- Original `schematic.crs.to_mercator` / `to_wgs84` are the reversible authority. Maintain every solver-added intermediate polyline vertex when projecting back. Do not reconstruct solver edges with UI-level elbows.
- Adopt `schematic.render.octilinearity` with PR #6's accepted threshold of **at least 99.5% of line length within ±1°** of octilinear bearings. Preserve the raw metric and avoid classifying tiny rounding stubs by unweighted per-segment count.
- Keep existing PR #6's five coordinate/regression tests. Add a ten-stage end-to-end regression asserting finite coordinates, metric axis consistency, station/edge/line identity, exact vertex roundtrip, and native-result disposition.
- Verify a real V8 native run. The 99.97897% result is a historical measurement of the 23-station proof, **not** a target that V8 has already achieved.

### C. Freeze and archive a computed layout as an immutable artifact

Upstream `ARCHITECTURE.md` explicitly warns that LOOM `topo` is nondeterministic even on the same input; raw stage JSON also contains unstable pointer-like node IDs. A successful optimized layout is a stored artifact, **not** a recipe guaranteed to recreate its exact topology.

- Define a content-addressed V8 `layout_id` from source-fixture content digest, selected station/source-edge IDs, explicit route membership, stage/layer encoding, adapter version, geometry seed configuration, exact coordinate-bridge version, engine/LOOM commit, backend, and every enabled solver stage/argument. Keep run time/date out of the content hash; record them separately as metadata.
- Write every stage to a staging directory and publish a complete accepted set atomically after all gates pass. No implicit re-run on preview or export. A rejected candidate is archived as diagnostic output, not placed in the accepted-layout store.
- Preserve manifest + `seed.graph.json`, `solver.input.geojson`, `loom.geojson`, `octi.geojson`, `render.svg`, `viewer.html`, `integrity.audit.json`, and screenshots/label metrics. Include sha256 for each immutable file and the source commit SHA.
- If `topo` is introduced in a research-only experiment, keep its input and output and run the stricter source-station and line membership comparison. For the active M-Journey adapter, **omit `topo` by default**: upstream notes that it may merge stops, and the M-Journey authorization model currently disallows source-adjacency rewriting.
- Never assert equivalence using LOOM ephemeral node IDs or raw JSON hashes across runs. Compare normalized station IDs, authored edge endpoints/directions, line labels and per-station line memberships, geometry-only junctions, and, for replay, the stored authoritative stage file.
- Pin the exact native LOOM commit with `SCHEMATIC_LOOM_COMMIT` in the run manifest, not only a moving clone URL; record binary/backend and flags.

**Proposed manifest fields:** `layout_id, source_fixture_sha256, source_git_sha, displayed_moment_ids, displayed_source_edge_ids, source_directed_pairs, route_memberships, source_layer_ids, stage_order, synthetic_crs, bridge_commit, loom_commit, loom_backend, solver_stages_and_flags, intermediate_sha256, station_identity, line_identity, per_line_adjacency, directed_edge_provenance, weighted_octilinearity, stage_integrity, solver_used, render_label_metrics, screenshot_metadata, review_status`.

### D. Treat the adapter as a semantic contract, not a transit-data converter

- The complete research fixture remains **67 moments, 87 authored relations, ten stages, seven authored layers**. V7's display is an intentional **59-moment / 68-edge projection**, not a replacement for the canonical data.
- Keep distinct: source moments, authored directed relationships, route membership, candidate customer alternative, short activity chain, research layer, branch/convergence, dependency and feedback/lifecycle relation.
- The two named A&E/EPC-mediated versus direct-customer-led selection alternatives remain **candidate source-backed paths**, not independently validated customer personas. Nine other visual chains are activity routes, not automatically nine more journey scenarios. `layer-0` is Journey sequence, not a department.
- Do not turn non-traversable dependencies, annotated feedback, lifecycle returns, or crossings into rail-like transfers. Mark only source-approved handoffs as such, with stable source edge IDs.
- Add a semantic projection manifest checked before solver invocation. If a rendered station/edge cannot be traced back to the author-approved fixture, fail.
- Defer any proposal to display all 87 links as transit tracks until each link has an approved visualization rule; preserve the ability to show research evidence or dependencies as separate selectable overlays.

### E. Preserve one geometry and a coherent viewer state

The upstream package has a **single renderer** and a page-controller seam `window.__present`; `setView`, `setRoutes`, `setLabels`, `setFrame`, `state`, and `settle` coordinate views, labels, route membership and camera. For the sanitized M-Journey standalone, borrow this **state/control architecture**, not its GTFS, geographic, timetable, train, or playback semantics.

- Specify one data source and one map-controller state: `arrangement=schematic|linear`, `selectedRouteIds: Set`, `selectedLayerId`, `labels`, `selectedMomentId`, `camera`. Both arrangements use identical canonical station identities and ordered route/source edge memberships.
- Support **A-only, A+B, arbitrary valid route subsets and All**; focus must be able to show two pathways concurrently. Source layer filter remains orthogonal and never implies a transfer.
- Schematic and Linear are **alternative arrangements**, not portfolio carousel chapters. Linear must preserve meaningful source order and actual branch membership; avoid drawing fake continuous connections for disjoint records.
- There is no authentic Geographic representation and no completed Spatial view; do not add either. Presentation/export must be a controlled, deterministic state with controls hidden in captured frames.
- Fit uses actual visible route/station/label SVG bounds, with measured space for headings and controls. One camera owner handles resize, fullscreen, focus and labels-off. Avoid label-click zoom; clicks should inspect evidence. Bound wheel/button zoom to useful content-derived limits; phone layouts keep a legible stage window and pan instead of shrinking the full ten stages.
- Prefer a self-contained, locally viewable HTML/SVG artifact; upstream's viewer intentionally avoids runtime fetches for offline export. The present V7 Google-font import is a candidate for offline/self-containment review before shipping.

### F. Cartography quality is a measured engineering gate

Avoid tuning CSS to compensate for rejected geometry. Compare candidates based on topology-preserving objective metrics and human review:

1. **Bend economy:** count weighted non-station turns and redundant reversal changes for each named route; remove geometry jitter while retaining genuine 45° turns.
2. **Route continuity and track ordering:** verify parallel offsets remain stable through shared segments and rejoin junctions, with no unexplained line swaps or overlaps.
3. **Stage/organization readability:** preserve all ten ordered stage domains and the seven source layer identities; test alternate vertical band spacing instead of making each research stage a fixed 330-unit corridor when that compresses junctions.
4. **Labels:** use upstream oriented-box `labels.py` collision handling; test actual drawn text, 45° label boxes, and station/line/stage-heading clearance. The current browser visibility pass is supplemental, not proof of no collisions. Record priority labels (branch, authorization, handoff, release) that were dropped or clipped.
5. **Density/whitespace:** measure empty space, path stretch, number of stations per occupied band, and long low-information vertical excursions. Evaluate CDMX for distributed hubs, SF Muni for shared-track offsets, Chicago for meaningful junction continuity; **do not copy their topology**.
6. **Visual task tests:** at 1440×900 and approximately 390×844, can a reviewer trace A&E versus direct, identify a real handoff, follow a technical/financial activity, recover stage order, and inspect source evidence without a zoom surprise?

No fixed bend-count or whitespace threshold is proven by the references; establish baselines from rendered candidate outputs rather than inventing an arbitrary passing score.

## Implementation order and measurable deliverables

| Priority | Work package | Deliverable | Pass condition |
| --- | --- | --- | --- |
| P0 | Coordinate bridge integration | V8 adapter imports PR #6 shared exact bridge and weighted angle validator | New tests and source integrity green on 59/68 projection; no remaining `cos(48°)` adapter |
| P0 | Provenance and layout store | Atomic immutable geometry artifact with manifest and full intermediate stages | Reuse accepted layout without implicit LOOM reruns; original source/route/solver identity traceable |
| P0 | Source/solver comparison | Directed provenance and per-line station adjacency checks, stage-order and source-layer checks | Any lost/gained/merged station or unauthorized transfer rejects native result |
| P1 | Stage-constrained cartographic candidates | At least two topology-identical layout candidates with geometry/label metrics and screenshots | Both preserve canonical IDs/edges; publish **only** accepted geometry and explain why a candidate is selected |
| P1 | Line order and label quality | Shared-route offset audit, junction straightness, rotated-label clearance, priority label coverage | No unreviewed line order inversion or visible priority-label/stage-heading collision at test viewports |
| P1 | Viewer parity | Unified Schematic/Linear controller, multi-route selection A+B, labels, content-aware Fit, zoom and fullscreen | Browser tests validate identical IDs and order across modes, stable camera and route subset bounds |
| P2 | Portfolio-grade presentation | Minimal UI aligned to P `.mj-controls`, accessible labels and caption hierarchy | No decorative proof text, no misleading train/time/geographic metaphors, fullscreen/mobile tested |
| P2 | Carousel and product integration | Only after technical/visual approval; separate M-Journey implementation decision | Six established chapters preserved, no retired Spatial view, no unapproved code/product release |

## Proposed CI and audit structure

- **Source unit suite:** canonical counts, stage ordinals, distinct research layer IDs, route chain continuity, directed edge provenance, approved handoff IDs, no fabricated physical/time/persona semantics.
- **Projection suite:** import PR #6's tests, exact synthetic Mercator roundtrip across both axes at large vertical extent, 3+ point polylines and canonical ID preservation.
- **Determinism suite:** identical **stored** accepted layout renders produce byte-stable SVG/HTML under unchanged options; compare raster outputs in **RGB with a channel tolerance**, never RGBA alpha-only or PNG file hash equality. Comparing two freshly optimized `topo` runs for byte equality is invalid.
- **Native suite:** compile pinned original C++ tools and record input, `loom`, `octi`, solver commit, audit and accepted/rejected disposition. Require explicit `solver.used=true` for native acceptance; a green fallback job is not evidence of native acceptance.
- **Visual/browser suite:** screenshots Schematic and Linear at desktop/mobile; labels-on/off; A, B, A+B, all; station inspector with invariant camera; repeated Fit/zoom extremes; fullscreen; no viewport clipping, stage-heading collision or misleading overlap. On each browser run, record active selection and actual SVG bounds.
- **Human approval:** review candidate and reference screenshots side-by-side, record outstanding defects, and withhold integration until the user accepts the composition and semantics.

## Work coordination and integration boundary

Keep current draft experiments intact: PR #4 is the reference/source-backed 23-station diagnostic; PR #6 is the independently green exact projection fix; PR #5 is the unfinished ten-stage V7 experiment. **Do not merge one into another wholesale without checking their different bases and changes.** V7 contains code paths PR #6 does not modify, so V8 should explicitly adopt only the projection/angle primitives and tests, then validate them with the full projection.

Other agents may deliver further research. Update this plan by appending sourced decisions, risks and deltas, not silently rewriting previously confirmed facts. Run an exact-head review after incorporating each external result. Keep the user-facing portfolio and `sss2808/m-journey` repositories unchanged until a separate approved implementation phase. Do not merge, deploy, or publish this planning branch without explicit authorization.

## Evidence gaps still open

1. The exact geometry and line-membership status for the **59-station V8** under the PR #6 bridge is unknown; V7 native fallback cannot be treated as accepted.
2. A deterministic semantic way to lay out all ten stages with low bend count and correct multi-route junctions has **not** been demonstrated.
3. Dynamic multi-route A+B selection, Linear branch-aware presentation, and label-on/off Fit parity are not yet fully implemented in V7.
4. The original transit viewer's presentation seam is a design reference; reusing `window.__present` verbatim for M-Journey requires a deliberate adapter review, not direct copying of train controls.
5. Source-specific permissions and licensing for the original map SVGs remain for review before any portfolio publication.

**Planning rule:** correctness gates first, composition/interaction second, optional polish last. A visually convincing map that alters research adjacency fails, and a mathematically valid map that still looks like a jagged corridor is not finished.


## V8 addendum: PR #7, upstream notebooks and contributor testing requirements

**Added 2026-11-02.** This section refines the prior work packages without claiming any implementation has occurred. Preserve the distinctions between original upstream GTFS pipeline behavior, the currently restricted M-Journey research adapter and proposed V8 quality gates.

### 1. The semantics of the pipeline are narrower than the word “schematization”

The upstream notebooks provide a useful inspection order:

| Stage | Upstream notebook observation | V8 diagnostic question |
| --- | --- | --- |
| `gtfs2graph` | Creates a GTFS-derived GeoJSON line graph; **not applicable** to canonical authored research records | Is our explicitly versioned adapter generating exactly the authorized stations and selected directed relations? |
| `topo` | Merges overlapping track/platforms, potentially removing separate stop identities | Leave disabled; would any merge remove or fabricate a research station, connection, membership or handoff? |
| `loom` | Solves line ordering on existing edges without changing geometric centerlines | Are shared-track occupancy and per-edge ordered route labels correct? Do not expect this stage alone to remove jagged elbows |
| `octi` | Moves/schematizes coordinates onto a supported base graph/grid | Are stage ordering, source adjacency, bend count and length-weighted 0°/45°/90°/135° quality acceptable? |
| `schematic.render` | Draws one addressed SVG path per (line, edge) with native parallel offsets, station glyphs and oriented-box labels | Do offset changes and label collision occur here rather than in the optimized centerline? |

From [notebook 02](https://github.com/richc117/legible-cities/blob/main/notebooks/02_build_line_graph.ipynb), compare `station_id` and `station_label` after schematization and enumerate all edges carrying more than one line. Record the *authored-source* to *post-solver* correspondence; a stop ID lost by transit-platform merging is unacceptable for M-Journey absent an explicitly approved source mapping.

From [notebook 03](https://github.com/richc117/legible-cities/blob/main/notebooks/03_schematize.ipynb), measure angles **after** `to_mercator`, length-weighted. The notebook demonstrates `octi -b` choices `octilinear`, `orthoradial`, `ortholinear`, and also names `hexalinear`. Treat other bases strictly as separately audited *visual-layout experiments*; a visually appealing ring or orthoradial form is not evidence for an authored customer lifecycle loop.

From [notebook 04](https://github.com/richc117/legible-cities/blob/main/notebooks/04_render_svg.ipynb), draw the **same accepted octi graph** both with `schematic.render.render` and LOOM's `transitmap -l` for a diagnostic, never as two parallel production map engines. Differences in junction appearance, parallel-track stroke order and label placement help localize whether the defect is in solver centerlines versus M-Journey's renderer/offsets. The reference viewer requires native stable SVG path identity; preserve canonical IDs for source reconstruction.

### 2. Source certificate is not the same as a pretty, byte-stable layout

PR #7 further tightens our P0 requirements:

- Persist a **frozen source manifest** *before* running a solver. Store directed `sourceEdgeId → fromId/toId`, the ordered station and stage/layer fields, authorized visual line IDs, route membership *on every selected source edge*, and which links are traversable versus merely dependency/feedback annotations.
- Validate **exact station identity and cardinality** and **per-connection ordered line membership**. Comparing only a set of readable labels or undirected adjacency, as in the proof, is insufficient. Source direction may live in the immutable projection manifest even when LOOM treats rendered track geometry as undirected.
- Normalize away **geometry-only helper vertices** when comparing source station adjacency, while retaining all geometry details in the layout artifact. Helper-node-pointer reshuffles must pass the semantic gate; dropped/added stations, source adjacencies, unauthorized handoffs, altered line occupancy, or stage regressions fail.
- Keep **two distinct hashes**: an input/cache identifier derived from input and build configuration; and **an output digest** over the exact accepted layout/render files. Neither the input ID nor raw byte JSON comparison across independently optimized runs establishes topology identity. Save a separate stable **semantic fingerprint** of station identities, normalized source/route connectivity and ordered line memberships, excluding transient pointer IDs.
- A solver run must report `solver_attempted`, `solver_accepted`, `fallback_used` and `presented_artifact_id` independently. An optimizer exit status cannot promote a rejected native result; a source-preserving fallback may be displayed as *diagnostic*, but never masquerades as accepted optimized geometry.
- Archive **every** attempted candidate, including all intermediate stage outputs, rejected stages and exact failures, and keep accepted outputs in immutable durable storage. PR #7 reports **14-day artifact retention** for its underlying 23-station proof. Prior V7 workflows may set other expiration windows; inspect each workflow rather than treating any GitHub Actions archive as permanent.
- Record the exact LOOM source commit SHA, OS/architecture, compiler/solver backend, all stage arguments, source/adapter SHA and input/output digests. Do not depend on moving branch heads or on `SCHEMATIC_LOOM_COMMIT` alone as a guarantee that a recomputed layout equals the approved output.

**Repeat-run matrix:** Run the frozen V8 adapter input ten times through `loom → octi` on the pinned native configuration, and save/compare each run separately. Include semantic graph fingerprints, geometry differences, stage integrity and weighted octilinearity. Only if a concrete need arises, run `topo` in an isolated experiment across the intended operating systems; in upstream [issue #44](https://github.com/ad-freiburg/loom/issues/44), macOS variants differed semantically, while an eight-run Ubuntu control did not. A stable ten-run sample is **not** a deterministic guarantee.

**Negative regression fixtures:** a missing authorized edge (fail), a newly added transfer (fail), two merged research stations (fail), a duplicated `station_id` (fail), a per-edge line membership/order change where the order is prescribed (fail), a backward stage move (fail), and a helper-vertex-pointer/ID relabel with invariant canonical graph (pass). Build these as explicit automated cases, not merely code review checklist items.

### 3. Explicit test coverage is mandatory: a green CI badge is not enough

[Upstream CONTRIBUTING.md](https://github.com/richc117/legible-cities/blob/main/CONTRIBUTING.md) states that its standard workflow can skip feed-, stored-layout-, native-LOOM-, real-map-, ffmpeg- and capture-dependent tests when fixtures are unavailable. This is an upstream **coverage warning**, not evidence that any particular M-Journey CI run skipped those tests.

- Use pinned Python 3.12+ dependency setup (`uv sync --locked --extra dev` in the original project), and report test **executed/pass/fail/skip** counts and named skip reasons using `pytest -q -rs`. A green suite with missing solver/capture dependencies is an incomplete V8 acceptance record.
- Build actual native LOOM and explicitly run the dedicated V8 stage/identity/negative-provenance suite. Verify the source manifest, `solver_accepted=true`, source edge membership, direction and stage constraints in an exact-head CI job. Do not allow `solver_accepted=false` with success exit to satisfy the *native acceptance* job.
- Run **full Chromium** for picture/presentation QA when reproducing upstream screenshot behavior; CONTRIBUTING distinguishes it from the headless shell because rasterization can differ. Include 1440×900 desktop, ~390×844 mobile, native fullscreen, Schematic/Linear, A-only, B-only, A+B and labels on/off.
- Perform browser accessibility audit (`bin/audit-page`/axe as supported) on the actual tested generated page. Check keyboard route selectors, inspector and fullscreen controls, contrast and reduced-motion behavior.
- For changes to upstream renderer/engine or integrated atlas behaviors, follow the original's **real-data** regression method: build LA Metro, Pittsburgh T and CDMX and inspect changes to station, line, matched stop and dropped-label counts, reviewing all skips. Keep this separate from V8's research-fixture-only tests.
- Image comparisons must use **RGB channel differences and a tolerance**, never raw PNG file hashes or RGBA-alpha-only checks. Put actual screenshot files, environment and dynamic state beside results. Zero `dropped_labels` does not prove human legibility.

### 4. Updated execution order and decision gates

| Priority | Concrete addition to existing V8 plan | Definition of done |
| --- | --- | --- |
| **P0a** | Merge *conceptually* the PR #7 canonical source certificate into the proposed V8 adapter validator | Stable source moment IDs, directed source edge ID, exact authorized line memberships per edge, ordinal stages and layer properties all audited; negative tests behave as expected |
| **P0b** | Integrate proven PR #6 Mercator bridge and weighted octilinearity without modifying research topology | 59/68 V8 tests explicitly pass, no legacy approximation, all solver-created polyline vertices retained |
| **P0c** | Implement immutable candidate/output bundle and differentiate input, semantic and accepted-output fingerprints | Replaying accepted geometry never implicitly re-invokes LOOM; fallback is visibly diagnostic, rejected stages persisted |
| **P0d** | Add executed-vs-skipped CI evidence plus pinned real native and browser jobs | Native acceptance cannot silently skip; logs/manifest report actual runs and dependency versions |
| **P1a** | Profile geometry at `loom`, `octi` and renderer separately; compare `schematic.render` with LOOM `transitmap` on identical accepted graphs | Bend/offset/label defects localized to the responsible stage before any styling changes |
| **P1b** | Evaluate low-bend, stage-constrained candidates and complete multi-route Schematic/Linear camera/interaction parity | Topology unchanged, A+B focus and Fit tested, priority labels and junctions visually reviewed |
| **P2** | Apply editorial visual style, animation and portfolio integration after correctness plus usability approval | No invented geographic mode, passenger/time metaphor, decorative technical claims or loss of original six-chapter portfolio narrative |

**Dependencies:** The candidate validator and source certificate gate all later cartographic output. The exact coordinate bridge and immutable output audit are independent P0 tasks and can be implemented on separate draft branches, but their final combined test must cover 59 moments and 68 chosen edges. Only then choose a composed Schematic. Do not interpret PR #6's green 23-station CI as a passed 59-station V8 geometry run.

### 5. Coordination notes for the other agents

- PR #7 is already documentation only; avoid copying it verbatim as a second competing source-of-truth document. This addendum links its additional acceptance requirements into the existing V8 plan and leaves both originals intact.
- Treat the notebooks as **stage-by-stage debugging recipes** that use public GTFS, not direct algorithms for generating authorized research connections. Notebook 02's `topo` example is explicitly **not** permission to enable that stage in V8.
- Compare source, line-order, optimized geometry, SVG offsets, and browser camera in that order before writing CSS tweaks. Source integrity and optimized geometry acceptance are different from meeting the visual design bar.
- No source research fixture edits, new routes, merges/deployments, portfolio/product modifications, or reintroduction of the retired Spatial view are authorized by this planning update.


## Implementation update: P0a source certificate

**Status:** code and tests proposed in [draft PR #10](https://github.com/sss2808/legible-cities/pull/10), stacked on the V8 plan branch. This is not an approval of V8 geography, LOOM optimizer output, research-method validity or portfolio publication.

- Reusable implementation: \`src/schematic/mjourney_source_integrity.py\`; source-only CLI: \`bin/mjourney-source-certificate\`.
- Frozen V7 sanitized source bytes and semantic projection hash: \`fixtures/mjourney/equipment-source-certificate-lock-v7.json\`. This prevents a silently changed fixture from generating a newly self-consistent baseline.
- Source authority includes all 67/87 canonical records and the selected 59 moments, 68 directed source relationships and 11 explicit route IDs. Exact station/line IDs, stage/layer identities, directed source-edge provenance, and per-edge route memberships are explicit.
- Strict pre-solver validation fails on fabricated transfer edges, dropped/reversed source links, duplicate stations, membership changes and source metadata drift. Post-solver structural mode collapses geometry-only helper vertices and **does not** claim to verify directed source provenance.
- Negative/positive unit tests and the dedicated exact-head CI issue machine-readable audit outputs. See [P0a implementation notes](MJOURNEY_V8_P0A_SOURCE_CERTIFICATE.md) for usage, scope limits and test cases.
- **Pending independent work:** PR #6 Mercator integration and 59-station native solver acceptance (P0b); durable accepted-stage artifacts (P0c); executed/skip coverage for native+browser QA (P0d); source-aware solver-edge reconstruction; cartographic visual quality (P1).

## P0b implementation and latest M-Journey product interpretation

The [product RFC #429](https://github.com/sss2808/m-journey/pull/429) has a **newer source-backed grouping interpretation** than the original V7 line-chain prototype. The final colored Schematic/Workstreams guides map to a chosen *authored grouping field* (the equipment package has seven existing layers). Named pathway \`routeId\` selection is a separate filter, and directed source \`JourneyConnection\` edges are a separate System data layer. A layer guide that passes between moments **does not create a new authored connection**. Portfolio-only regrouping by existing moment type is a distinct proposed experiment, not an existing generalized product feature. The existing product editor, analytics, evidence, scenarios and comparison tools remain intact.

Therefore **do not extrapolate V7's eleven route-colored tracks into a final product contract**. The 59/68 V7 selected-route graph is a limited topological stress fixture for P0a/P0b, not the eventual seven-group Schematic or the complete 67/87 directed system overlay.

**P0b code:** [draft PR #11](https://github.com/sss2808/legible-cities/pull/11) ports PR #6's reversible metric projection into \`bin/mjourney-system-network\`, uses the original upstream length-weighted \`octilinearity\` (> or = 99.5% within 1°), verifies frozen source identity before the native candidate, pins LOOM's exact commit and runs a separate native acceptance gate. The [P0b engineering note](MJOURNEY_V8_P0B_EXACT_METRIC_INTEGRATION.md) records limits. **Do not claim a geometry acceptance until the actual native CI confirms solver.used=true.**

The first product-facing milestone after correctness is still a coherent **Schematic + Workstreams + System** experience, all from the same canonical moments, authored stage/layer data, source connection IDs and existing filter identities. It should be reviewed with real 67/87 research content and stage columns, not achieved by adding phantom transfers to the V7 proof.
