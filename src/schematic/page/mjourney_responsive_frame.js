/* Responsive M-Journey category legend, preserving the native line toggles.
 * This module only composes pre-existing controls. It neither redraws routes
 * nor writes the SVG's viewBox, which the Legible Cities viewer owns.
 */
(() => {
  "use strict";
  if (!document.documentElement.hasAttribute("data-mjourney-inspector")) return;
  const panel = document.getElementById("more-panel");
  const row = panel && panel.querySelector(".panel-row");
  const chips = document.getElementById("line-toggles");
  const group = row && row.querySelector(".panel-group");
  if (!panel || !row || !chips || !group) return;
  if (document.getElementById("mj-category-disclosure")) return;
  row.classList.add("mj-legend-composed");

  const disclosure = document.createElement("button");
  disclosure.id = "mj-category-disclosure";
  disclosure.type = "button";
  disclosure.setAttribute("aria-controls", "line-toggles");
  disclosure.setAttribute("aria-expanded", "true");
  disclosure.setAttribute("aria-label", "Hide category line filters");
  disclosure.textContent = "Hide lines";
  group.appendChild(disclosure);

  let expanded = true;
  function redrawMeasuredContent() {
    // The native viewer owns canvas Fit and route selection. Only its existing
    // research stage headers and labels need a fresh browser measurement.
    requestAnimationFrame(() => {
      window.__mjourneyScene?.redrawStages?.();
      window.__mjourneyLabels?.redraw?.();
    });
  }
  function setExpanded(on) {
    expanded = !!on;
    row.classList.toggle("mj-legend-collapsed", !expanded);
    chips.hidden = !expanded;
    disclosure.setAttribute("aria-expanded", String(expanded));
    disclosure.setAttribute("aria-label",
      expanded ? "Hide category line filters" : "Show category line filters");
    disclosure.textContent = expanded ? "Hide lines" : "Show lines";
    redrawMeasuredContent();
  }
  disclosure.addEventListener("click", () => setExpanded(!expanded));

  // Preserve all seven original chip nodes, including their upstream pointer,
  // keyboard and All/None handling, and keep the research map in the
  // viewport. Do not resize or move the source SVG ourselves.
  const api = Object.freeze({
    expanded: () => expanded,
    sourceChipCount: () => chips.querySelectorAll(".chip").length,
    sourceChipLabels: () => [...chips.querySelectorAll(".chip")]
      .map(chip => chip.textContent.trim()),
    noClippedChipBounds: () => {
      if (!expanded) return null;
      const container = chips.getBoundingClientRect();
      return [...chips.querySelectorAll(".chip")].every(chip => {
        const b = chip.getBoundingClientRect();
        return b.left >= container.left - 1 &&
          b.right <= container.right + 1 &&
          b.top >= container.top - 1 &&
          b.bottom <= container.bottom + 1;
      });
    },
  });
  window.__mjourneyResponsiveFrame = api;
  setExpanded(true);
})();
