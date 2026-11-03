# M-Journey System viewport and category-legend composition experiment

Status: **planning-only until registration and implementation**. TM-01 subtask, stacked on [Legible Cities PR #20](https://github.com/sss2808/legible-cities/pull/20). Own fork branch `feature/mjourney-system-responsive-legend-framing`.

## Goal

At 950 × 520 and 1440 × 900, keep every colored category guide and its controls accessible, avoid clipped or horizontally scrolling legend chips, and reduce unnecessary empty vertical space around the native source-traced schematic **without changing research semantics or rebuilding the native camera**.

## Owned behavior and files

- `bin/mjourney-preview`: only M-Journey System-scoped CSS and loading a new progressive-enhancement script, not upstream Legible Cities global styles.
- `src/schematic/page/mjourney_responsive_frame.js`: new, M-Journey-only responsive legend disclosure and non-motion static fit integration, reusing existing DOM and native controls.
- `tests/browser/test_mjourney_browser.py` or a new dedicated Chromium smoke: viewport, keyboard/ARIA, legend visibility, inspector, header height, complete map and source positions.
- `.github/workflows/mjourney-system-research-contract.yml`: focused CI and evidence artifacts if tests are added.
- This planning record, confined to this fork.

## Non-goals

No M-Journey product file editing, canvas replacement, animation, morphing, new graph metric, station significance, transfer/pathway semantics, import/export schema, user data, additional dependencies or GPL code distribution into another repo. Do not edit W361/W365 motion plans, W13-owned renderer regions, W370 map UX documents, W371 screenshot tools, the portfolio, or the shared M-Journey register except through its separate owner-aware registration PR.

## Dependencies and integration

- Source authority: original sanitized equipment (67 moments, 87 directed relationships, ten stages, seven grouping categories) and starter (19 moments/18 relations/three categories), validated through existing fork sidecar.
- Depends on fork PR #20 and its earlier stacked source-integrity, junction and corridor experiments. Does not assume any is merged.
- Coordination: M-Journey [PR #431](https://github.com/sss2808/m-journey/pull/431) / TM-01 register, and [issue #104](https://github.com/sss2808/m-journey/issues/104). W373 owns the shared register; submit the isolated registration for integration supervisor reconciliation.
- Review gate: exact-head synthetic-only source/Chromium verification, both target viewports, native line All/None and seven individual category chips, keyboard and responsive disclosure, no introduced clipping/scrollbars, unchanged rendered source IDs/stations/edges, screenshots before visual approval.
- GPL: this remains confined to the existing GPL-3.0 fork. No product or portfolio embedding approval.

Status tracker: **planned / doc-only**, fork PR and integration registration pending.