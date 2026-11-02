# Original Legible Cities schematic SVG references

These are the **six actual SVG drawings supplied by the M-Journey owner** for cartographic engineering comparisons, preserved as editable, inspectable SVG source on the unmerged development branch.

They are **reference networks**, not M-Journey research records, product assets, or permission to infer customer movements from metro services. They have not been incorporated into the portfolio or M-Journey product. For interpretation, see the [six-network structural audit](../../docs/MJOURNEY_ATLAS_SHAPE_REFERENCE_AUDIT_2026-11-02.md) and the [LA Metro REA browser-state analysis](../../docs/MJOURNEY_REA_LA_METRO_DEEP_DIVE_2026-11-02.md).

| SVG source | Main design question | Relative priority |
| --- | --- | --- |
| [cdmx-metro.svg](cdmx-metro.svg) | How are multiple distributed interchanges and intersecting routes composed without a single dominant trunk? | First |
| [sf-muni-metro.svg](sf-muni-metro.svg) | How do numerous continuous routes share a track while keeping line offsets and station labels legible? | First |
| [chicago-l.svg](chicago-l.svg) | What makes angular corners, concentrated junctions and genuine cyclic transit paths readable? | Second; never infer a customer loop |
| [nyc-subway.svg](nyc-subway.svg) | How does the renderer behave under extreme shared-corridor and station-label density? | Later stress test |
| [trimet-max.svg](trimet-max.svg) | Where does a centralized shared hub become too crowded, and how can outbound branches retain clarity? | Counterexample |
| [septa-regional-rail.svg](septa-regional-rail.svg) | How does a radial network behave when many route identities share similar colors? | Counterexample |

## Provenance and safe use

- **Original publisher:** [Legible Cities Atlas](https://richc117.github.io/legible-cities/atlas/), by `richc117`; generated schematic rail maps from transit-provider data. The files in this folder are **owner-uploaded source exports**, not drawings created for M-Journey.
- **Attribution:** Retain the original SVG `<title>`, route-group names, colors and original generated path geometry. The atlas is the source of the visual implementation; transit labels and paths refer to actual agencies, not M-Journey.
- **License:** The Legible Cities repository's [LICENSE](../../LICENSE) governs code in this fork. SVG-generated output and underlying agency datasets may have separate rights/terms; confirm applicable reuse permissions before redistributing these assets in an independent portfolio or commercial product. They are committed here for code/design comparison only.
- **Data caveat:** Generated `data-src`/`data-dst` and `data-node` keys may be transient renderer identifiers, not durable external station IDs. Do not copy them into the M-Journey research fixture.
- **Integration boundary:** Only borrow schematic design and rendering techniques. Never import real train/timetable/date/passenger functionality into the customer journey.

## Tests to run against these references

1. Compare line identity, path continuity, joined caps and 0°/45°/90° bends, without requiring every corner to be curved.
2. Measure adjacent stroke clearance through shared corridors and inspect ordering at intersections.
3. Check labels against track and stage-heading collisions at desktop and mobile viewports.
4. Test source-backed systems route selection with single and multiple line subsets, content-aware Fit, and zoom.
5. Preserve canonical source station and relationship identities; reject LOOM output that introduces or removes research connections.

These SVGs are **reference evidence, not a target topology**. The M-Journey diagram must derive its shape from authorized research relationships.
