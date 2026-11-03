# M-Journey System constrained corridor routing experiment

Status: **draft and visual acceptance pending**. Branch `feature/mjourney-constrained-corridor-routing` stacked on [junction grammar PR #18](https://github.com/sss2808/legible-cities/pull/18).

## Source authority and design question

The user identified the strong triangle near **Funding authorized** and **Vendor selected**, and asked whether deliberate stepped tracks could create more legible corridors without turning unrelated crossings into transfers.

This experiment targets **seven original directed vendor-selection relationship records** highlighted over the existing Legible Cities-native category tracks. It does not reorganize those seven category-line chains and does not claim to solve the full schematic. Stage coordinates, stations, legend memberships and the canonical research graph are unchanged.

The public fixture's directed alternatives:
- A&E/EPC: `edge44,edge48,edge49,edge50`
- Direct customer-led: `edge45,edge51,edge52`
- Branch origin: **eq31** supported by `edge44` and `edge45`
- Reconvergence: **eq37** supported by `edge50` and `edge52`

None is independently approved as a verified customer itinerary; category guides remain explicitly non-traversable.

## Constrained candidate router

`src/schematic/page/mjourney_corridor_router.js` is browser-side and independent of Python LOOM, Octi and the native Legible Cities renderer. It uses the **post-render SVG station coordinates**, not the adapter's preliminary numbers.

1. For every source edge, generate deterministic combinations of horizontal, vertical and 45-degree segments between **the same two station locations**. For axial station pairs, bounded symmetric step detours are also candidates.
2. Keep candidates inside the original source-edge endpoint x envelope, permitting at most **28 SVG units** of additional x detour, and the native station vertical span plus **38 SVG units**.
3. Score each candidate for drawn length, bends, very short segments, proximity to any unrelated canonical station, crossings with native category-guide segments and overlapping previous selected source-edge geometry.
4. Select the lowest-cost candidate with a stable lexical tie-break. Plan both alternatives once in interleaved source order, even when only one is selected, so the same edge does not jump to another geometry when the UI changes focus.
5. Render only the seven original edge IDs through the existing SVG relationship overlay. No generated bend becomes a stop, interchange, graph node or source connection.

The router is a **bounded deterministic local heuristic**, not a global octilinear optimum. Station clearance is heavily penalized and independently checked by Chromium for the equipment focus. Native category geometry is only an obstacle input and is never modified in this slice.

## Measurable acceptance

- Original public fixture and P0a checksum unchanged: **67 moments, 87 authored directed relations, 60 non-traversable category guides**, ten source-authoritative stages.
- All highlighted edges maintain their original source IDs and original exact endpoint coordinates, with 0°, 45° or 90° route segments.
- No unrelated station lies within 13 native SVG units of selected routed edge interiors in the equipment branch.
- Explicit regression: old direct straight segment `eq35 → eq37` passed through an unrelated `eq34` station; routed `edge52` must clear it.
- Browser screenshot at 950×520 and 1440×900, with the same route geometry irrespective of selected focus. Diagnostic `system-corridor-metrics.json` records route lengths, bends, category crossings and per-edge minimum station clearance.
- Normal Legible Cities transit behavior and the no-trip research mode semantics stay distinct. Exact-head CI must pass before interpretation.

## Deliberate exclusions

This does **not** improve the global seven colored category-guide chains, invent shared corridors or additional line memberships, or assert source-backed transfers at geometric crossings. It does not optimize labels/camera, center the expanded frame, alter stage widths or solve all viewport clipping. Any later stage-constrained route optimizer for category tracks should be a separately tested geometry layer, backed by explicit before/after collision and provenance audits, rather than another series of CSS offsets.

No merge, deployment or edit to M-Journey product or portfolio occurs in this branch.
