/* System presentation-only stage anchors and source-backed relationship focus.
 * Uses the canonical contract that passed Python source integrity validation.
 * Does not alter native track geometry, stations, stage identity or research.
 */
(() => {
  "use strict";
  const model = window.__mjourneyResearchViewer;
  if (!model) return;
  const {data, svg, stage, morePanel, moments, stages, relationships, positions} = model;
  const NS = "http://www.w3.org/2000/svg";
  const el = (tag, name) => {
    const node = document.createElement(tag);
    if (name) node.className = name;
    return node;
  };
  const svgEl = tag => document.createElementNS(NS, tag);
  const focus = data.focusSequences || [];
  const canonicalRelations = new Map(relationships.map(x => [x.id, x]));

  // Stage headings follow rendered station positions, not a second schematic.
  // Stage domains remain ordinal, never proportional to journey duration.
  const strip = el("div", "mj-stage-strip");
  strip.id = "mj-stage-strip";
  strip.setAttribute("role", "group");
  strip.setAttribute("aria-label", "Authored operational stage sequence");
  stage.prepend(strip);
  const stageLabels = data.canonical.stages.map((item, i) => {
    const node = el("span", "mj-stage-name");
    node.setAttribute("data-stage-id", item.id);
    node.setAttribute("title", item.name);
    node.setAttribute("aria-label", "Stage " + (i + 1) + ": " + item.name);
    node.textContent = item.name;
    strip.appendChild(node);
    return {item, node};
  });

  function updateStageHeaders() {
    const rootCTM = svg.getScreenCTM();
    if (!rootCTM) return;
    const box = stage.getBoundingClientRect();
    const centers = stageLabels.map(({item}, i) => {
      const xs = data.canonical.moments
        .filter(m => m.stageId === item.id && positions.has(m.id))
        .map(m => positions.get(m.id).x);
      if (!xs.length) return NaN;
      xs.sort((a, b) => a - b);
      const center = xs[Math.floor(xs.length / 2)];
      const p = svg.createSVGPoint();
      p.x = center;
      p.y = 0;
      return p.matrixTransform(rootCTM).x - box.left;
    });
    // Empty-stage fallback: interpolate between neighboring anchored domains.
    const width = box.width;
    for (let i = 0; i < centers.length; i++) {
      if (Number.isFinite(centers[i])) continue;
      const leftIndex = centers.slice(0, i).findLastIndex(Number.isFinite);
      const rightIndex = centers.findIndex((n, j) => j > i && Number.isFinite(n));
      if (leftIndex >= 0 && rightIndex >= 0) {
        centers[i] = centers[leftIndex] + (centers[rightIndex] - centers[leftIndex])
          * (i - leftIndex) / (rightIndex - leftIndex);
      } else centers[i] = width * (i + .5) / centers.length;
    }
    stageLabels.forEach(({node}, i) => {
      const center = Math.min(width - 15, Math.max(15, centers[i]));
      const leftSpace = i ? Math.abs(center - centers[i - 1]) : center * 2;
      const rightSpace = i + 1 < centers.length
        ? Math.abs(centers[i + 1] - center) : (width - center) * 2;
      const maxWidth = Math.min(136, Math.max(38, Math.min(leftSpace, rightSpace) * .89));
      node.style.left = center + "px";
      node.style.maxWidth = maxWidth + "px";
      node.style.width = maxWidth + "px";
    });
  }

  // Render only original directed relationships from validated focus sequences.
  // These are research highlights, not approved customer itineraries.
  const overlay = svgEl("g");
  overlay.id = "mj-source-relationships";
  overlay.setAttribute("pointer-events", "none");
  overlay.setAttribute("aria-hidden", "true");
  const stationLayer = svg.querySelector("#stations");
  if (stationLayer) svg.insertBefore(overlay, stationLayer);
  else svg.appendChild(overlay);

  const colors = ["#E9A15E", "#6CB7EA", "#A794E9"];
  const defs = svg.querySelector("defs") || (() => {
    const node = svgEl("defs");
    svg.insertBefore(node, svg.firstChild);
    return node;
  })();
  focus.forEach((item, i) => {
    const marker = svgEl("marker");
    marker.id = "mj-source-arrow-" + i;
    marker.setAttribute("markerWidth", "5");
    marker.setAttribute("markerHeight", "5");
    marker.setAttribute("refX", "4.7");
    marker.setAttribute("refY", "2.5");
    marker.setAttribute("orient", "auto");
    marker.setAttribute("markerUnits", "strokeWidth");
    const tip = svgEl("path");
    tip.setAttribute("d", "M0,0 L5,2.5 L0,5 Z");
    tip.setAttribute("fill", colors[i % colors.length]);
    marker.appendChild(tip);
    defs.appendChild(marker);
  });
  function octilinear(a, b) {
    const dx = b.x - a.x, dy = b.y - a.y;
    const sx = Math.sign(dx), sy = Math.sign(dy);
    const diagonal = Math.min(Math.abs(dx), Math.abs(dy));
    const extra = Math.abs(dx) >= Math.abs(dy)
      ? (Math.abs(dx) - diagonal) / 2
      : (Math.abs(dy) - diagonal) / 2;
    const first = Math.abs(dx) >= Math.abs(dy)
      ? {x: a.x + sx * extra, y: a.y}
      : {x: a.x, y: a.y + sy * extra};
    const second = {x: first.x + sx * diagonal, y: first.y + sy * diagonal};
    const coords = [a, first, second, b];
    const distinct = coords.filter((p, i) => !i || p.x !== coords[i - 1].x ||
      p.y !== coords[i - 1].y);
    return distinct.map((p, i) => (i ? "L" : "M") +
      p.x.toFixed(2) + "," + p.y.toFixed(2)).join(" ");
  }
  function renderFocus(value) {
    overlay.replaceChildren();
    for (const [i, candidate] of focus.entries()) {
      if (value !== "all" && value !== candidate.id) continue;
      for (const edgeId of candidate.sourceEdgeIds) {
        const original = canonicalRelations.get(edgeId);
        if (!original) throw new Error("Unrecognized directed research relation: " + edgeId);
        const from = positions.get(original.fromId), to = positions.get(original.toId);
        if (!from || !to) throw new Error("Missing canonical station for " + edgeId);
        const path = svgEl("path");
        path.setAttribute("d", octilinear(from, to));
        path.setAttribute("data-source-edge-id", edgeId);
        path.setAttribute("data-focus-id", candidate.id);
        path.setAttribute("data-research-kind", original.kind);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", colors[i % colors.length]);
        path.setAttribute("stroke-width", "8");
        path.setAttribute("stroke-linejoin", "round");
        path.setAttribute("stroke-linecap", "round");
        path.setAttribute("opacity", ".95");
        path.setAttribute("marker-end", "url(#mj-source-arrow-" + i + ")");
        overlay.appendChild(path);
      }
    }
  }

  const focusRow = el("div", "mj-focus-tools");
  const focusLabel = el("label", "");
  focusLabel.textContent = "Source relationships";
  focusLabel.htmlFor = "mj-focus-select";
  const select = el("select", "");
  select.id = "mj-focus-select";
  select.setAttribute("aria-label", "Highlight authored research relationship sequence");
  const options = [{value: "", name: "No focus"}];
  for (const item of focus)
    options.push({value: item.id, name: item.id.replaceAll("_", " ")});
  if (focus.length > 1)
    options.push({value: "all", name: "Compare alternatives"});
  for (const item of options) {
    const option = el("option", "");
    option.value = item.value;
    option.textContent = item.name;
    select.appendChild(option);
  }
  focusLabel.appendChild(select);
  focusRow.appendChild(focusLabel);
  const note = el("span", "mj-focus-note");
  note.textContent = "Highlights authored directed edges, not validated travel.";
  focusRow.appendChild(note);
  if (focus.length) {
    const existing = morePanel.querySelector(".mj-research-tools");
    if (existing) existing.appendChild(focusRow);
    else morePanel.prepend(focusRow);
  }
  select.addEventListener("change", () => renderFocus(select.value));

  const resize = new ResizeObserver(updateStageHeaders);
  resize.observe(stage);
  resize.observe(svg);
  window.addEventListener("resize", updateStageHeaders);
  requestAnimationFrame(updateStageHeaders);

  // Testing seam is read-only except deliberately user-driven focus selection.
  window.__mjourneyScene = Object.freeze({
    stageCount: stageLabels.length,
    availableFocusIds: focus.map(x => x.id),
    redrawStages: updateStageHeaders,
  });
})();