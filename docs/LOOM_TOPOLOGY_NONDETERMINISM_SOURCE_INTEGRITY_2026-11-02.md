# LOOM topology nondeterminism and source-integrity controls

**Date:** 2026-11-02  
**Status:** Research finding and implementation guidance. No solver change, research data change, product integration, or release approval.  
**Scope:** The Legible Cities fork's research-to-transit cartographic adapter. This document belongs in `sss2808/legible-cities`, **not** the `sss2808/m-journey` product repository.  
**Related work:** [REA cartographic audit](MJOURNEY_REA_LA_METRO_DEEP_DIVE_2026-11-02.md), [transit adapter plan](MJOURNEY_TRANSIT_ADAPTER_PLAN.md), [exact Mercator proof, draft PR #6](https://github.com/sss2808/legible-cities/pull/6), [expanded 23-station proof, draft PR #4](https://github.com/sss2808/legible-cities/pull/4).

## Executive conclusion

**LOOM's `topo` stage is not guaranteed to produce the same graph from the same inputs.** This is explicitly documented by the original Legible Cities architecture, independently evidenced in upstream LOOM issue #44, and confirmed as expected behavior by a LOOM maintainer. The consequence is not that every rerun is invalid, or that a different *shape* is a defect. The consequence is that neither identical inputs nor a passing geometry score can establish **research-source integrity** or reproduce the exact layout shown to a reviewer.

**Decision for the research adapter:** Keep the canonical authored journey immutable. Archive every solver candidate's stage inputs/outputs and provenance. Validate the candidate against canonical station identity, intended line membership, approved source connections and ordinal stage constraints **before** accepting or publishing it. Accept geometric variation only when all semantic invariants are preserved. Do not run `topo` against the research-derived network without explicit evidence that its aggregation respects these invariants.

## Primary evidence and what it actually proves

1. **Original architecture, first-party description.** [`docs/ARCHITECTURE.md`, “Layouts, and the determinism rule”](ARCHITECTURE.md) states: “LOOM's `topo` is not deterministic: the same binary on the same input can give a different graph.” The pipeline stores the four graph stages as `00_gtfs2graph.json`, `01_topo.json`, `02_loom.json` and `03_octi.json`, with `.meta.json`. It draws a map from a stored set rather than silently rerunning the layout. It says internal LOOM JSON node IDs are pointer addresses, so **raw byte equality is not the right graph comparison**. Its `tests/test_loom.py::_as_graph` compares stable station identity, graph endpoints and ordered edge-line labels instead.
2. **Upstream reproduction.** [ad-freiburg/loom issue #44](https://github.com/ad-freiburg/loom/issues/44), reported 2026-09-07, measured repeated `topo` calls on the same source graph and binary. A macOS arm64 run varied between 117 and 118 output nodes; a second macOS build kept the same node count yet still produced different graphs. The reported Linux Docker control was stable in eight repetitions. The reporter compared **semantic graph structure**, not pointer-ID or JSON bytes. This is evidence that nondeterminism can affect structure, not only serialisation, while **not proving identical variability on every platform and build**.
3. **Upstream confirmation.** [LOOM maintainer response, 2026-09-15](https://github.com/ad-freiburg/loom/issues/44#issuecomment-5681272160): “This is expected behavior, the `topo` tool is not deterministic.” Issue closed; no upstream fix or deterministic-mode guarantee is established by that response.
4. **Plausible mechanism, not a proven root-cause fix.** The issue reporter traced pointer-ordered `std::set<Node*>` iteration and equal-distance candidate/tie decisions during segment collapse. Memory allocation order may affect candidate selection. A geometric tie-breaker patch reduced but did not remove variability; do not cite that experiment as a validated correction.
5. **Present fork's pipeline.** `src/schematic/pipeline.py` computes layout IDs from input data, LOOM commit setting and stage arguments, stores whole sets, and has a force-rebuild path that can replace a stored set **under the same input-derived ID**. That ID is **not a content fingerprint of optimized geometry**. Therefore a matching layout ID alone cannot prove that two outputs or screenshots are identical.

## The current cartographic proof is different from a full `topo` pipeline

- Draft PR #6's native workflow builds LOOM and runs **`loom → octi`**, intentionally **skipping `topo`**. Do not describe that proof as a test showing `topo` is deterministic or harmless. It verifies the corrected projection and its current, restricted candidate graph.
- `bin/mjourney-multiline-proof` retains `*.input.geojson`, `*.loom.geojson`, `*.octi.geojson`, and `*.audit.json`. Its native acceptance checks currently include **undirected per-line station adjacency**, distinct station IDs, line-label set, ordered stage domains, and at least **99.5% length-weighted octilinearity** at ±1°.
- The native acceptance gate can reject meaningful topology loss: PR #4's 27-connection experiment lost the authored `eq46 → eq47` station adjacency and was rejected; the narrowed 25-edge variant passed its gates. **A successful solver exit is not equivalent to an accepted research network.**
- Limits of the current proof: the adjacency comparison is deliberately *undirected*; `identities` compares a set of **display labels**; stage review checks displayed ordinal order, not complete research semantics; and stage `hash` values hash raw JSON, including potentially transient IDs. These are useful proof-level checks, but **not yet a complete candidate certificate for a production authoring import or a future `topo` run**.
- CI uploads the intermediate outputs as build artifacts with **14-day retention**. This is useful diagnostic capture, not durable preservation of an approved map. The native workflow clones a branch head of `sss2808/loom` and records the resulting commit; a future accepted artifact must explicitly pin that exact SHA rather than assume later rebuilds use it.
- **Do not conflate** the successful 23-station/6-line proof with complete source coverage: its fixture derives from a canonical 67-moment/87-relation journey across ten ordinal stages. The current proof displays a reviewed subset (23 stations, 25 authorized connections, five represented stages) and must not invent missing transfers to improve the metro shape.

## Required semantic invariants: candidate versus source

Create a canonical, privacy-reviewed *source manifest* **before optimization**, for the selected cartographic projection. These checks distinguish source truth from optimization helpers:

| Gate | Required validation | Failure treatment |
| --- | --- | --- |
| Station identities | Exact set and cardinality of selected canonical `station_id` values; no duplicated, omitted, renamed, or fabricated source stations. Geometry-only LOOM helper vertices remain distinct from research stations. | Reject |
| Line identities | Compare stable **line IDs** and ordered membership where authored, not only readable labels/colors. Validate the set of lines on **each approved source connection**. | Reject |
| Connectivity | Compare station-to-station **per-line** adjacency after collapsing only geometry-only helper vertices, with both missing and added connections reported. Shared-corridor occupancies must remain intentional. | Reject |
| Direction and provenance | Keep the **directed** original relation and its `sourceEdgeId` in a separate immutable manifest. Compare each rendered traversable link to its approved source edge(s), even when the metro geometry is undirected. The current undirected graph check alone cannot prove direction. | Reject unsupported connectivity; report orientation/provenance separately |
| Stages and layers | Verify each selected station's authored stage/layer fields, ordinal stage ordering and no undesired migration across stage domains. Check the full source manifest independently of what is visible. | Reject |
| Route semantics | Explicitly distinguish approved candidate customer pathways, organizational/activity branches, dependencies and lifecycle-return relationships. Neither shared stage nor shared category establishes permission to invent a route or transfer. | Reject |
| Geometry | Verify original solver polylines and track order, nonzero lengths, finite projected coordinates and length-weighted octilinearity. Use exact `schematic.crs` Mercator transforms. | Reject malformed or out-of-tolerance candidate; do not repair semantics by drawing guessed elbows |
| Labels and camera | Separate human legibility, collisions, filter focus, Fit, fullscreen and mobile-scale tests from semantic provenance. Zero labels dropped or a 99.98% octilinearity result does **not** prove visual quality. | Review before presentation/release |

**Important:** The definition of a valid track is the *approved cartographic projection of the authored graph*, not every original relationship. A dependency or lifecycle return does not automatically become a passenger-like edge. The validation must compare against the frozen selected projection plus separately preserved canonical provenance. A changed helper vertex ID or slightly different bend is not a semantic violation.

## Preservation and comparison protocol

For each input candidate and each solver attempt, retain an **immutable, versioned** evidence bundle. A practical suggested shape is:

```text
layout-candidates/<candidate-id>/
  source-manifest.json                 # canonical station/line/edge/stage IDs and hashes
  00_adapter-input.geojson            # exact geometry sent to LOOM
  01_topo.geojson                     # ONLY if topo is explicitly enabled
  02_loom.geojson
  03_octi.geojson
  accepted-render.svg                 # only if accepted
  audit.json                          # gates, pass/fail and precise changed IDs
  manifest.json                       # provenance, tool versions, options and file digests
```

The stage numbering above is descriptive for this adapter. Preserve the original Legible Cities pipeline's `00_gtfs2graph → 01_topo → 02_loom → 03_octi` names when operating on a genuine GTFS feed; do **not** fabricate a `gtfs2graph` stage for research data.

Minimum manifest fields: source fixture/version and SHA-256; adapter revision/commit; exact Git SHA for the LOOM fork/upstream and compilation details; OS/architecture/compiler/solver backend; `topo` enabled/disabled and flags; `loom`/`octi` flags; the exact input bytes hash; each saved stage's raw-content SHA-256; semantic graph fingerprint; accepted/rejected status and reasons; identity counts; timestamp; reviewer/approval state. Synthetic Web Mercator anchor is **diagram geometry**, never physical research geography.

Use **two fingerprints**: (a) raw file SHA-256 for identifying exact retained bytes; (b) stable, sorted semantic representation of canonical stations, normalized endpoints, line IDs and per-edge ordered membership (and, separately, source direction/source-edge IDs) for provenance comparisons. Explicitly exclude transient LOOM pointer IDs from the semantic fingerprint. Record coordinates/geometry with a stated tolerance for geometric difference reports, while never using a coordinate tolerance to excuse a change in source identity or connection. Keep ordered track offsets where their order is a meaningful part of the output.

Retain **rejected candidates**, their failure diffs and originating source inputs, including the 27-edge `eq46 → eq47` regression. A rejected candidate must never be silently promoted by a seed fallback. Separate `solver_attempted`, `solver_accepted`, `fallback_used` and `presented_artifact_id`.

An input-derived cache/layout ID is not enough to reproduce a map. For an approved screenshot, viewer or portfolio exhibit, pin the **actual accepted output files and digests**. Rebuilding on another machine produces a new candidate requiring another audit, even with identical flags. Protect accepted artifacts from `force` replacement; use immutable snapshots or content-addressed versioning. GitHub Actions artifacts with 14-day expiration are insufficient for long-lived approved maps.

## Suggested reproducibility experiment and automated gates

**Phase A — current native `loom → octi` proof (no `topo`):**

1. Freeze the canonical selected projection, adapted GeoJSON, exact binary commit and command-line options.
2. Run the same input several times (suggest ten, consistent with upstream's test), saving **each** stage rather than comparing only the final screenshot.
3. Compare raw digests **and** semantic fingerprints; report station sets, per-line membership/adjacency differences, stage ordering, angle fractions and geometry deltas. Geometric differences alone do not fail the semantic gate.
4. Treat every solver candidate independently. If one fails any mandatory gate, record it as rejected; never present fallback seed geometry as an accepted native run.

**Phase B — optional experimental `topo` enablement:**

1. Introduce `topo` only in a separately named test mode with saved `adapter-input → topo → loom → octi` artifacts. Never turn it on implicitly in the product or portfolio.
2. Run repeated identical inputs on the intended runner. Compare *after every stage* to identify the first structural difference. Compare at least Linux/native and, if macOS is in the intended authoring environment, macOS/native. A stable ten-run sample does **not** establish a guarantee.
3. Reject if `topo` merges two research stations, drops/introduces approved source adjacency, alters an approved line occupancy, or invalidates required source IDs; accepting topology aggregation should require an explicit **source-preserving** mapping with demonstrated evidence.
4. Add negative fixtures: one lost approved adjacency, one added transfer, one duplicated station, one line-membership change, one stage regression, and a geometry-only helper-ID reshuffle that **passes** the semantic gate.
5. Surface a machine-readable per-candidate audit in exact-head CI with explicit test execution. No silent successful fallback, and no release implication from a green geometry/projection test alone.

**Phase C — accepted-map preservation:**

- Save accepted input/stage/output bundle with persistent retention, immutable content digest and human review, then link the approved viewer to that artifact ID.
- Render, focus and labels are reviewed separately; no engine tuning may override source/semantic gates to attain a more cinematic shape.
- Validate the entire canonical journey and any alternate scenario **separately** before claiming multi-scenario compatibility.

## Recommended follow-up, ordered

1. **Now:** Preserve the existing restriction against `topo` in the 23-station proof; keep its source-adjacency rejection logic and intermediate files. Treat PR #6's exact Mercator correction as a separate geometric fix, not a resolution of topology nondeterminism.
2. **Next:** Extract a reusable **canonical semantic fingerprint + validator** from the proof into the adapter, comparing stable line IDs and memberships and preserving directed source-edge provenance. Extend the native audit output and add negative regression fixtures.
3. **Then:** Make durable candidate archival explicit, including exact LOOM build SHA, platform and stage files, and distinguish input-cache identity from immutable output identity. Replace or supplement 14-day CI retention for *accepted* outputs.
4. **Only if needed:** Evaluate `topo` in a sandboxed repeated-run matrix, or adopt carefully constrained source-aware topology operations; do not assume arbitrary geographic track merging makes sense for research journeys.
5. **Finally:** Evaluate network composition, transfer/branch aesthetics, shared-line spacing and label placement on **accepted** source-backed outputs. Those remain different from the corrected coordinate projection and from the nondeterminism question.

## References

- [Original Legible Cities architecture — layout storage, nondeterminism and stage contracts](ARCHITECTURE.md)
- [Original Legible Cities README — preservation policy and LOOM pipeline](../README.md)
- [Upstream LOOM issue #44 — same-input topology variation, tests and hypothesis](https://github.com/ad-freiburg/loom/issues/44)
- [LOOM maintainer response — expected behavior](https://github.com/ad-freiburg/loom/issues/44#issuecomment-5681272160)
- [Local graph-comparison test `tests/test_loom.py::_as_graph`](../tests/test_loom.py)
- [Local pipeline `src/schematic/pipeline.py`](../src/schematic/pipeline.py)
- [23-station proof `bin/mjourney-multiline-proof`](../bin/mjourney-multiline-proof)
- [Native projection workflow `.github/workflows/mjourney-mercator-projection.yml`](../.github/workflows/mjourney-mercator-projection.yml)
- [Projection regression tests](../tests/test_mjourney_projection.py)

**Boundary:** This is a research/audit record, not a statement that the completed full journey has passed these gates. No change here authorizes changing the canonical 67-moment/87-relation source, shipping a Spatial mode, merging draft PRs, or publishing the portfolio.
