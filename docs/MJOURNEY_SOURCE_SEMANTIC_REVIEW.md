# TM-01b source-backed semantic review lens

**Status:** experimental visual integration, not approved journey semantics, native cartography, or product release. Built in the GPL-3.0 Legible Cities fork as a deliberately stacked addition to [TM-01a PR #21](https://github.com/sss2808/legible-cities/pull/21), which depends on [stage-demand PR #20](https://github.com/sss2808/legible-cities/pull/20).

**Cross-repository tracking:** [M-Journey issue #437](https://github.com/sss2808/m-journey/issues/437), [TM-02 research classification PR #435](https://github.com/sss2808/m-journey/pull/435), [pending governance register PR #431](https://github.com/sss2808/m-journey/pull/431).

## What changes in the visual prototype

The existing native System stage-constrained metro and seven colored category filters remain unchanged. The existing directed focus highlights already illustrate the A&E/EPC and direct-customer alternatives `eq31 → eq37`, including source-backed branch/reconvergence rings.

TM-01b **reuses the existing Relationships selector**. It retains the original no-focus and A&E/direct options, and adds two explicitly qualified research-review choices. No extra toolbar row is created:

1. **No focus** (existing default): unchanged category guides, native stations and existing relationship controls.
2. **Handoffs (3):** source-authored relationships `edge71` (eq52 C&Q handover → eq53 Validation starts, **same layer**), `edge78` (eq59 Released to production → eq60 Handover, **cross layer**) and `edge84` (eq64 Project closed → eq65 Operate/maintain, **cross layer**). Dashed amber directed source strokes are computed from the *existing actual station positions*, using the already integrated native SVG corridor candidate router. They are labeled as **review candidates, not approved transit interchanges**. No transfer marker, category rail or source edge is created.
3. **Lifecycle return (1):** original directed `edge87` from eq67 End-of-life to eq01 Need emerges. Only the two actual endpoint stations receive dashed rings, with a textual description. **No full-map transit rail is drawn** from the last stage to the first, because it would misleadingly imply a traversal/scale and conflict with legibility.

Because both source alternatives and review options share a **single native select**, only one focus choice can be active at once. This prevents visually stacking different semantics into a purported single customer itinerary.

All source relationships, IDs, directions, stages, grouping assignments, category continuity and inspector evidence are unchanged. The renderer/visual fork is not a new persisted editor model. Unlike the category guides, the highlighted handoff paths correspond to existing directed source edges; their presentation is still experimental.

## Research authority and review status

The source of truth remains `fixtures/mjourney/equipment-sanitized-v1.json`, verified by the native read-only `mjourney-system-research-contract/v1` before viewer injection. W375's independently derived 87-edge and 67-station matrix confirms typed handoffs, route scopes, cross-layer counts and the lifecycle endpoint relation. This module does **not** duplicate the matrix CSVs, invent new source/edge IDs, translate geometry into research interpretation, or fetch private evidence.

A source `handoff` type does not automatically establish a **customer-visible transfer/interchange**. `edge71` explicitly remains a same-layer authored handoff. An ordinary cross-layer `sequence` or `dependency` must not be represented as a transfer. The complete set of category guides remains **60 non-traversable segments**, separate from the **87 authored directed research relations**.

Underlying interview/research evidence was not retrieved in this prototype. Source classifications and their qualifications therefore remain subject to research-owner review. No inferred duration, volume, causal effect, customer prevalence or relative business importance is introduced.

## Implementation boundaries

| Path | Change |
| --- | --- |
| `src/schematic/page/mjourney_semantic_review.js` | NEW read-only typed-source classifier, review selector, SVG presentation layer and isolated test API |
| `bin/mjourney-preview` | BOUNDED stacked script bootstrap only; no additional CSS/header height or native SVG fit changes |
| `src/schematic/page/mjourney_scene.js` | BOUNDED one-line safeguard on dependent PR #22: show eq31/eq37 branch rings only for existing authored focus options, not review choices |
| `tests/browser/test_mjourney_browser.py` | BOUNDED inherited test expectation update for two additional choices in the original Relationships select |
| `tests/test_mjourney_semantic_review.cjs` | NEW source-snapshot counts, original edge IDs and negative contract cases |
| `tests/browser/test_mjourney_semantic_review.py` | NEW real Chromium review, source endpoints, reversibility, keyboard-accessible select and viewport metrics |
| `.github/workflows/mjourney-source-semantic-review.yml` | NEW exact-head CI for original fixture integrity, source/projection tests, Chromium captures |
| `docs/MJOURNEY_SOURCE_SEMANTIC_REVIEW.md` | NEW decision/provenance/visual acceptance record |

No modifications to `mjourney.py`, `mjourney_research_contract.py`, `mjourney_labels.js`, canonical source fixtures, native station geometry, original renderer, W375 source docs, M-Journey Editor/Product/portfolio, or other agents' PR branches. The one-line scene guard and inherited browser expectation update are explicitly stacked on PR #21, never committed to its branch. Fork GPL-3.0 code is not imported into M-Journey or the portfolio.

## Verification protocol and acceptance boundaries

Generate the existing native experimental System HTML:

```bash
python bin/mjourney-preview --system-v3 --stage-demand-corridors --html \
  --focus-path ae=edge44,edge48,edge49,edge50 \
  --focus-path direct=edge45,edge51,edge52 \
  --output out/system-browser.svg
```

Then run:

```bash
node --check src/schematic/page/mjourney_semantic_review.js
node tests/test_mjourney_semantic_review.cjs
python tests/browser/test_mjourney_semantic_review.py
python tests/browser/test_mjourney_responsive_frame.py
```

The dedicated workflow also executes original read-only fixture/projection Python tests and checks the P0a frozen byte digest. The existing full research browser workflow continues to exercise the original vendor-alternative UI. Browser tests verify original 67 native stations, 87 directed relationships, seven category controls, 60 non-traversable guides, three authored handoff path identities and exact endpoints, two actual lifecycle endpoint markers, no fabricated interchange, and exclusive focus controls at 950 × 520 and 1440 × 900.

Screenshots and the machine-readable audit are uploaded as CI artifacts for **independent human visual review**. **Automated source tests and screenshots alone cannot approve cartographic appearance**, camera framing, label clarity or the semantic placement of transfers.

**First-run regression and correction:** An initial standalone extra control row passed the new semantic browser test, but failed the inherited 950×520 responsive inspector test: the extra row reduced map height and cropped 14 source station centers. This was not waived. The revision moves review choices into the existing Relationships selector, removes the extra CSS/row and limits branch rings to original focus values. Rerun the inherited responsive and new semantic tests on the revised exact head before acceptance.

The existing upstream parent [PR #20](https://github.com/sss2808/legible-cities/pull/20) and responsive [PR #21](https://github.com/sss2808/legible-cities/pull/21) inherited a general `tests/test_site.py` page-description failure. The new dedicated review suite does not fix or weaken that unrelated upstream test. Broad-suite status and exact-head acceptance must be checked separately before integration.

## Actual screenshot review (2026-11-03)

The first revised exact-head [source and Chromium run #41635850862](https://github.com/sss2808/legible-cities/actions/runs/41635850862) **passed both focused jobs**, including the original 950 × 520 responsive test that failed when a separate review row was used. The run produced [PNG/HTML/metrics artifact #13230676453](https://github.com/sss2808/legible-cities/actions/runs/41635850862/artifacts/13230676453). The screenshots were opened and reviewed, rather than treating a green test as visual approval.

**Observed strengths:** all three authored handoff strokes are identifiable as distinct dashed amber directed overlays, with source IDs/endpoints checked; the return mode shows just two source endpoints; original branch-alternative selection remains separate and station/category counts stay intact. The 950 px layout no longer adds a new toolbar row.

**Observed limitations:**

- At **950 × 520**, the selected long text in the existing Relationships control was visibly truncated. The subsequent small source-only copy correction shortens the displayed review option to **Handoffs (review)**; the longer semantic qualification remains in the native select title, accessible name and desktop text. Re-capture and verify this on its new exact head.
- At **1440 × 900**, the composed inspector makes the panoramic seven-rail map occupy a relatively shallow horizontal band, leaving substantial unused space beneath. The static native Fit was intentionally retained rather than stretching 45-degree geometry. Camera/viewport work remains **TM-01**, not a research semantics change.
- Dashed handoff strokes necessarily intersect or overlap the original category-guide rail field in the right-hand lifecycle stages. Source authority is correct, but the visual distinction from a navigable interchange still deserves comprehension testing.
- In the **950 px inspector-open lifecycle** screenshot, the upper documentation rail comes close to the top crop boundary; the independent station-center containment assertion is **not** a complete route/label clipping audit. Geometry owner must evaluate the full painted rail and label bounds before visual acceptance.
- The seven categories remain largely separate, horizontally organized lines. These research highlights do **not** establish the shared-corridor and network cartography of the Mexico City Metro reference. Reorganizing the map would require separately reviewed traversal semantics and geometry, not fabricated junctions.

**Disposition:** functional source-relationship visual experiment accepted for further review **only**, not approved cartographic finish. Owner must independently inspect the final source head's screenshots, final exact-head CI, 950 px readability and 1440 px framing. Do not merge or embed in portfolio/product on this basis.

## Downstream gates

- **Research owner:** review W375's proposed treatment of handoff and recurrence; decide if any item warrants a new operational interchange marker. None is preapproved here.
- **TM-01 visual owner:** review real screenshot evidence against Legible Cities source-first, category/track separation, viewport containment and clarity. Retain revision gates.
- **TM-03 data contract:** only after semantic approval define opt-in reusable importable path/membership/transfer hints, with no second canonical graph.
- **Governance/integration:** the existing W373 register owner must add the TM-01b subtask via an owner-controlled update; fork PR remains stacked/draft/unmerged. GPL-3.0 licensing decision, second journey, editor, full product, portfolio and EXE/web parity remain subsequent gates.
