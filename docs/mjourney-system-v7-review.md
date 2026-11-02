# M-Journey ten-stage systems-map experiment

Status: **Draft V7, not visually approved, not merged or deployed.** Branch `feature/mjourney-system-network-v7`. Stacked on the 23-station REA experiment in draft PR #4. The existing V5, V6, two-line and six-line experiments are preserved.

## Source and scope

- Canonical input is `fixtures/mjourney/equipment-sanitized-v1.json` with 67 sanitized moments, 87 authored relationships, ten stages and seven **authored research layers**.
- V7 projects 59 of those moments and 68 authored traversable sequence, branch, convergence and handoff connections. It does not alter the canonical fixture or add a moment, edge, cross-workstream transfer, role, duration or persona.
- Source route chains are explicit, ordered edge-ID arrays in `bin/mjourney-system-network`. Every adjacent pair in a chain is asserted to meet on the same canonical station. The A&E/EPC and direct-customer alternatives share prefix and suffix segments, diverge at eq31 and converge at eq37. They are **candidate source-backed pathways**, not independently validated customer behavior.
- Other routes are named **activity chains** (technical feasibility, concept documentation, business case costing, technical approval, financial review, site readiness, logistics readiness, validation strategy and handover documentation). The label is not a second validated customer itinerary.
- Three displayed source handoffs are edge71, edge78, edge84. These are distinct from crossings, same-colored segments or any invented interchange.
- `layer-0` is **Journey sequence**, not an organizational workstream. The other six layer records identify authored activity categories. The map's station ring and horizontal guides encode the canonical `layerId`; transit tracks encode continuous route families. Stage x-order is authored ordinal progression, not time.

## Architecture and visibility

- Ten headings are positioned using the rendered native SVG station coordinates and a checked affine stage transform.
- The y placement uses the seven recorded layer positions as a **display layout**; it never changes research relationships. Stage columns and layer bands are deliberately separate visual encodings.
- The same stable sanitized `eqXX` IDs drive the station markers, inspector and route focus. No raw source UUIDs, research narratives or confidential evidence identifiers enter the preview.
- `schematic.render.render` draws the path geometry, station markers, offset tracks and placed labels. Existing native label collision behavior and LOOM's exact candidate geometry remain the source of those shapes. Render-only round caps and joins do not change polyline endpoints.
- Focused routes have content-aware SVG viewBox framing. The research-layer filter highlights station membership without pretending an organizational lane is a second customer route. Zoom, Fit and fullscreen are in the figure toolbar. The inspector is closed until a station is selected.
- The standalone uses restrained portfolio-like button geometry. It is **not** yet an integrated six-palette portfolio exhibit.

## Before and after

| Attribute | Previous PR #4 | V7 proposal |
|---|---|---|
| Authored stations shown | 23 | 59 |
| Authored connections shown | 25 | 68 |
| Journey stages shown | 5 of 10 | 10 of 10 |
| Route identities | 2 candidate pathways and 4 short activities | 2 candidate pathways and 9 authored activity chains |
| Organizational context | Workstream largely inspector-only | Source research layer rings, spatial bands and interactive layer focus |
| Canvas | Extended horizontal corridor | Ten stage domains with vertical branching aligned to layer metadata |
| Reading | Tiny labels, fixed full-system fit | Importance-sensitive label visibility, route-specific framing, mobile pan and zoom |
| Inspector | Permanent 278px sidebar | Collapsible on-demand overlay |
| Visual checks | No confirmed owner approval | Dedicated desktop/mobile screenshots and browser tests in CI |

An increase in line/station count is not by itself evidence that the map is improved. The owner must judge continuity, label legibility, geometry and spatial balance against the original LA Metro REA screenshots.

## Integrity and native LOOM boundary

The command `python bin/mjourney-system-network --output out/mjourney-system-v7` creates standalone `.html`, `.svg` and `.audit.json` outputs. CI tests canonical counts, exact edge membership, continuous route chains, unique station identities, all ten stage orders, zero fabricated connections and HTML renderer structure.

The optional `--native-loom` executes original C++ `loom` and `octi`. The solver's graph is displayed **only if** per-line adjacency, all station IDs, all line identities, stage ordinal order and octilinearity pass the existing strict gates. The audit distinguishes `solver.attempted` and `solver.used`; fallback seed geometry is explicit, not falsely labeled as optimized. Native rejection must remain a geometry blocker requiring layout/constraint revision. Do not silently alter source topology or use `topo` to manufacture transfers.

The branch workflow also captures real Chromium desktop and mobile screenshots. Browser/CI results are evidence of functioning output, not owner visual approval.

## Remaining before product or portfolio integration

1. Review actual desktop and mobile captures for overall balance, meaningful visible branches, line overlap, stage and label collisions, compact toolbar layout and fullscreen behavior.
2. Inspect the native LOOM audit `solver.used`, edge ordering and any lost/gained per-line adjacency; adjust constrained input geometry, not the research graph, if rejected.
3. Tune label placement or introduce a verified collision-free progressive disclosure pass if the native placer drops important decisions and handoffs.
4. Confirm semantic representation of all seven research layers with the owner and decide whether to title the shared journey sequence separately from the six workstream categories.
5. Determine whether 11 route identities are too numerous at overview scale, and whether secondary activity branches should default to muted while retaining interactive focus.
6. Compare against the original Legible Cities map for track pitch, rounded turns, station markers, selected-route framing and mobile reading.
7. Review licensing, keyboard navigation, accessibility, color contrast and the exact V87 portfolio palettes.
8. Integrate only after approval into the existing six-chapter Network, Structure, Journey, Overview, Personas and Evidence progression, preserving one sample graph and stable public-local IDs. Do not reinstate the retired Spatial view or replace the scrollytelling with a static picture.

No merge, publication, deployment, portfolio modification or product replacement is authorized by this experiment.


## Follow-up after LA Metro REA deep-dive and owner screenshots

Reference: `docs/MJOURNEY_REA_LA_METRO_DEEP_DIVE_2026-11-02.md` on the underlying REA branch. The owner judged V7's greater source-backed network density to be an improvement while flagging camera faults, missing mode controls, small jagged bends and distracting public copy.

The standalone now exposes **Schematic** and **Linear** as two representations of the same canonical sanitized moments. Schematic retains the native Legible Cities rendered paths; Linear repeats those same canonical IDs in route-specific ordered rows and does not synthesize connections or infer time. The alternative Geographic mode seen in LA Metro remains intentionally absent because M-Journey lacks authentic geographic coordinates. The existing six-chapter portfolio sequence is also distinct from these map modes.

Camera behavior now has one `setView` owner, an aspect-correct `fitVisible` derived from native SVG track and station bounds, a 45% baseline minimum for short-focused routes, bounded zoom at 28%-110% of the initial full-network fitted width, and a Fit button that refits the currently selected content. Opening the station inspector from labels, stations or Linear stops does not change camera geometry. Fullscreen and resize re-fit with the same camera model.

The rejected deterministic seed no longer jitters canonical research stations vertically according to numeric IDs. Each authored connection now uses at most one 45-degree octilinear bend if one is required, and source-layer spacing is more compact. This is a **seed-layout readability change**, not acceptance or replacement of native LOOM solver geometry; no source edges, endpoints or line occupancy were altered. The native candidate must still pass the original audit gates. Preserving occasional purposeful angular turns is consistent with the REA reference. Rendering a loop/transfer that is not authored remains prohibited.

The public legend now contains only two useful pathway keys, with redundant explanatory prose removed. Additional activity routes retain names in the Route control and Linear rows. The inspector remains available for research metadata and source relationships.

### Explicit follow-up gates

- View switch toggles active pressed states, keeps IDs stable, supports both desktop and mobile, and renders all 11 ordered route rows in Linear.
- Route focus and research-layer filters produce content-relative Fit bounds without extreme closeups; repeated zoom-out never shrinks the map below readable baseline.
- Clicking a station name only opens its inspector, not zoom or selection-driven camera movement.
- Schematic seed has no arbitrary same-layer 16-unit jitter; no unsupported node or interchanges are added.
- Chromium screenshots and exact-head behavior tests must be reviewed. Passing browser assertions alone does not approve visual legibility.
- **Not yet implemented**: REA arbitrary A+B multi-route selection, route-level framing on very small mobile displays, full SVG label-collision visual approval, native LOOM acceptance and final portfolio integration.
