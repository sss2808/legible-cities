# W382 static transit cartography experiment

**Status:** source-safe visual candidate, independent review pending, unmerged. Fork-only. Not the default M-Journey application renderer or a portfolio release.

## Baseline and reference

- Parent stack: fork PR [#22](https://github.com/sss2808/legible-cities/pull/22) → [#21](https://github.com/sss2808/legible-cities/pull/21) → [#20](https://github.com/sss2808/legible-cities/pull/20).
- Owner coordination: [M-Journey issue #104](https://github.com/sss2808/m-journey/issues/104), W382 PATCH-CLAIM; PR #21 independent screenshot review [#6603853046](https://github.com/sss2808/legible-cities/pull/21#issuecomment-6603853046).
- Visual reference: original Legible Cities [LA Metro schematic](https://github.com/richc117/legible-cities/blob/main/docs/la-metro-rail.png). Borrow legibility, weight, termini and stage-independent path geometry. Do not copy assets into M-Journey, change the original upstream renderer or assume GPL clearance.

## Changes

1. Render larger, source-anchored white station disks and distinct guide termini using the **same 67 canonical station positions**. Decoration is not a new SVG station identity or an approved interchange.
2. Strengthen the original Legible Cities category guide strokes. All 60 guide paths remain native renderer outputs, with the same 7 category layers, original line colors, segment endpoints and no fabricated guide intersection.
3. Add compact near-origin layer labels only where browser-measured placement avoids existing moment labels, giving late-start lines identifiable origins instead of a permanent swimlane label rail.
4. Show all 10 **authored** operational stage names in compact display using a CSS source-name presentation. The existing numeric compact DOM/aria navigation and desktop source names are preserved.
5. Prioritize the existing source focus endpoints at default Key label density (Funding authorized, Vendor selected). Expand the browser-collision-measured label budget at desktop, leaving the prior compact maximum intact.
6. In default overview only, show the two already-authored research focus sequences: **edge44, edge48, edge49, edge50** (A&E) and **edge45, edge51, edge52** (direct). They use the existing validated corridor routes, with dashed analytical strokes and true source-ID endpoint rings. A visible qualification explicitly says these are research relationships, **not transit transfers**. Selecting an existing research-focus or PR #22 review mode hides this default overlay to prevent duplicate readings.

No new relationship, moment, station/line membership, projection metadata, order, customer itinerary, operational transfer, invented trunk, shared corridor or distant lifecycle loop.

## Real browser acceptance gate

Build the native generated static HTML with the original Legible Cities pipeline:

```sh
python bin/mjourney-preview --system-v3 --stage-demand-corridors --html \
  --focus-path ae=edge44,edge48,edge49,edge50 \
  --focus-path direct=edge45,edge51,edge52 \
  --output out/system-browser.svg
node --check src/schematic/page/mjourney_cartographic_polish.js
python tests/browser/test_mjourney_cartographic_polish.py
```

CI workflow `.github/workflows/mjourney-static-cartography.yml` checks the unchanged frozen fixture SHA, original 67 moments, 87 directed relationships, 7 layers, 60 **nontraversable** category guides, source edge endpoints, label collisions, responsive no-overflow, interaction/inspector, exact stage names and 950×520 / 1440×900 real Chromium screenshots. Its artifact includes `cartography-w382-950.png`, `cartography-w382-1440.png`, `cartography-w382-fork-1440.png` and `cartography-w382-metrics.json`. Re-run inherited responsive and semantic-review browser checks.

### Side-by-side visual assessment against original Legible Cities

| Gate | Original LA Metro renderer | W382 candidate / remaining risk |
| --- | --- | --- |
| Connected metro geometry | Actual connected rail infrastructure, bends, crossings and approved transfers | Stronger native colored paths and a *separately labeled* seven-edge directed research branch; seven categories remain nontraversable research guides, not a single travel network |
| Visible station hierarchy | Dense, named stops and distinct connection/terminal markers | Enlarged 67 source-anchored disks, explicit non-transfer guide endpoints, more labels at desktop, measured non-overlap |
| Source fork/convergence | True transit junctions when infrastructure connects | Only the researched eq31/eq37 fork and reunion are shown by default; rings are **research** endpoints, not interchanges |
| Wayfinding | Clear line names, stops and context | Source stage names at both sizes, contextual near-terminus line names, semantic IDs intact |
| Composition | Layout exploits a two-dimensional authentic rail topology | Full-width native ten-stage panoramic map remains vertically letterboxed at 1440×900; filling the blank height without cropping/stretches requires a separate approved camera/layout experiment |

**Acceptance is not implied by a green CI job.** A source-faithful no-transfer model cannot legitimately manufacture the dense cross-line physical junctions of the LA Metro original. User/independent cartographic review must judge whether this guide-versus-research-connection visual grammar is immediately understandable. Any broader geometry rerouting or camera change needs a new coordinated owner decision, rather than silently converting 64 cross-layer edges into interchange markers.

## Source safety and integration boundaries

The public sanitized fixture is unchanged (frozen SHA256 `580a66acd1b9f55fe4fa0aa3624bb4aa500028e34cdf8bac01cf138b7c59ce00`). W375 research classification and operational interchange authorization remain separate. W382 deliberately stacks on the active PR #22 bootstrap seam; no parent branch changes. No merge, deployment, M-Journey application import, license clearance or published portfolio material.
