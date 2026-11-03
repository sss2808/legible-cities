# M-Journey stage-demand category corridor experiment

Status: **draft experiment**, not accepted product geometry. Branch \`feature/mjourney-stage-demand-category-corridors\` stacked on [fork PR #19](https://github.com/sss2808/legible-cities/pull/19).

## Why this experiment

The 67-moment equipment System has seven source-backed colored category guides and 87 original directed research relationships. The current V3 station y coordinates use deterministic sine-wave offsets, which make steps but do not explain *why* a corridor gets more or less room. All 60 old category guides already clear nonincident stations by at least 38 **pre-render source-layout units**; adding arbitrary obstacle detours to all 60 would not solve a demonstrated station-collision problem.

This proposal tests a bounded new rule: **allocate the existing vertical space between organizational categories according to authored cross-category relationship demand**, while preserving all stage assignments, ids, category memberships, directed research relations and the native Legible Cities SVG engine.

## Geometry policy

1. **Authoritative data.** Read the existing moments, stages, layer order, and connection records. A connection with endpoints in different categories adds *spacing demand* to the category boundaries between those endpoints for each stage touched. A recorded dependency or feedback relationship can contribute to visibility pressure, **but never becomes a path**.
2. **Stage domains.** Keep every station's original V3 x coordinate, ordinal stage and within-stage ordering. No invented durations, routes or stages.
3. **Fixed overall height.** With seven categories there are six intercategory gaps. Their stage-specific sum remains exactly 624 layout units (6 × 104). Each gap is adjusted within a bounded range based on source demand, redistributing room from quieter to busier boundaries. This is not a proportional measure of research impact or elapsed time.
4. **Purposeful steps.** For every existing same-category segment, connect its *new* stage-guided station endpoints by a central horizontal–45°–horizontal or vertical–45°–vertical bend sequence, never adding a stop or an authored relationship. A small set of fixed fractions changes step placement only if the preferred center placement would collide with another station or cross another category guide.
5. **Fail closed.** For the tested equipment and starter fixtures the new geometry must retain exact canonical IDs/edges and have no proper crossings of different category guides and no nonincident station closer than 30 pre-render layout units. If the constrained candidates cannot satisfy those checks, reject the projection rather than add invented interchanges or hide offending research records.
6. **Native renderer.** Use the original \`schematic.render.render\`, \`animate\` viewer, inspector, source junction overlay, label hierarchy and browser interactions. All seven source-category lines remain organizational, non-traversable rails.

## How to generate both views

The old baseline is unchanged:

\`\`\`bash
python bin/mjourney-preview --system-v3 --html --output out/system-browser.svg
\`\`\`

The opt-in experimental alternative is:

\`\`\`bash
python bin/mjourney-preview --system-v3 --stage-demand-corridors \
  --html --focus-path ae=edge44,edge48,edge49,edge50 \
  --focus-path direct=edge45,edge51,edge52 \
  --output out/system-stage-demand.svg
\`\`\`

No default behavior in the fork or the M-Journey product changes. The variant is strictly guarded by \`--system-v3\`.

## Acceptance and honest limitations

- **Source:** equipment 67 stations, 87 directed research connections, 60 non-traversable category guide edges; same IDs, endpoints, stage order, category identity and provenance. Starter: 19 moments, 18 original relations, 16 guides over 3 channels and 5 stages.
- **Stage geometry:** same x for every moment; bounded redistributed y; 10 ordinal stage domains; no x-order or membership reassignment; identical overall intercategory span.
- **Cartography:** every guide remains H/V/45; no guide crossing or station-clearance violation; native source-backed vendor-selection relationship overlay continues to operate at the newly rendered coordinates.
- **Browser:** test 950 × 520 and 1440 × 900 views; capture baseline and variant overview/focus screenshots, compare label hierarchy, stage alignment, station pointer selection and inspector without viewport overflow.
- **Review:** consider whether the source-demand spacing produces *purposeful* steps and clearer quiet/complex corridors. **No visual approval is inferred from a green test**; no shared corridors or interchanges are manufactured.
- **Non-goals:** this is not a global metro optimizer, a network analysis tool, an inferred operational transfer model, a new category-membership ontology, a camera/zoom redesign, or a user-facing product release. All source graph and evidence semantics remain independent of visual geometry.

Future work should use evidence from the screenshot A/B and measurable label/track clearance to select which spacing strategy deserves further development, rather than adding another layer of decorative CSS.
