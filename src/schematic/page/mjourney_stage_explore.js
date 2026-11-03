/* TM-01c: opt-in, source-preserving desktop exploration of a panoramic map.
 *
 * This adjusts only the CSS presentation of the EXISTING native SVG.
 * It never edits a station coordinate, SVG viewBox, category guide, authored
 * relationship, native renderer geometry, source fixture, or product camera.
 */
(() => {
  "use strict";
  const model = window.__mjourneyResearchViewer;
  if (!model || !window.__mjourneyScene) return;
  const {data, stage, svg, positions} = model;
  if (!stage || !svg || document.getElementById("mj-stage-explore")) return;

  const MIN_WIDTH = 1200;
  const ZOOM = 1.65;
  const sourceViewBox = svg.getAttribute("viewBox");
  const originalTransform = svg.style.transform;
  const originalTransformOrigin = svg.style.transformOrigin;
  const stageMomentXs = new Map(data.canonical.stages.map(s => [
    s.id, data.canonical.moments
      .filter(m => m.stageId === s.id && positions.has(m.id))
      .map(m => positions.get(m.id).x),
  ]));
  const worldXs = [...positions.values()].map(p => p.x);
  const minWorldX = Math.min(...worldXs);
  const maxWorldX = Math.max(...worldXs);
  const stagePicker = document.getElementById("mj-stage-picker");
  let enabled = false;
  let frame = 0;
  let currentStageId = stagePicker?.value || "";

  const ui = document.createElement("div");
  ui.id = "mj-stage-explore";
  ui.className = "mj-stage-explore";
  ui.setAttribute("role", "group");
  ui.setAttribute("aria-label", "Optional enlarged stage exploration");
  const button = document.createElement("button");
  button.type = "button";
  button.id = "mj-stage-explore-toggle";
  button.textContent = "Explore stages";
  button.setAttribute("aria-pressed", "false");
  button.setAttribute("aria-label", "Explore individual stages at larger scale");
  const note = document.createElement("span");
  note.id = "mj-stage-explore-note";
  note.textContent = "Fit shows the complete journey";
  ui.append(button, note);
  stage.appendChild(ui);

  const stageHeadings = [...stage.querySelectorAll(
    "#mj-stage-strip .mj-stage-name[data-stage-id]")];

  function centerForStage(id) {
    const xs = stageMomentXs.get(id);
    if (xs && xs.length)
      return (Math.min(...xs) + Math.max(...xs)) / 2;
    const a = positions.get("eq31");
    const b = positions.get("eq37");
    if (a && b) return (a.x + b.x) / 2;
    return (minWorldX + maxWorldX) / 2;
  }

  function screenX(ctm, worldX) {
    const point = svg.createSVGPoint();
    point.x = worldX;
    point.y = 0;
    return point.matrixTransform(ctm).x;
  }

  function restoreHeadings() {
    for (const node of stageHeadings) {
      node.style.visibility = "";
      node.style.left = "";
      node.style.maxWidth = "";
    }
  }

  function visibleHeadings() {
    if (!enabled) {
      restoreHeadings();
      return;
    }
    const matrix = svg.getScreenCTM();
    if (!matrix) return;
    const bounds = stage.getBoundingClientRect();
    const candidates = stageHeadings.map(node => ({
      node,
      id: node.dataset.stageId,
      x: screenX(matrix, centerForStage(node.dataset.stageId)) - bounds.left,
    })).filter(entry => Number.isFinite(entry.x))
      .sort((a, b) => a.x - b.x);
    const visible = [];
    for (const entry of candidates) {
      if (entry.x < 48 || entry.x > bounds.width - 48) continue;
      const prev = visible[visible.length - 1];
      // Prevent pile-ups of offscreen names at the two clipped edges.
      if (prev && entry.x - prev.x < 98) {
        if (entry.id === currentStageId && prev.id !== currentStageId)
          visible[visible.length - 1] = entry;
        continue;
      }
      visible.push(entry);
    }
    const accepted = new Set(visible.map(entry => entry.id));
    for (const entry of candidates) {
      const node = entry.node;
      const show = accepted.has(entry.id);
      node.style.visibility = show ? "visible" : "hidden";
      if (show) {
        const idx = visible.findIndex(item => item.id === entry.id);
        const leftGap = idx ? entry.x - visible[idx - 1].x : entry.x * 2;
        const rightGap = idx + 1 < visible.length
          ? visible[idx + 1].x - entry.x
          : (bounds.width - entry.x) * 2;
        node.style.left = entry.x + "px";
        node.style.maxWidth = Math.max(58, Math.min(146,
          .86 * Math.min(leftGap, rightGap))) + "px";
      }
    }
  }

  function updatePresentation() {
    // Existing stage header and label logic runs against the *same* native
    // station positions and SVG getScreenCTM, including our CSS zoom.
    window.__mjourneyScene?.redrawStages?.();
    window.__mjourneyLabels?.redraw?.();
    requestAnimationFrame(() => requestAnimationFrame(visibleHeadings));
  }

  function render() {
    frame = 0;
    if (window.innerWidth < MIN_WIDTH) enabled = false;
    if (!enabled) {
      svg.style.transform = originalTransform;
      svg.style.transformOrigin = originalTransformOrigin;
      stage.classList.remove("mj-stage-exploring");
      button.setAttribute("aria-pressed", "false");
      button.setAttribute("aria-label", "Explore individual stages at larger scale");
      button.textContent = "Explore stages";
      note.textContent = "Fit shows the complete journey";
      restoreHeadings();
      updatePresentation();
      return;
    }

    // Reset our own transform before measuring the native, unmodified SVG.
    svg.style.transform = originalTransform;
    svg.style.transformOrigin = originalTransformOrigin;
    const rect = stage.getBoundingClientRect();
    const svgRect = svg.getBoundingClientRect();
    const nativeCTM = svg.getScreenCTM();
    if (!nativeCTM) return;
    const originX = svgRect.left + svgRect.width / 2;
    const targetBase = screenX(nativeCTM, centerForStage(currentStageId));
    const firstBase = screenX(nativeCTM, minWorldX);
    const lastBase = screenX(nativeCTM, maxWorldX);
    const zoomX = base => originX + ZOOM * (base - originX);
    let delta = rect.left + rect.width / 2 - zoomX(targetBase);
    // Bounds keep both journey ends reachable while allowing intentional
    // partial-journey exploration. No hidden source nodes are deleted.
    const low = rect.right - 44 - zoomX(lastBase);
    const high = rect.left + 44 - zoomX(firstBase);
    if (low <= high) delta = Math.max(low, Math.min(high, delta));
    svg.style.transformOrigin = "50% 50%";
    svg.style.transform = "translateX(" + delta.toFixed(2) +
      "px) scale(" + ZOOM + ")";
    stage.classList.add("mj-stage-exploring");
    button.setAttribute("aria-pressed", "true");
    button.setAttribute("aria-label", "Fit the complete journey without cropping");
    button.textContent = "Fit full journey";
    const name = data.canonical.stages.find(s => s.id === currentStageId)?.name;
    note.textContent = name
      ? "Stage focus: " + name
      : "Use the Stage menu above to move";
    updatePresentation();
  }

  function schedule() {
    if (frame) cancelAnimationFrame(frame);
    frame = requestAnimationFrame(render);
  }

  button.addEventListener("click", () => {
    enabled = !enabled;
    schedule();
  });
  window.addEventListener("mjourney:stage-focus", event => {
    currentStageId = event.detail?.stageId || "";
    if (enabled) schedule();
  });
  window.addEventListener("resize", schedule);
  const observer = new ResizeObserver(schedule);
  observer.observe(stage);
  render();

  window.__mjourneyStageExplore = Object.freeze({
    state: () => ({
      active: enabled,
      selectedStage: currentStageId,
      originalViewBoxPreserved: svg.getAttribute("viewBox") === sourceViewBox,
      stationCount: positions.size,
      zoom: enabled ? ZOOM : 1,
    }),
  });
})();
