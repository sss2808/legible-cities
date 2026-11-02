# M-Journey P0a source authority certificate

**Status:** implemented in isolated draft PR #10, not merged, deployed, or approved for native geometry. This is the source-integrity prerequisite defined in the [V8 plan](MJOURNEY_V8_ARCHITECTURE_AND_GEOMETRY_PLAN_2026-11-02.md). The canonical 67-moment / 87-relation research fixture and V7 visualization implementation are unchanged.

## Scope of source authority

- Canonical fixture: \`fixtures/mjourney/equipment-sanitized-v1.json\`.
- Exact frozen baseline: \`fixtures/mjourney/equipment-source-certificate-lock-v7.json\` pins the current file SHA-256, normalized source-projection SHA-256, 67/87/10/7 canonical totals, and the selected 59-moment/68-relation/11-route projection.
- Source adapter: \`src/schematic/mjourney_source_integrity.py\`, independent of UI and optimizer.
- Source-only CLI: \`bin/mjourney-source-certificate\`, temporarily reading the exact current \`ROUTES\` from \`bin/mjourney-system-network\` so the source certificate cannot silently drift from the V7 renderer's selected chains.
- Tests: \`tests/test_mjourney_source_integrity.py\`; CI: \`.github/workflows/mjourney-v8-p0a-source-certificate.yml\`.

This certificate is a **frozen technical provenance baseline for the existing sanitized research fixture**, not proof that the authored journey alternatives are validated participant behavior. The candidate A&E/EPC and direct-customer-led pathways and nine activity chains remain the V7 display interpretation. It does not authorize new stations, customer personas, physical travel, timed movements, fabricated transfers, or relationships.

## Three different identities

1. **Source bytes:** SHA-256 of the exact canonical source file. A label/edit/whitespace change must prompt deliberate review rather than self-certifying from whatever input happens to be present.
2. **Source semantics:** Stable sorted JSON projection of canonical moment IDs, authored stage and research layer IDs, all directed source-edge IDs/from/to/kind, selected route IDs and their ordered source-edge/station chains, and exact per-connection route memberships. The manifest hash excludes geometry, readable station labels, colors and unstable LOOM node pointers.
3. **Graph structure:** Stable normalized station IDs, line IDs and unordered per-line station adjacencies, collapsing only geometry-only helper vertices. Original source direction remains stored separately and is **not** inferred from octilinear line geometry.

The immutable source authority requires all three to be interpreted correctly. Graph geometry alone cannot attest that a source direction or a visual line label represents a real customer action.

## Strict pre-solver gate

\`validate_projection_graph(graph, manifest, require_source_edge_ids=True)\` requires:

- Exact set and cardinality of canonical station IDs with no duplicates.
- Exact source station stage/layer membership and all selected source-edge IDs.
- Exactly one sourceEdgeId per displayed original research connection; each projected edge retains the original directed endpoints.
- Exact **set of stable route IDs per source edge**; no new/lost route occupancy, stations or source connections.
- Exact station-to-station per-line track adjacency after ignoring synthetic geometry-only helper IDs.
- Explicit exception for which links can be visual tracks: sequence, branch, convergence and handoff. Dependencies and lifecycle returns are not authorized automatically.

**Important boundary:** The source fixture does not author an ordered left-to-right slot number for parallel route strokes. The validator checks unordered membership IDs, not an invented design-time stroke order. LOOM may legitimately reorder the strokes. Its solved track order must be audited separately in P1, including unintended flips at junctions. The route's **directed order of source edges** is preserved here.

## Post-solver structural review

\`validate_projection_graph(graph, manifest, require_source_edge_ids=False)\` checks:

- Canonical stations and stable line IDs.
- Station adjacency for each line after collapsing only geometry helper vertices.
- Available stage/layer source fields for contradictions.

It deliberately reports \`sourceEdgeProvenanceVerified=false\` and \`directedSourceAuthority=frozen_manifest_only\`. A solver may insert intermediate geometry vertices or discard arbitrary edge props, so its output cannot be certified as a directed source graph merely by comparing undirected station pairs. A future semantic mapping from accepted solver output back to exact source IDs must be assessed before production acceptance. P0a does not pretend to have solved that mapping.

## Negative controls

The automated suite includes missing edges, fabricated transfer, duplicate station identity, source-directed endpoint reversal, changed route membership, missing/modified stage and layer, disallowed lifecycle relation, altered canonical source record, and stable handling of transient pointer IDs and helper vertices. A separate CI shell test uses a forged GeoJSON transfer and requires the CLI to exit nonzero, then checks the machine-readable rejection audit. Another deliberately changes only a moment label and verifies that the **frozen source byte lock** rejects it even when semantic topology is unmodified.

## Run and output

From repository root with Python 3.12+ and engine installed:

\`\`\`bash
python -m unittest discover -s tests -p 'test_mjourney_source_integrity.py' -v
python bin/mjourney-source-certificate --output out/p0a-source-certificate.json
python bin/mjourney-source-certificate \
  --candidate out/source-projection.geojson \
  --output out/p0a-candidate-audit.json
\`\`\`

The optional candidate must be source-provenanced unless \`--post-solver\` is selected. \`--post-solver\` reports structural validity only, never directed source approval. Output includes \`manifest\`, \`canonicalReview\`, \`frozenBaselineReview\`, \`v7SeedReview\`, optional \`candidateReview\`, \`nativeOptimizationAttempted=false\`, and an unambiguous disclaimer.

No native binaries are compiled or invoked by this P0a workflow. The CLI does not create a true immutable layout store, a production import/editor, a solved route-order validator, or V8 optimized geometry. Those are independent P0b/P0c and P1 work packages.

## Remaining review and coordination

- **Source baseline owner approval:** Pinning V7 source bytes detects drift. It does not turn expert-inference fixture content into validated customer interviews. Changes to the frozen authority require an explicit reviewed version bump and new lock, not a silent rewrite.
- **P0b:** Integrate PR #6 exact synthetic Mercator bridge and length-weighted octilinearity into the ten-stage renderer. Do not confuse PR #6's accepted 23-station solver with V7's rejected 59-station native result.
- **P0c:** Implement immutable output bundles, solver-version provenance, stage artifacts, accepted-vs-rejected disposition and no implicit reruns. Input and output hashes are separate.
- **Source-edge reconstruction:** If native LOOM changes source-edge segmentation or introduces helper junctions, retain the frozen manifest and prove a source-aware mapping before attesting directed provenance. The source-only strict validator is not a substitute for that mapping.
- **P0d/P1:** Add explicit full native CI and visualize shared-line ordering and oriented labels in a separate, real geometry acceptance phase.
- **No merge:** PR #10 remains a draft stacked on PR #8. Do not merge it with V7, PR #6 or the actual product without an integration review.
