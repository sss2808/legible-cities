# M-Journey System viewport and category-legend composition experiment

Status: **implemented fork-only experiment, in review, visual approval open**. TM-01a subtask, stacked on [Legible Cities PR #20](https://github.com/sss2808/legible-cities/pull/20). Implemented in [draft PR #21](https://github.com/sss2808/legible-cities/pull/21), branch `feature/mjourney-system-responsive-legend-framing`. Registration is [M-Journey W374 draft PR #433](https://github.com/sss2808/m-journey/pull/433), deliberately stacked on unmerged W373 governance #431.

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

## Implemented in draft PR #21

- `src/schematic/page/mjourney_responsive_frame.js` adds an opt-in, keyboard-operated **Hide lines / Show lines** disclosure for the **original seven** native line-chip controls. No replacement widget, source route selection, filter state or native camera.
- `bin/mjourney-preview` scopes the layout to M-Journey System: the seven native chips **wrap into available space instead of disappearing into horizontal overflow**, while the existing All/None controls and research labeling remain intact.
- `tests/browser/test_mjourney_responsive_frame.py` checks real Chromium at 950×520 and 1440×900: all seven source categories remain visible, original toggles and keyboard handling work, hidden/open state keeps original DOM controls, the page does not overflow horizontally or vertically, the map and inspector do not intersect, and **all 67 original station marker centers remain inside the map viewport when the inspector opens**.
- `.github/workflows/mjourney-system-research-contract.yml` runs the dedicated browser audit after the existing source boundary and inspector checks, capturing actual screenshot and JSON diagnostic artifacts.

## Verified exact-head evidence and limitations

- [Custom CI run #41569762108](https://github.com/sss2808/legible-cities/actions/runs/41569762108) passed both `canonical-research-contract` and `browser-inspector-smoke` jobs at `303fdcf7d84aea66f89402ee406d893a8c1f13e0`. The preceding run #41569258935 already passed both custom jobs; the newer run adds a strict every-station visibility assertion.
- [Actual browser screenshots + `system-responsive-frame-metrics.json` artifact](https://github.com/sss2808/legible-cities/actions/runs/41569762108/artifacts/13200732335). At 950×520 the compact map stage is 344.25px before inspector, 394.92px when legend collapsed, and 212.25px when inspector opens. No source station disappears, and no page scrolling is introduced. 1440×900 shows all seven native categories on a single row.
- **General fork suite known parent failure:** [fork PR #20 exact-head test run #41566569906](https://github.com/sss2808/legible-cities/actions/runs/41566569906) already failed `tests/test_site.py::test_the_page_describes_its_map_once_from_the_layout_it_already_has` because `page.html` contains four `map-description` strings where the test expects two. [PR #21 general run #41569258899](https://github.com/sss2808/legible-cities/actions/runs/41569258899) has the **same inherited failure** with 1 failed, 1711 passed, 126 skipped. `page.html` and that test are outside TM-01a ownership; no blanket assertion that the full suite passed. The latest full-suite run must be checked separately.
- **Static framing constraint:** The complete ten-stage layout is panoramic. A tall 1440×900 viewport will retain unused vertical space under native `preserveAspectRatio="meet"`. Filling the entire panel would require intentional camera crop/pan or distortion; neither is approved as a silent CSS fix. The native SVG viewBox is untouched. A separate, owner-coordinated camera/semantic zoom task is needed to improve tall-frame detail.
- **Not an accepted product update:** no M-Journey source, editor, portfolio, deployment or GPL redistribution; no source stage/edge/line IDs, derived route topology or semantic classifications changed. Reviewer acceptance and licensing remain pending.

Status tracker: **fork-only experiment in review; both targeted CI jobs green; full general suite has the pre-existing parent failure; full-height overview framing not resolved**.