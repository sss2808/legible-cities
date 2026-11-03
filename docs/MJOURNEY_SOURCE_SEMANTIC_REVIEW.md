# TM-01b source-backed semantic review lens

**Status:** experimental visual integration, not approved journey semantics, native cartography, or product release. Built in the GPL-3.0 Legible Cities fork as a deliberately stacked addition to [TM-01a PR #21](https://github.com/sss2808/legible-cities/pull/21), which depends on [stage-demand PR #20](https://github.com/sss2808/legible-cities/pull/20).

**Cross-repository tracking:** [M-Journey issue #437](https://github.com/sss2808/m-journey/issues/437), [TM-02 research classification PR #435](https://github.com/sss2808/m-journey/pull/435), [pending governance register PR #431](https://github.com/sss2808/m-journey/pull/431).

## What changes in the visual prototype

The existing native System stage-constrained metro and seven colored category filters remain unchanged. The existing directed focus highlights already illustrate the A&E/EPC and direct-customer alternatives `eq31 → eq37`, including source-backed branch/reconvergence rings.

TM-01b adds a distinct, compact **Review** selector underneath the original research controls. It has three options:

1. **No review overlay** (default): unchanged category guides, native stations and existing relationship controls.
2. **Handoffs (3):** source-authored relationships `edge71` (eq52 C&Q handover → eq53 Validation starts, **same layer**), `edge78` (eq59 Released to production → eq60 Handover, **cross layer**) and `edge84` (eq64 Project closed → eq65 Operate/maintain, **cross layer**). Dashed amber directed source strokes are computed from the *existing actual station positions*, using the already integrated native SVG corridor candidate router. They are labeled as **review candidates, not approved transit interchanges**. No transfer marker, category rail or source edge is created.
3. **Lifecycle return (1):** original directed `edge87` from eq67 End-of-life to eq01 Need emerges. Only the two actual endpoint stations receive dashed rings, with a textual description. **No full-map transit rail is drawn** from the last stage to the first, because it would misleadingly imply a traversal/scale and conflict with legibility.

Choosing a semantic review option clears any active A&E/direct source-highlight selection; choosing an A&E/direct highlight clears semantic review. Thus sources from different visual contexts cannot silently accumulate into an apparently single customer itinerary.

All source relationships, IDs, directions, stages, grouping assignments, category continuity and inspector evidence are unchanged. The renderer/visual fork is not a new persisted editor model. Unlike the category guides, the highlighted handoff paths correspond to existing directed source edges; their presentation is still experimental.

## Research authority and review status

The source of truth remains `fixtures/mjourney/equipment-sanitized-v1.json`, verified by the native read-only `mjourney-system-research-contract/v1` before viewer injection. W375's independently derived 87-edge and 67-station matrix confirms typed handoffs, route scopes, cross-layer counts and the lifecycle endpoint relation. This module does **not** duplicate the matrix CSVs, invent new source/edge IDs, translate geometry into research interpretation, or fetch private evidence.

A source `handoff` type does not automatically establish a **customer-visible transfer/interchange**. `edge71` explicitly remains a same-layer authored handoff. An ordinary cross-layer `sequence` or `dependency` must not be represented as a transfer. The complete set of category guides remains **60 non-traversable segments**, separate from the **87 authored directed research relations**.

Underlying interview/research evidence was not retrieved in this prototype. Source classifications and their qualifications therefore remain subject to research-owner review. No inferred duration, volume, causal effect, customer prevalence or relative business importance is introduced.

## Implementation boundaries

| Path | Change |
| --- | --- |
| `src/schematic/page/mjourney_semantic_review.js` | NEW read-only typed-source classifier, review selector, SVG presentation layer and isolated test API |
| `bin/mjourney-preview` | BOUNDED stacked bootstrap/CSS addition only; original PR #21 responsive/focus code and renderer untouched |
| `tests/test_mjourney_semantic_review.cjs` | NEW source-snapshot counts, original edge IDs and negative contract cases |
| `tests/browser/test_mjourney_semantic_review.py` | NEW real Chromium review, source endpoints, reversibility, keyboard-accessible select and viewport metrics |
| `.github/workflows/mjourney-source-semantic-review.yml` | NEW exact-head CI for original fixture integrity, source/projection tests, Chromium captures |
| `docs/MJOURNEY_SOURCE_SEMANTIC_REVIEW.md` | NEW decision/provenance/visual acceptance record |

No modifications to `mjourney.py`, `mjourney_research_contract.py`, `mjourney_scene.js`, `mjourney_labels.js`, canonical source fixtures, original renderer, W375 source docs, M-Journey Editor/Product/portfolio, or other agents' PR branches. Fork GPL-3.0 code is not imported into M-Journey or the portfolio.

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

The dedicated workflow also executes original read-only fixture/projection Python tests and checks the P0a frozen byte digest. Browser tests verify original 67 native stations, 87 directed relationships, seven category controls, 60 non-traversable guides, three authored handoff path identities and exact endpoints, two actual lifecycle endpoint markers, no fabricated interchange, and exclusive focus controls at 950 × 520 and 1440 × 900.

Screenshots and the machine-readable audit are uploaded as CI artifacts for **independent human visual review**. **Automated source tests and screenshots alone cannot approve cartographic appearance**, camera framing, label clarity or the semantic placement of transfers.

The existing upstream parent [PR #20](https://github.com/sss2808/legible-cities/pull/20) and responsive [PR #21](https://github.com/sss2808/legible-cities/pull/21) inherited a general `tests/test_site.py` page-description failure. The new dedicated review suite does not fix or weaken that unrelated upstream test. Broad-suite status and exact-head acceptance must be checked separately before integration.

## Downstream gates

- **Research owner:** review W375's proposed treatment of handoff and recurrence; decide if any item warrants a new operational interchange marker. None is preapproved here.
- **TM-01 visual owner:** review real screenshot evidence against Legible Cities source-first, category/track separation, viewport containment and clarity. Retain revision gates.
- **TM-03 data contract:** only after semantic approval define opt-in reusable importable path/membership/transfer hints, with no second canonical graph.
- **Governance/integration:** the existing W373 register owner must add the TM-01b subtask via an owner-controlled update; fork PR remains stacked/draft/unmerged. GPL-3.0 licensing decision, second journey, editor, full product, portfolio and EXE/web parity remain subsequent gates.
