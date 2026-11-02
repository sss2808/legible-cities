# P0b exact coordinate bridge for the ten-stage diagnostic

**Status:** implementation in draft [PR #11](https://github.com/sss2808/legible-cities/pull/11); native acceptance under test. No merge, deployment or product/portfolio change.

## Decision after evaluating the product-level review

M-Journey remains the authoritative research platform with canonical moments, authored relationships, scenarios, personas, comparisons, evidence and editing. Legible Cities is a presentation/rendering reference and LOOM an optional geometry optimizer. The [current product RFC #429](https://github.com/sss2808/m-journey/pull/429) clarifies that a colored metro line is a **chosen source-backed grouping dimension**. For the equipment fixture it can be one of seven authored layers; other packages may use other authored layer definitions. The user later approved testing existing `moment.type` as an optional *portfolio-only* regrouping experiment. Route focus, real directed source edges, and data groupings are distinct.

The **V7** visual proof uses eleven source-edge chains (two candidate buying alternatives and nine activity-chain identities) as transit lines. Those are a restricted *solver diagnostic*, **not the final product semantics** and not extra authored route IDs. This P0b changes their coordinates, not their meaning. Do not add fabricated same-layer directed connections to satisfy LOOM.

## What P0b implements

- Imports the existing [PR #6 exact metric adapter](https://github.com/sss2808/legible-cities/pull/6) in `src/schematic/mjourney_projection.py`. It converts synthetic ordinal diagram x/y through exact Web Mercator using the shared upstream `schematic.crs` routines, then maps to/from WGS84 for LOOM. The fixed (8°, 48°) anchor is synthetic and makes **no geographic research claim**.
- `bin/mjourney-system-network` now uses `graph.reproject(to_solver_point)` and `graph.reproject(from_solver_point)` instead of its local `cos(48°)` longitude / linear latitude approximation. **Every** solver-generated polyline vertex is passed through the inverse without simplification or re-elbowing.
- Replaces `poly_review`'s per-segment threshold with original `schematic.render.octilinearity` on recovered isotropic diagram coordinates, requiring **at least 99.5% of total drawn length within ±1° of 0°/45°/90°/135°**. Tiny rounding stubs do not dominate the score.
- Requires **P0a strict source certificate** (67/87 canonical, 59/68 selected graph, frozen source byte/semantic lock and directed source-edge memberships) before attempting native LOOM.
- The native output undergoes station/line/per-line-adjacency checks, stage-order check, P0a undirected structural review, and length-weighted octilinearity. It reports `sourceDirectionReconstructed=false`: P0a's frozen manifest remains the only source of directed relationship authority once native tools have rewritten edges.
- Uses only `loom → octi`, **not `topo`**. A candidate is displayed only if all hard constraints pass; otherwise the map is a visibly audited deterministic seed fallback, not accepted optimized geometry.
- Three test groups cover the 21 P0a regressions, the five inherited PR #6 projection tests, and a new seven-test full-ten-stage suite. The dedicated native CI compiles the **pinned LOOM fork SHA `1e4757838104d1e4d22186c9b77d5fc4b98681a0`**, saves intermediate `input/loom/octi` GeoJSON and detailed audit, and **fails closed when `solver.used=false`**.

## Outcome required to advance

This step is only geometrically accepted when the exact-head C++ native run reports **both** `solver.attempted=true` **and** `solver.used=true` with source station/line identities, stage order, per-line source adjacency, post-solver semantic review and weighted-angle threshold all passing. A green projection-unit test does not prove native acceptance. A rejected native candidate is still useful diagnostic evidence, but is **not** a completed full-scale map.

**Still out of scope:** the approved product's seven authored-layer (or other source-grouped) line identities; distinct directed system-edge overlays; 67/87 complete fixture visualization; stable edge-source reconstruction after native geometry; immutable accepted-layout archival (P0c); objective label/whitespace/junction QA; browser editor or portfolio integration and publishing. These remain separate gates in the [V8 master plan](MJOURNEY_V8_ARCHITECTURE_AND_GEOMETRY_PLAN_2026-11-02.md).
