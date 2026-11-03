/* TM-01b/TM-02: read-only visual review of authored equipment handoffs/returns.
 * The signed source contract and native Legible Cities station positions are
 * authoritative. No category guide, canonical edge, route or transfer changes.
 */
(function (root) {
  "use strict";
  function classify(data) {
    if (!data || data.schema !== "mjourney-system-research-contract/v1" ||
        !data.integrity || data.integrity.passed !== true)
      throw new Error("Semantic review requires a validated source contract");
    const moments = new Map((data.canonical?.moments || []).map(m => [m.id, m]));
    const ids = new Set(), handoffs = [], returns = [];
    for (const e of data.canonical?.relationships || []) {
      if (!e.id || ids.has(e.id) || !moments.has(e.fromId) ||
          !moments.has(e.toId) || e.fromId === e.toId)
        throw new Error("Semantic review source identity mismatch");
      ids.add(e.id);
      const from = moments.get(e.fromId), to = moments.get(e.toId);
      const record = {id: e.id, fromId: e.fromId, toId: e.toId,
        kind: e.kind, crossLayer: from.layerId !== to.layerId};
      if (e.kind === "handoff") handoffs.push(record);
      else if (e.kind === "lifecycle_return") returns.push(record);
    }
    return {handoffs, returns, sourceRelationCount: ids.size,
      sourceMomentCount: moments.size};
  }

  function init(model) {
    if (!model) return null;
    const {data, svg, positions, moments} = model;
    const review = classify(data);
    if (!review.handoffs.length && !review.returns.length) return null;
    const focusSelect = document.getElementById("mj-focus-select");
    if (!focusSelect || !svg ||
        focusSelect.querySelector('option[value="review:handoffs"]')) return null;
    const documentNS = "http://www.w3.org/2000/svg";
    const svgEl = tag => document.createElementNS(documentNS, tag);
    const group = svgEl("g");
    group.id = "mj-semantic-review-edges";
    group.setAttribute("pointer-events", "none");
    group.setAttribute("aria-hidden", "true");
    group.setAttribute("data-visual-role", "source-review-overlay");
    const stations = svg.querySelector("#stations");
    if (stations) svg.insertBefore(group, stations);
    else svg.appendChild(group);

    const defs = svg.querySelector("defs") || svg.insertBefore(svgEl("defs"), svg.firstChild);
    const arrow = svgEl("marker");
    arrow.id = "mj-semantic-review-arrow";
    for (const [name, value] of Object.entries({
      markerWidth: "10", markerHeight: "10", refX: "10", refY: "5",
      orient: "auto", markerUnits: "userSpaceOnUse"}))
      arrow.setAttribute(name, value);
    const tip = svgEl("path");
    tip.setAttribute("d", "M0,0 L10,5 L0,10 Z");
    tip.setAttribute("fill", "#F2B46D");
    arrow.appendChild(tip);
    defs.appendChild(arrow);

    // Reuse the original directed-relationship selector. A new toolbar row
    // would reduce the native compact viewport and crop authored stations.
    const status = document.querySelector(".mj-focus-note");
    if (!status) throw new Error("Original relationship qualification is missing");
    const defaultNote = status.textContent;
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.id = "mj-semantic-review-status";
    for (const [value, name] of [
      ["review:handoffs", "Handoffs (research review, not transfers)"],
      ["review:returns", "Lifecycle return (research review)"],
    ]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = name;
      focusSelect.appendChild(option);
    }
    focusSelect.setAttribute("aria-label",
      "Highlight source relationships or review handoffs and lifecycle return; no approved transit transfers");
    const guides = [...svg.querySelectorAll("#lines path[data-src][data-dst]")]
      .map(path => {
        const parts = (path.getAttribute("d") || "").match(
          /-?\d+(?:\.\d+)?(?:e[-+]?\d+)?/gi) || [];
        const pts = [];
        for (let i = 0; i + 1 < parts.length; i += 2)
          pts.push({x: Number(parts[i]), y: Number(parts[i + 1])});
        return pts;
      }).filter(points => points.length >= 2);
    const router = root.MJourneyCorridorRouter;
    if (review.handoffs.length && !router)
      throw new Error("Source-backed review requires native corridor router");
    const handoffRoutes = review.handoffs.length
      ? router.plan(review.handoffs, positions, guides) : [];
    const byRoute = new Map(handoffRoutes.map(route => [route.id, route]));

    function clearOverlay() { group.replaceChildren(); }
    function render(value) {
      clearOverlay();
      if (value === "review:handoffs") {
        for (const e of review.handoffs) {
          const route = byRoute.get(e.id);
          if (!route || !positions.has(e.fromId) || !positions.has(e.toId))
            throw new Error("Missing source handoff geometry " + e.id);
          const path = svgEl("path");
          path.setAttribute("d", route.path);
          path.setAttribute("data-source-edge-id", e.id);
          path.setAttribute("data-source-from", e.fromId);
          path.setAttribute("data-source-to", e.toId);
          path.setAttribute("data-research-kind", "handoff");
          path.setAttribute("data-review-status", "needs-research-review");
          path.setAttribute("data-cross-layer", String(e.crossLayer));
          path.setAttribute("stroke", "#F2B46D");
          path.setAttribute("stroke-width", "6");
          path.setAttribute("stroke-dasharray", "14 7");
          path.setAttribute("stroke-linejoin", "round");
          path.setAttribute("stroke-linecap", "round");
          path.setAttribute("marker-end", "url(#mj-semantic-review-arrow)");
          path.setAttribute("fill", "none");
          group.appendChild(path);
        }
        status.textContent = review.handoffs.length + " authored handoffs; " +
          review.handoffs.filter(e => e.crossLayer).length +
          " cross layers. Review candidates, not approved transit interchanges.";
      } else if (value === "review:returns") {
        for (const e of review.returns) {
          // A full-width track would falsely imply travel continuity. Instead,
          // mark the source and target of the EXISTING authored recurrence.
          for (const [id, role] of [[e.fromId, "source"], [e.toId, "target"]]) {
            const point = positions.get(id);
            if (!point) throw new Error("Missing lifecycle source station " + id);
            const ring = svgEl("circle");
            ring.setAttribute("cx", String(point.x));
            ring.setAttribute("cy", String(point.y));
            ring.setAttribute("r", "13");
            ring.setAttribute("stroke", "#F2B46D");
            ring.setAttribute("stroke-width", "3");
            ring.setAttribute("stroke-dasharray", "4 4");
            ring.setAttribute("fill", "none");
            ring.setAttribute("data-source-edge-id", e.id);
            ring.setAttribute("data-source-moment-id", id);
            ring.setAttribute("data-return-endpoint", role);
            ring.setAttribute("data-review-status", "authored-recurrence");
            group.appendChild(ring);
          }
        }
        status.textContent = review.returns.length + " authored lifecycle return: " +
          review.returns.map(e =>
            (moments.get(e.fromId)?.label || e.fromId) + " → " +
            (moments.get(e.toId)?.label || e.toId)).join("; ") +
          ". Endpoint markers only, not a transit route or measured duration.";
      } else {
        status.textContent = defaultNote;
      }
    }
    focusSelect.addEventListener("change", () => render(focusSelect.value));
    render("");
    const api = Object.freeze({
      counts: () => ({handoffs: review.handoffs.length,
        crossLayerHandoffs: review.handoffs.filter(e => e.crossLayer).length,
        returns: review.returns.length, stations: review.sourceMomentCount,
        directedRelations: review.sourceRelationCount}),
      state: () => focusSelect.value.startsWith("review:") ? focusSelect.value : "",
      overlaySourceIds: () => [...new Set([...group.children]
        .map(node => node.getAttribute("data-source-edge-id")))],
    });
    root.__mjourneySemanticReview = api;
    return api;
  }

  const api = Object.freeze({classify, init});
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root && root.document && root.__mjourneyResearchViewer)
    init(root.__mjourneyResearchViewer);
})(typeof window !== "undefined" ? window : null);
