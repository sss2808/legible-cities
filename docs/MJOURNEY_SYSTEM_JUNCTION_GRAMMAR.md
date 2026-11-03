# Source-faithful junction grammar for M-Journey System

Status: isolated visual experiment on `feature/mjourney-semantic-junction-grammar`; not an accepted M-Journey product rule. Based on the fork's 67-moment public equipment projection and two source-backed vendor-selection focus chains.

## Governing principle

**Geometry does not establish research meaning.** Colored category guides show membership. The source connection records independently establish directed dependencies, branches, sequences and convergences. A visual crossing is not a transfer, even when several colored strokes overlap at the same location.

| Visual situation | Meaning and treatment | Required source authority |
| --- | --- | --- |
| Ordinary station | Canonical research moment; keep native marker | Source moment ID |
| Continuous category guide | Organizational continuity only, **not traversable** | Source category membership |
| Stepped lane / 45° bend | Space management, label clearance or source-approved routing | Geometry only; no new edges or stages |
| Geometric crossing of two tracks | No automatic marker, transfer or adjacency | Do not infer from coordinates |
| Branch origin (larger colored ring) | Two or more source-directed **branch** edges diverge from the same original moment | Original edge IDs and shared source endpoint |
| Reconvergence (larger colored ring) | Two or more **convergence** edges terminate at the same original moment | Original edge IDs and shared target endpoint |
| Category multi-membership | One canonical station may belong to multiple category lines; **not automatically an interchange** | Explicit authored membership (future contract extension) |
| Actual operational transfer | Separate future marker only after source-approved transfer/interchange semantics | Explicit source classification, not geometry |
| Selected relationship overlay | Only source-authorized directed edges, never the same thing as the colored guide rails | Existing edge IDs and direction |

## Equipment validation

The original equipment fixture includes two directed, source-authored alternatives from **eq31 Funding authorized** to **eq37 Vendor selected**:

- `edge44 → edge48 → edge49 → edge50` (A&E/EPC-mediated)
- `edge45 → edge51 → edge52` (direct customer-led)

`edge44` and `edge45` are source-classified `branch` edges from eq31. `edge50` and `edge52` are `convergence` edges into eq37. Thus **eq31 is a branch origin and eq37 is a reconvergence** in this *selected research subgraph*. Neither automatically becomes a transit interchange, a recorded physical handoff, or a fully corroborated customer itinerary. The original graph has no directed `eq31 → eq37` edge.

Current native rendering also draws a category continuity guide directly between those two moments because they are consecutive in the same authored category. When a source-backed relationship focus is selected, that specific *unconnected category shortcut* is visually subordinated to reduce an accidental triangle. The guide remains in the source projection, available to the category filters and restored when focus is reset. No original SVG station position or source relationship is changed.

## Implementation/acceptance

- Detect larger rings **only** when two or more validated source focus sequences share their start and end, diverge to distinct next moments through source `branch` edges, and reconverge from distinct preceding moments through source `convergence` edges.
- Rings appear only while an authored relationship focus is active. Without focus, ordinary canonical station markers remain unchanged.
- Each ring carries `data-moment-id`, `data-junction-role`, and the supporting `data-source-edge-ids`. The inspector explains the marker and evidence caveat.
- Never place a ring merely because SVG lines intersect or a moment belongs to several display categories.
- Render focus edges with their canonical IDs and directions, without changing endpoint positions.
- Detect and subordinate only category guides between the same derived start/end where there is **no** direct source relationship; restore them fully on focus reset.
- Browser-test the exact two equipment markers, their four source edge IDs, no default rings, no markers at ordinary crossings, reversible guide opacity, and preserved 67 moments/87 authored directed edges/60 grouping guides.
- Inspect browser screenshots at 950×520 and 1440×900. A visually attractive ring must not be mistaken for transit interchange. The next iteration can test constrained stepped corridor routing, but cannot invent connectivity to make a more intricate map.

## Not in scope

No second map engine, no global LOOM/Octi solver modification, no new source categories or edges, no Simple view, no implicit passenger route planner, no stage/label coordinate changes, no merge or deployment.