/* TM-01c fork-only static cartography. Native 67 moment coordinates, 60 category
 * guides, 87 source relationships, controls, inspector and camera remain owned
 * by the original Legible Cities renderer and earlier M-Journey adapters.
 * Drawn research links are directed analytical overlays, never transfers.
 */
(() => {
  "use strict";
  const model = window.__mjourneyResearchViewer;
  const scene = window.__mjourneyScene;
  if (!model || !scene || document.getElementById("mj-cartography-style")) return;
  const {data, svg, stage, positions, moments, relationships} = model;
  const NS = "http://www.w3.org/2000/svg";
  const mk = tag => document.createElementNS(NS, tag);
  const css = document.createElement("style");
  css.id = "mj-cartography-style";
  css.textContent = `
    :root[data-mjourney-inspector] #lines .line path {
      stroke-width: 12.8px; stroke-linecap: round; stroke-linejoin: round;
    }
    :root[data-mjourney-inspector] .mj-stage-strip { height: 56px; }
    :root[data-mjourney-inspector] .mj-stage-name {
      font-family: system-ui, sans-serif; font-weight: 750;
      font-size: clamp(10px, .86vw, 12.5px); line-height: 1.12;
      padding: 2px 1px 3px; max-height: 42px;
      color: var(--text); letter-spacing: -.012em;
    }
    :root[data-mjourney-inspector] .mj-readable-label {
      font-family: system-ui, sans-serif; font-weight: 660;
      font-size: clamp(11.5px, .91vw, 13px);
      line-height: 1.2;
      text-shadow: 0 1px 3px var(--bg), 1px 0 3px var(--bg),
        -1px 0 3px var(--bg), 0 -1px 3px var(--bg);
    }
    :root[data-mjourney-inspector] #mj-static-cartography-note {
      position: absolute; left: 1.25rem; bottom: .48rem;
      z-index: 5; max-width: min(82%, 570px); pointer-events: none;
      padding: .3rem .45rem; border-radius: .25rem;
      color: var(--text); background: color-mix(in srgb,var(--bg) 84%, transparent);
      font: 600 10.5px/1.25 system-ui, sans-serif;
      letter-spacing: .005em; opacity: .84;
    }
    :root[data-mjourney-inspector] .mj-cartography-tags {
      position: absolute; inset: 0; pointer-events: none; z-index: 5;
      overflow: hidden;
    }
    :root[data-mjourney-inspector] .mj-cartography-tag {
      position: absolute; box-sizing: border-box;
      font: 700 11px/1.2 system-ui, sans-serif;
      white-space: nowrap; color: var(--text);
      border-left: 4px solid var(--line-color);
      padding: .16rem .33rem; border-radius: 2px;
      background: color-mix(in srgb,var(--bg) 91%, transparent);
      box-shadow: 0 1px 4px #0008;
    }
    /* Fit the unmodified native SVG viewBox into a docked desktop inspector.
       Width changes only; never stretch, pan, change the research graph,
       or override the original full-width overview camera. */
    @media (min-width: 1091px) {
      :root[data-mjourney-inspector] .mj-research-workspace #stage > svg {
        width: calc(100% - 32px) !important; height: auto !important;
      }
    }
    @media (max-width: 1080px) {
      :root[data-mjourney-inspector] .mj-stage-name[data-visible-stage] {
        font-size: 0; line-height: 1;
      }
      :root[data-mjourney-inspector] .mj-stage-name[data-visible-stage]::after {
        content: attr(data-visible-stage); display: block;
        font-size: 10px; font-weight: 750; letter-spacing: -.02em;
        line-height: 1.11; white-space: normal;
      }
      :root[data-mjourney-inspector] .mj-cartography-tag { font-size: 10px; }
      :root[data-mjourney-inspector] #mj-static-cartography-note {
        font-size: 10px; max-width: 95%;
      }
    }
  `;
  document.head.appendChild(css);

  // Present the ten actual authored stage names. Compact labels may wrap at
  // existing source-positioned domain widths; no invented timeline or reorder.
  const stageStrip = document.getElementById("mj-stage-strip");
  const originalNames = new Map(data.canonical.stages.map(s => [s.id, s.name]));
  function nameStages() {
    if (!stageStrip) return;
    for (const span of stageStrip.querySelectorAll("[data-stage-id]")) {
      const full = originalNames.get(span.dataset.stageId);
      if (!full) continue;
      span.dataset.visibleStage = full;
      span.title = full;
    }
  }
  if (stageStrip) {
    new MutationObserver(nameStages).observe(stageStrip,
      {childList: true, subtree: true, characterData: true});
    nameStages();
  }

  const originOf = new Map();
  const endOf = new Map();
  // Line termini are *guide* termini. They imply no directed travel or
  // cross-layer interchange, even when an authored research edge crosses one.
  for (const guide of svg.querySelectorAll("#lines .line")) {
    const line = guide.getAttribute("data-line");
    const ins = new Set(), outs = new Set();
    for (const path of guide.querySelectorAll("path[data-src][data-dst]")) {
      outs.add(path.dataset.src); ins.add(path.dataset.dst);
    }
    originOf.set(line, [...outs].filter(id => !ins.has(id)));
    endOf.set(line, [...ins].filter(id => !outs.has(id)));
  }
  const termini = new Set([...originOf.values(), ...endOf.values()].flat());

  // Enlarged read-only station cartography is *decorative* and sits above
  // original native station elements; only the original 67 carry station IDs.
  const marks = mk("g");
  marks.id = "mj-cartographic-markers";
  marks.setAttribute("pointer-events", "none");
  marks.setAttribute("aria-hidden", "true");
  for (const moment of data.canonical.moments) {
    const p = positions.get(moment.id);
    if (!p) throw new Error("Missing canonical station " + moment.id);
    const layer = data.canonical.categories.find(c => c.id === moment.layerId);
    const terminal = termini.has(moment.id);
    const junction = moment.id === "eq31" || moment.id === "eq37";
    const halo = mk("circle");
    halo.setAttribute("cx", p.x); halo.setAttribute("cy", p.y);
    halo.setAttribute("r", terminal ? 10.1 : 7.35);
    halo.setAttribute("fill", "#f8f1e8");
    halo.setAttribute("stroke", junction ? "#f7c17a" : "#1c1613");
    halo.setAttribute("stroke-width", junction ? 3.7 : 3.2);
    halo.setAttribute("data-source-moment-ref", moment.id);
    if (terminal) halo.setAttribute("data-guide-terminus", "true");
    if (layer) halo.setAttribute("data-layer-ref", moment.layerId);
    marks.appendChild(halo);
  }
  svg.appendChild(marks);

  const sourceById = new Map(relationships.map(r => [r.id, r]));
  const routesById = new Map(scene.corridorRoutes().map(r => [r.id, r]));
  const prescribed = (data.focusSequences || []).filter(f =>
    f.sourceEdgeIds.every(id => {
      const e = sourceById.get(id), route = routesById.get(id);
      return e && route && positions.has(e.fromId) && positions.has(e.toId);
    }));
  // Use only the two already-authored A&E and direct research paths. No graph
  // inference, shared-station transfer grammar, or extra 64 cross-layer edges.
  const branch = mk("g");
  branch.id = "mj-cartographic-source-branch";
  branch.setAttribute("pointer-events", "none");
  branch.setAttribute("aria-hidden", "true");
  const stationGroup = svg.querySelector("#stations");
  if (stationGroup) svg.insertBefore(branch, stationGroup);
  else svg.appendChild(branch);
  const colors = ["#ffcd96", "#9ad8f4"];
  for (const [index, chain] of prescribed.entries()) {
    const color = colors[index % colors.length];
    for (const id of chain.sourceEdgeIds) {
      const edge = sourceById.get(id), route = routesById.get(id);
      const path = mk("path");
      path.setAttribute("d", route.path);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", color);
      path.setAttribute("stroke-width", "6.5");
      path.setAttribute("stroke-linecap", "round");
      path.setAttribute("stroke-linejoin", "round");
      path.setAttribute("stroke-dasharray", "12 9");
      path.setAttribute("opacity", ".91");
      path.setAttribute("data-source-edge-id", id);
      path.setAttribute("data-source-from", edge.fromId);
      path.setAttribute("data-source-to", edge.toId);
      path.setAttribute("data-research-link-not-transfer", "true");
      branch.appendChild(path);
    }
  }
  const forkIds = new Set();
  for (const chain of prescribed) {
    if (chain.momentIds.length) {
      forkIds.add(chain.momentIds[0]);
      forkIds.add(chain.momentIds.at(-1));
    }
  }
  for (const id of forkIds) {
    const p = positions.get(id);
    const outer = mk("circle");
    outer.setAttribute("cx", p.x); outer.setAttribute("cy", p.y);
    outer.setAttribute("r", "17"); outer.setAttribute("fill", "#211811");
    outer.setAttribute("stroke", "#ffcf8c"); outer.setAttribute("stroke-width", "4");
    outer.setAttribute("data-source-junction-ref", id);
    branch.appendChild(outer);
    const inner = mk("circle");
    inner.setAttribute("cx", p.x); inner.setAttribute("cy", p.y);
    inner.setAttribute("r", "8"); inner.setAttribute("fill", "#f8f1e8");
    inner.setAttribute("data-source-junction-ref", id);
    branch.appendChild(inner);
  }
  const picker = document.getElementById("mj-focus-select");
  // The empty focus value actually shows the source-authored overview fork.
  // Clarify the existing selector without adding another control or route.
  const overviewOption = picker?.querySelector('option[value=""]');
  if (overviewOption && overviewOption.textContent.trim() === "No focus") {
    overviewOption.textContent = "A&E/direct overview";
  }
  const note = document.createElement("div");
  note.id = "mj-static-cartography-note";
  note.textContent = "Colored routes = research categories. Dashed A&E / direct links = authored relationships, not transit transfers.";
  stage.appendChild(note);
  function sync() {
    const defaultFocus = !picker || picker.value === "";
    branch.style.display = defaultFocus ? "" : "none";
    note.hidden = !defaultFocus;
  }
  picker?.addEventListener("change", sync);
  sync();

  // At guide termini, add small source-authored line identifiers where there
  // is actual room. All labels are DOM-measured, and never conceal an earlier
  // moment label or an operational stage header.
  const tags = document.createElement("div");
  tags.className = "mj-cartography-tags";
  tags.id = "mj-cartography-terminus-labels";
  tags.setAttribute("aria-hidden", "true");
  stage.appendChild(tags);
  let shownTags = [];
  let queue = false;
  function redrawTags() {
    queue = false;
    tags.replaceChildren();
    shownTags = [];
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    const rect = stage.getBoundingClientRect();
    const header = stageStrip?.getBoundingClientRect();
    const reservedTop = header ? header.bottom - rect.top + 4 : 48;
    const existing = [...stage.querySelectorAll("#mj-readable-labels .mj-readable-label")]
      .filter(x => x.isConnected)
      .map(x => x.getBoundingClientRect());
    const occupied = existing.map(x => ({left:x.left - rect.left, top:x.top - rect.top,
      right:x.right - rect.left, bottom:x.bottom - rect.top}));
    const intersects = (a, b) => a.left < b.right + 5 && a.right + 5 > b.left &&
      a.top < b.bottom + 5 && a.bottom + 5 > b.top;
    // Prefer late starting guide lines and short existing names; never add
    // a permanent seven-row swimlane title rail.
    const items = [];
    for (const layer of data.canonical.categories) {
      const ids = originOf.get(layer.name) || [];
      for (const id of ids) if (positions.has(id)) {
        const p = positions.get(id);
        items.push({layer, id, p, late: p.x > 450});
      }
    }
    items.sort((a,b) => Number(b.late) - Number(a.late) || a.p.x - b.p.x);
    for (const item of items) {
      if (shownTags.length >= (rect.width < 1080 ? 4 : 7)) break;
      const pt = svg.createSVGPoint(); pt.x = item.p.x; pt.y = item.p.y;
      const pos = pt.matrixTransform(ctm);
      const x = pos.x - rect.left, y = pos.y - rect.top;
      const tag = document.createElement("span");
      tag.className = "mj-cartography-tag";
      tag.textContent = item.layer.name;
      tag.title = item.layer.name + " · starts at " + moments.get(item.id).label;
      tag.style.setProperty("--line-color", item.layer.color);
      tags.appendChild(tag);
      const b = tag.getBoundingClientRect();
      const w = b.width, h = b.height;
      const candidates = [[x + 13,y - h/2], [x - w - 13,y - h/2],
        [x - w/2,y - h - 15], [x - w/2,y + 15]];
      let placed = false;
      for (const [left,top] of candidates) {
        const box = {left,top,right:left+w,bottom:top+h};
        if (left < 7 || box.right > rect.width - 7 || top < reservedTop ||
            box.bottom > rect.height - 28 || occupied.some(o=>intersects(box,o))) continue;
        tag.style.left = left.toFixed(1) + "px";
        tag.style.top = top.toFixed(1) + "px";
        occupied.push(box); shownTags.push(item.layer.name); placed = true;
        break;
      }
      if (!placed) tag.remove();
    }
  }
  function schedule() {
    if (queue) return;
    queue = true;
    requestAnimationFrame(() => requestAnimationFrame(redrawTags));
  }
  window.addEventListener("resize", schedule);
  stage.addEventListener("transitionend", schedule);
  document.getElementById("mj-label-controls")?.addEventListener("click", schedule);
  document.getElementById("mj-moment-picker")?.addEventListener("change", schedule);
  document.getElementById("mj-category-disclosure")?.addEventListener("click", schedule);
  new ResizeObserver(schedule).observe(stage);
  // The readable-label layer repositions labels in its own animation frame.
  // Recheck tag clearance *after* every label layout, not just after controls
  // change: Chromium may resolve fonts/layout later than the first tag pass.
  // Observe only the label layer. Our tag mutations cannot retrigger this
  // observer, so the two-frame placement stays nonrecursive.
  const readableLabels = document.getElementById("mj-readable-labels");
  if (readableLabels) {
    new MutationObserver(schedule).observe(readableLabels, {
      childList: true, subtree: true, attributes: true,
      attributeFilter: ["style", "class"],
    });
  }
  document.fonts?.ready.then(schedule);
  schedule();

  window.__mjourneyCartography = Object.freeze({
    sourceMomentCount: () => moments.size,
    originalResearchEdgeCount: () => relationships.length,
    categoryGuideCount: () => svg.querySelectorAll("#lines path[data-src][data-dst]").length,
    overlayEdgeIds: () => [...branch.querySelectorAll("path[data-source-edge-id]")]
      .map(p => p.dataset.sourceEdgeId),
    visibleLineTags: () => shownTags.slice(),
    markerCount: () => marks.children.length,
    getStageHeadings: () => [...stageStrip.querySelectorAll("[data-stage-id]")]
      .map(n => n.dataset.visibleStage || n.textContent),
    redraw: () => {nameStages(); redrawTags();},
  });
})();