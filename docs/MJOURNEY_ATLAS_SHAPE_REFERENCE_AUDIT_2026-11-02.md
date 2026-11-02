# Six-network shape audit for the M-Journey cartographic system

**Date:** 2026-11-02  
**Status:** Additional design reference for [PR #4](https://github.com/sss2808/legible-cities/pull/4); unapproved experimental analysis, not a new M-Journey implementation or evidence of research routes.  
**Provenance:** Six user-provided SVG files exported from Legible Cities: `trimet-max.svg`, `sf-muni-metro.svg`, `nyc-subway.svg`, `septa-regional-rail.svg`, `chicago-l.svg`, `cdmx-metro.svg`. Their content was inspected programmatically and visually. All six source SVGs are now committed under [the Legible Cities reference folder](../references/legible-cities/README.md), with their original generated paths and station/line metadata preserved. See also [LA Metro REA deep dive](MJOURNEY_REA_LA_METRO_DEEP_DIVE_2026-11-02.md).

## Decision

**The six references are useful. LA Metro alone was insufficient for understanding the range of possible network structures.** We have enough *static* geometry examples now; another broad REA browser-capture session is **not** needed before improving the cartographic model.

For immediate visual engineering, prioritize:

1. **CDMX Metro** to study *distributed junctions, crossings, multi-axis topology and balanced network composition*.
2. **SF Muni Metro** to study *continuous multi-line shared corridors, line-offset ordering, branch continuity and labels through parallel tracks*.
3. **Chicago L** to study *large-scale line continuity through concentrated loops/hubs*, but **do not invent a customer lifecycle loop** because a transit map has one.
4. **NYC Subway** only as a *later stress test* for densely shared edges, overlapping stations, and label LOD/camera.
5. **TriMet MAX** as an alternate central-complex plus long outer branch example. This is a useful failure/counterexample case if the map creates a knot instead of a readable hub.
6. **SEPTA Regional Rail** as a *negative shape comparison*: many route identities radiating from shared central territory while using a uniform route color, demonstrating that line count or colors do not by themselves convey research structure.

The shape should emerge from M-Journey's authorized research topology, not be copied from any transit network. Our 10 ordinal stages are not transit geography or elapsed time. Do not force a loop, star, hub, or transfer to imitate a reference.

## Download and inspect the original SVG sources

The following are **actual vector files**, not screenshots or recreated images:

- [Mexico City Metro](../references/legible-cities/cdmx-metro.svg)
- [San Francisco Muni Metro](../references/legible-cities/sf-muni-metro.svg)
- [Chicago L](../references/legible-cities/chicago-l.svg)
- [New York City Subway](../references/legible-cities/nyc-subway.svg)
- [TriMet MAX](../references/legible-cities/trimet-max.svg)
- [SEPTA Regional Rail](../references/legible-cities/septa-regional-rail.svg)

The [reference folder index](../references/legible-cities/README.md) records provenance, priorities and the permitted engineering use. The SVGs retain native `g[data-line]` and path `data-src`/`data-dst` for programmatic geometry studies.

## Parsed SVG inventory

The values below were computed from original SVG markup, not inferred from screenshots. `g[data-line]` is a route group; `path[data-src][data-dst]` defines a rendered source/destination edge. **Shared node pairs** count distinct unordered path endpoint pairs carried by more than one line group. **Junction nodes** are endpoint IDs with undirected degree ≥3 in the SVG path-endpoint graph. This graph can include geometry-only vertices and is *not* a count of author-approved passenger interchanges.

| Attached reference | Route groups | Station markers | Rendered paths | Distinct endpoint pairs | Pairs with multiple route groups | Degree ≥3 graph nodes | Connected components | Cycle rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TriMet MAX | 8 | 159 | 307 | 183 | 93 | 29 | 1 | 24 |
| SF Muni Metro | 7 | 160 | 300 | 166 | 36 | 15 | 1 | 7 |
| NYC Subway | 27 | 402 | 1117 | 471 | 338 | 79 | 2 | 60 |
| SEPTA Regional Rail | 13 | 156 | 230 | 159 | 18 | 11 | 1 | 1 |
| Chicago L | 8 | 144 | 226 | 156 | 39 | 15 | 1 | 10 |
| CDMX Metro | 12 | 165 | 189 | 183 | 6 | 27 | 1 | 17 |

**Method notes:** Counts of paths and circles come from raw XML; graph edges are unique unordered pairs of `data-src`/`data-dst`; `cycle rank = E - V + components`. A cycle in this graph does **not** establish a meaningful research feedback loop. Some network maps contain disconnected service geography, and some metadata endpoints may be geometry-only graph vertices. Full source records and connected edge semantics require source data and approval.

### What the different shapes imply

- **CDMX** has *few* repeated edge pairs shared by multiple line groups (6), but more branching/junction nodes (27) and 17 graph cycles. This is relevant for distributing authored M-Journey organizational handoffs and decision points across multiple stages, rather than forcing all categories onto a shared horizontal path.
- **SF Muni** has 36 shared edge pairs across 7 routes. Its parallel corridors and subsequent divergence are the best case for testing how LOOM arranges offset strokes and how labels avoid them.
- **Chicago** has 39 shared pairs, several concentrated hubs, and obvious large angular route geometry. Useful to judge the bend/label tradeoff, not as evidence that all M-Journey workstreams need a loop.
- **NYC** has 338 multi-route edge pairs across 27 line groups and 402 station circles. This is an *extreme case*: no obligation for our 67-research-moment demonstration to emulate NYC's density; use as an automated label/offset stress reference.
- **SEPTA** has 13 named routes with one dominant common track color, showing that color categories and graph structure are independent choices. Avoid interpreting same-color segments as one meaningful path without line membership.
- **TriMet** has 93 shared pairs and a prominent central connection cluster. Good for spotting excessive hub compression and large whitespace outside the core.

## Academic design principles applicable to M-Journey

The following advice is supported by transit-map/cartographic research, not by the uploaded SVGs alone:

1. **Preserve topology as a hard constraint.** The original station-line graph and authored adjacency must not be altered to produce a prettier picture. If LOOM changes them, reject the solution. [Nöllenburg and Wolff, survey](https://i11www.iti.kit.edu/extra/publications/n-asamm-14.pdf); [KIT hard/soft rules](https://i11www.iti.kit.edu/en/projects/geovis/metro).
2. **Octilinearity is a common rule, not a demand for curved corners.** Traditional diagram angles are 0°, ±45° and 90°. Minimize unnecessary turns and maintain line straightness through interchanges, with clear angular separation around branching nodes. [Survey on Automated Metro Map Layout](https://i11www.iti.kit.edu/extra/publications/n-asamm-14.pdf); [Preference vs performance](https://www.sciencedirect.com/science/article/pii/S1071581916300751).
3. **Treat layout, labels and shared-line ordering as interdependent optimization problems.** A geometrically valid layout can remain visually bad if long research moment labels collide or parallel tracks switch order. Consider candidate text positions and required clearance during placement, not after finalizing paths. [Nöllenburg & Wolff, 2011](https://pubmed.ncbi.nlm.nih.gov/20498505/); [Transit Layout survey, 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7539984/).
4. **Control whitespace and network density.** Large empty margins, extremely tight station clusters and long, low-information spokes are *quality failures*, even with exact 45° geometry. [Automated Metro Layout survey](https://i11www.iti.kit.edu/extra/publications/n-asamm-14.pdf).
5. **Measure user-task performance, not only aesthetic preference.** Octilinearity often helps but is not universally optimal. Test whether actual viewers can identify sequence, route divergence, workstream handoff, dependency and evidence. [Roberts et al., preference versus performance](https://www.sciencedirect.com/science/article/pii/S1071581916300751); [Stott et al., multi-criteria optimization](https://pubmed.ncbi.nlm.nih.gov/21071790/).
6. **Do not apply transit geography constraints literally.** Relative geographic position is important to subway maps, but M-Journey positions are author-defined stage and relationship semantics. Preserve *ordinal stage progression and documented logical grouping*; geographical distortions are irrelevant to this data.

## Targeted next evidence, rather than another broad REA run

### Required before expanding the full System map

- **Source-backed semantic/cartographic specification:** for all 67 moments and 87 relationships, separate immutable research relationships, line memberships, organizational workstreams, ordered stage, validated handoffs, dependencies, non-traversable annotations and feedback. Identify approved continuous lines and shared corridors without inventing personas or transfer events.
- **Actual native LOOM intermediate graph comparison:** for the M-Journey candidate model, inspect the input, `loom`, `octi`, final render and per-line adjacency/offset metrics. For additional layout baselines, compare CDMX and SF Muni intermediate polylines **only if available from the original renderer build**, without reverse-engineering the entire browser again. The user-supplied SVGs already provide final paths and `data-src`/`data-dst` for structural comparisons.
- **Visual/interaction acceptance data:** at 1440×900 and ~390×844, test original-label overlap and hidden labels; stage header continuity; focus on one and two route families; shared-stroke separability; number and severity of bends; absence of misleading transfer dots; fullscreen and Fit bounds. Test actual research-oriented navigation tasks (follow one branch, identify one approved handoff, inspect evidence) rather than just screenshot similarity.

### Optional only after an evidenced gap

- Run targeted REA on **CDMX** for a *multi-hub select/zoom/reframe behavior* not demonstrated by LA, or **Chicago** if an approved *cyclic cartographic route* actually exists. If the original interactive viewer uses the same scripts, the marginal REA benefit is likely low; prioritize the SVG/path comparison first.
- Use NYC as a label-packing stress dataset after a robust M-Journey graph exists. Do not import 27 transit lines as a model of seven workstreams.

## Scope of approval

This document is reference research and acceptance criteria only. It makes **no changes to the M-Journey research fixture, the product, the portfolio, or any map renderer**. The six owner-provided reference SVGs are committed on this **unmerged draft branch** for research and code comparison, not incorporated into the portfolio or product. Check SVG-generated output and agency data reuse permissions before external redistribution. Do not merge or deploy draft PRs from this finding alone.
