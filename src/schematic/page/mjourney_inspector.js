(() => {
  "use strict";
  const sourceTag = document.getElementById("mjourney-research");
  const stage = document.getElementById("stage");
  const svg = stage && stage.querySelector("svg");
  const morePanel = document.getElementById("more-panel");
  if (!sourceTag || !svg || !morePanel) return;
  const data = JSON.parse(sourceTag.textContent);
  if (!data.integrity || data.integrity.passed !== true ||
      data.schema !== "mjourney-system-research-contract/v1") return;

  const moments = new Map(data.canonical.moments.map(m => [m.id, m]));
  const groups = new Map(data.canonical.categories.map(l => [l.id, l.name]));
  const stages = new Map(data.canonical.stages.map(s => [s.id, s.name]));
  const relationships = data.canonical.relationships;
  const nodeSelector = "#stations [data-station-id]";
  const positions = new Map();
  for (const el of svg.querySelectorAll(nodeSelector)) {
    const id = el.getAttribute("data-station-id");
    if (!moments.has(id)) continue;
    let x, y;
    if (el.tagName.toLowerCase() === "circle") {
      x = Number(el.getAttribute("cx"));
      y = Number(el.getAttribute("cy"));
    } else {
      const match = /^M\s*([-\d.]+)[\s,]+([-\d.]+)/.exec(el.getAttribute("d") || "");
      if (!match) continue;
      x = Number(match[1]);
      y = Number(match[2]);
    }
    positions.set(id, { x, y });
  }

  // Read-only scene helpers share the exact canonical source and native SVG
  // station coordinates. The separate stage/relationship presentation module
  // must never reconstruct research edges from painted category guides.
  window.__mjourneyResearchViewer = Object.freeze({
    data, svg, stage, morePanel, moments, groups, stages, relationships, positions,
  });

  function elem(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }
  const toolbar = elem("div", "mj-research-tools");
  const caption = elem("label", "", "Inspect research moment");
  caption.htmlFor = "mj-moment-picker";
  const selector = elem("select", "");
  selector.id = "mj-moment-picker";
  selector.setAttribute("aria-label", "Select a canonical research moment");
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = "Choose a moment";
  selector.appendChild(empty);
  for (const st of data.canonical.stages) {
    const optgroup = document.createElement("optgroup");
    optgroup.label = st.name;
    for (const m of data.canonical.moments.filter(m => m.stageId === st.id)
             .sort((a, b) => a.label.localeCompare(b.label))) {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = m.label;
      optgroup.appendChild(opt);
    }
    selector.appendChild(optgroup);
  }
  caption.appendChild(selector);
  toolbar.appendChild(caption);
  morePanel.prepend(toolbar);

  const aside = elem("aside", "mj-inspector");
  aside.id = "mj-inspector";
  aside.hidden = true;
  aside.setAttribute("aria-label", "Research moment inspector");
  const header = elem("div", "mj-inspector-head");
  const heading = elem("h2", "", "Research moment");
  heading.id = "mj-inspector-heading";
  heading.tabIndex = -1;
  const close = elem("button", "", "Close");
  close.type = "button";
  close.setAttribute("aria-label", "Close research inspector");
  header.append(heading, close);
  const content = elem("div", "mj-inspector-body");
  aside.append(header, content);
  document.body.appendChild(aside);

  const mark = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  mark.setAttribute("id", "mj-selected-station");
  mark.setAttribute("fill", "none");
  mark.setAttribute("stroke", "#fff");
  mark.setAttribute("stroke-width", "3");
  mark.setAttribute("r", "11");
  mark.setAttribute("pointer-events", "none");
  mark.setAttribute("aria-hidden", "true");
  mark.style.display = "none";
  svg.appendChild(mark);

  const list = (title, records, direction) => {
    content.appendChild(elem("h3", "", title));
    if (!records.length) {
      content.appendChild(elem("p", "mj-inspector-muted", "No authored " + direction + " relationships in the public source."));
      return;
    }
    const ul = elem("ul", "");
    for (const r of records) {
      const neighbour = moments.get(direction === "outgoing" ? r.toId : r.fromId);
      const li = elem("li", "");
      li.appendChild(elem("span", "", (direction === "outgoing" ? "To " : "From ") +
        (neighbour ? neighbour.label : "Unknown") + " (" + r.kind + "; " + r.id + ")"));
      ul.appendChild(li);
    }
    content.appendChild(ul);
  };

  function selectMoment(id, moveFocus) {
    const m = moments.get(id);
    if (!m) return;
    selector.value = id;
    window.dispatchEvent(new CustomEvent("mjourney:selection",
      {detail: {momentId: id}}));
    heading.textContent = m.label;
    content.replaceChildren();
    content.appendChild(elem("p", "", "Stage: " + (stages.get(m.stageId) || m.stageId)));
    content.appendChild(elem("p", "", "Category: " + (groups.get(m.layerId) || m.layerId)));
    content.appendChild(elem("p", "", "Moment evidence: " +
      (m.evidenceClass || "Not supplied") +
      (m.evidenceRefPresent ? " (reference indicated)" : " (no reference indicated)")));
    const incoming = relationships.filter(r => r.toId === id);
    const outgoing = relationships.filter(r => r.fromId === id);
    list("Incoming authored relationships", incoming, "incoming");
    list("Outgoing authored relationships", outgoing, "outgoing");
    content.appendChild(elem("p", "mj-inspector-muted",
      "Category lines organize research moments. They do not establish customer travel, operational transfers or evidence strength. The source fixture does not include private research records."));
    aside.hidden = false;
    const pos = positions.get(id);
    if (pos) {
      mark.setAttribute("cx", String(pos.x));
      mark.setAttribute("cy", String(pos.y));
      mark.style.display = "";
    } else mark.style.display = "none";
    if (moveFocus) heading.focus();
  }

  selector.addEventListener("change", () => {
    if (selector.value) selectMoment(selector.value, true);
    else { aside.hidden = true; mark.style.display = "none"; }
  });
  close.addEventListener("click", () => {
    aside.hidden = true;
    mark.style.display = "none";
    selector.focus();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !aside.hidden) {
      aside.hidden = true;
      mark.style.display = "none";
      selector.focus();
    }
  });
  svg.addEventListener("click", event => {
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    const pt = svg.createSVGPoint();
    pt.x = event.clientX;
    pt.y = event.clientY;
    const p = pt.matrixTransform(ctm.inverse());
    const screenScale = Math.hypot(ctm.a, ctm.b);
    let nearest = null;
    let distance = screenScale > 0 ? 18 / screenScale : 0;
    for (const [id, loc] of positions) {
      const d = Math.hypot(p.x - loc.x, p.y - loc.y);
      if (d < distance) { nearest = id; distance = d; }
    }
    if (nearest) selectMoment(nearest, true);
  });
  const mapButton = document.getElementById("view-map");
  if (mapButton) {
    mapButton.setAttribute("aria-label", "System");
    mapButton.setAttribute("title", "System research schematic");
  }
})();
