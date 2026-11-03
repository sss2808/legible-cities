/* M-Journey System label hierarchy. Presentation only; no station movement,
 * synthetic connections, inferred chronology or permanent graph edits.
 * Uses audited key/decision flags, native projected station coordinates,
 * and browser-measured labels to reduce clutter at portfolio width.
 */
(() => {
  "use strict";
  const model = window.__mjourneyResearchViewer;
  if (!model) return;
  const {data, svg, stage, morePanel, moments, positions} = model;
  const picker = document.getElementById("mj-moment-picker");
  const focusPicker = document.getElementById("mj-focus-select");
  const nativeLabels = svg.querySelector("#linear-labels");
  const stageStrip = document.getElementById("mj-stage-strip");
  const tools = morePanel.querySelector(".mj-research-tools");
  if (!tools || !stageStrip) return;
  const sourceRank = new Map(data.canonical.moments.map((m, i) => [m.id, i]));

  const controls = document.createElement("div");
  controls.id = "mj-label-controls";
  controls.setAttribute("role", "group");
  controls.setAttribute("aria-label", "Map label detail");
  const options = [
    {id: "key", label: "Key labels"},
    {id: "more", label: "More labels"},
  ];
  const buttons = new Map();
  for (const option of options) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = option.label;
    btn.setAttribute("aria-pressed", String(option.id === "key"));
    btn.setAttribute("data-label-density", option.id);
    controls.appendChild(btn);
    buttons.set(option.id, btn);
  }
  tools.appendChild(controls);

  const layer = document.createElement("div");
  layer.id = "mj-readable-labels";
  layer.setAttribute("aria-hidden", "true");
  stage.appendChild(layer);
  let mode = "key";
  let selected = "";
  let focusedStageId = "";
  let scheduled = false;
  let placedIds = [];

  function coords(mid, ctm, stageBox) {
    const point = positions.get(mid);
    if (!point) return null;
    const p = svg.createSVGPoint();
    p.x = point.x; p.y = point.y;
    const screen = p.matrixTransform(ctm);
    return {x: screen.x - stageBox.left, y: screen.y - stageBox.top};
  }
  function priority(m) {
    // The ordering comes from source-authored metadata, not SVG topology.
    return (m.decision ? 3 : 0) + (m.key ? 2 : 0);
  }
  function candidates() {
    const ids = [], visited = new Set();
    const add = id => {
      if (moments.has(id) && !visited.has(id)) { ids.push(id); visited.add(id); }
    };
    if (selected) add(selected);
    const active = focusPicker ? focusPicker.value : "";
    // The source-authored fork and reunion matter even before any explicit
    // focus is selected. This is label priority, never a new research edge.
    if (!active) for (const path of data.focusSequences || []) {
      add(path.momentIds[0]);
      add(path.momentIds[path.momentIds.length - 1]);
    }
    const activePaths = data.focusSequences.filter(f =>
      f.id === active || active === "all");
    // Mark the source-backed branch and shared outcome before filling the rest.
    for (const path of activePaths) {
      add(path.momentIds[0]);
      add(path.momentIds[path.momentIds.length - 1]);
    }
    // A selected operational stage prioritizes its own source-keyed decisions
    // without claiming these belong to one directed customer pathway.
    if (focusedStageId) {
      const stageMembers = data.canonical.moments
        .filter(m => m.stageId === focusedStageId)
        .sort((a, b) => priority(b) - priority(a)
          || sourceRank.get(a.id) - sourceRank.get(b.id));
      for (const m of stageMembers) add(m.id);
    }
    for (const path of activePaths)
      for (const mid of path.momentIds) add(mid);
    // Preserve stage coverage in overview when space allows.
    for (const stage of data.canonical.stages) {
      const members = data.canonical.moments.filter(m => m.stageId === stage.id)
        .sort((a, b) => priority(b) - priority(a)
          || sourceRank.get(a.id) - sourceRank.get(b.id));
      if (members.length) add(members[0].id);
    }
    const rest = [...data.canonical.moments].sort((a, b) =>
      priority(b) - priority(a)
        || sourceRank.get(a.id) - sourceRank.get(b.id));
    for (const m of rest) add(m.id);
    return ids;
  }
  function intersects(a, b, pad = 4) {
    return a.left < b.right + pad && a.right + pad > b.left
      && a.top < b.bottom + pad && a.bottom + pad > b.top;
  }

  function redraw() {
    scheduled = false;
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    const frame = stage.getBoundingClientRect();
    const safe = 8;
    if (frame.width < 1 || frame.height < 1) return;
    layer.replaceChildren();
    placedIds = [];
    // The native label placer remains untouched and can still restore all
    // labels if an independent future detailed-map presentation needs them.
    // We deliberately show only clear, >=11px HTML callouts in this System
    // portfolio projection, using their canonical source labels.
    if (nativeLabels) nativeLabels.setAttribute("aria-hidden", "true");
    const maxVisible = Math.min(
      mode === "key" ? (frame.width < 1100 ? 14 : 26) : (frame.width < 1100 ? 23 : 42),
      Math.max(5, Math.floor(frame.width / (mode === "key" ? 56 : 40)))
    );
    const occupied = [];
    // Read only the already-rendered decorative Moment markers and approved
    // source-branch endpoint rings. Do not move a station or invent topology.
    // Labels must also clear unrelated station disks, not just other labels.
    const stations = [...svg.querySelectorAll(
      '#mj-cartographic-markers circle[data-source-moment-ref], ' +
      '#mj-cartographic-source-branch circle[data-source-junction-ref]')]
      .map(mark => {
        const id = mark.dataset.sourceMomentRef || mark.dataset.sourceJunctionRef;
        const point = svg.createSVGPoint();
        point.x = Number(mark.getAttribute('cx'));
        point.y = Number(mark.getAttribute('cy'));
        const p = point.matrixTransform(ctm);
        return {id, x: p.x - frame.left, y: p.y - frame.top,
          r: Number(mark.getAttribute('r')) * Math.hypot(ctm.a, ctm.b) + 2};
      });
    const coversOtherStation = (box, id) => stations.some(s => {
      if (s.id === id) return false;
      const dx = Math.max(box.left - s.x, 0, s.x - box.right);
      const dy = Math.max(box.top - s.y, 0, s.y - box.bottom);
      return dx * dx + dy * dy < s.r * s.r;
    });
    const stripBox = stageStrip.getBoundingClientRect();
    const reservedTop = Math.max(0, stripBox.bottom - frame.top + 5);
    const maxWidth = Math.min(frame.width - 2 * safe, frame.width < 1100 ? 112 : 128);
    for (const mid of candidates()) {
      if (placedIds.length >= maxVisible) break;
      const moment = moments.get(mid);
      const at = coords(mid, ctm, frame);
      if (!at || !Number.isFinite(at.x) || !Number.isFinite(at.y)) continue;
      const label = document.createElement("span");
      label.className = "mj-readable-label" + (mid === selected ? " mj-selected-label" : "");
      label.setAttribute("data-moment-id", mid);
      label.setAttribute("title", moment.label);
      label.textContent = moment.label;
      layer.appendChild(label);
      label.style.maxWidth = maxWidth + "px";
      const measure = label.getBoundingClientRect();
      const width = Math.min(maxWidth, Math.ceil(measure.width));
      const height = Math.ceil(measure.height);
      const choices = [
        [at.x - width / 2, at.y - height - 12],
        [at.x - width / 2, at.y + 14],
        [at.x + 12, at.y - height / 2],
        [at.x - width - 12, at.y - height / 2],
      ];
      let placed = false;
      for (const [cx, cy] of choices) {
        const left = Math.round(cx), top = Math.round(cy);
        const box = {left, top, right: left + width, bottom: top + height};
        if (box.left < safe || box.right > frame.width - safe
            || box.top < reservedTop || box.bottom > frame.height - safe
            || occupied.some(other => intersects(box, other))
            || coversOtherStation(box, mid)) continue;
        label.style.left = left + "px";
        label.style.top = top + "px";
        occupied.push(box);
        placedIds.push(mid);
        placed = true;
        break;
      }
      if (!placed) label.remove();
    }
    layer.setAttribute("data-visible-count", String(placedIds.length));
  }
  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(redraw);
  }
  for (const [name, button] of buttons) {
    button.addEventListener("click", () => {
      mode = name;
      buttons.forEach((b, k) => b.setAttribute("aria-pressed", String(k === mode)));
      schedule();
    });
  }
  if (focusPicker) focusPicker.addEventListener("change", schedule);
  if (picker) picker.addEventListener("change", schedule);
  window.addEventListener("mjourney:selection", event => {
    selected = event.detail && event.detail.momentId || "";
    schedule();
  });
  window.addEventListener("mjourney:stage-focus", event => {
    focusedStageId = event.detail && event.detail.stageId || "";
    schedule();
  });
  window.addEventListener("resize", schedule);
  const observer = new ResizeObserver(schedule);
  observer.observe(stage);
  observer.observe(svg);
  schedule();

  window.__mjourneyLabels = Object.freeze({
    visibleIds: () => placedIds.slice(),
    currentDensity: () => mode,
    currentStageId: () => focusedStageId,
    redraw: redraw,
  });
})();