/* Deterministic source-edge corridor routing on the *rendered* System SVG.
 *
 * Presentation geometry only. Fixed canonical station endpoints, no new nodes,
 * stage movements, connections, or transfer semantics. The browser supplies
 * original authored relationship IDs from the validated research sidecar.
 *
 * The compact candidate search uses H/V/45-degree elbows and compares them
 * for bends, length, clearance, incidental crossings and overlap with other
 * chosen source edges. It cannot and does not repair the native category-line
 * arrangement or claim a globally optimized transit map.
 */
(function (root) {
  "use strict";
  const EPS = 1e-5;
  const pt = (x, y) => ({x, y});
  const same = (a, b) => Math.abs(a.x - b.x) < EPS && Math.abs(a.y - b.y) < EPS;
  const length = (a, b) => Math.hypot(b.x - a.x, b.y - a.y);
  const sign = x => x < 0 ? -1 : x > 0 ? 1 : 0;

  function simplify(points) {
    const clean = [];
    for (const p of points) if (!clean.length || !same(p, clean[clean.length - 1]))
      clean.push(pt(p.x, p.y));
    let i = 1;
    while (i + 1 < clean.length) {
      const a = clean[i - 1], b = clean[i], c = clean[i + 1];
      const cross = (b.x - a.x) * (c.y - b.y) -
                    (b.y - a.y) * (c.x - b.x);
      const forward = (b.x - a.x) * (c.x - b.x) +
                      (b.y - a.y) * (c.y - b.y);
      if (Math.abs(cross) < EPS && forward >= -EPS) clean.splice(i, 1);
      else i++;
    }
    return clean;
  }
  function isOctilinear(points) {
    return points.length >= 2 && points.slice(1).every((b, i) => {
      const a = points[i], dx = Math.abs(b.x - a.x), dy = Math.abs(b.y - a.y);
      return length(a, b) > EPS &&
        (dx < EPS || dy < EPS || Math.abs(dx - dy) < EPS);
    });
  }
  function pathData(points) {
    return points.map((p, i) => (i ? "L" : "M") +
      p.x.toFixed(2) + "," + p.y.toFixed(2)).join(" ");
  }
  function segments(points) {
    return points.slice(1).map((p, i) => [points[i], p]);
  }
  function cross(a, b, p) {
    return (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x);
  }
  function properIntersection(a, b, c, d) {
    return cross(a, b, c) * cross(a, b, d) < -EPS &&
           cross(c, d, a) * cross(c, d, b) < -EPS;
  }
  function distancePointSegment(p, a, b) {
    const dx = b.x - a.x, dy = b.y - a.y;
    const denom = dx * dx + dy * dy || 1;
    const t = Math.max(0, Math.min(1,
      ((p.x - a.x) * dx + (p.y - a.y) * dy) / denom));
    return Math.hypot(p.x - a.x - t * dx, p.y - a.y - t * dy);
  }
  function overlapLength(a, b, c, d) {
    // Only exactly collinear segments are considered shared corridors.
    if (Math.abs(cross(a, b, c)) > EPS ||
        Math.abs(cross(a, b, d)) > EPS) return 0;
    const dx = Math.abs(b.x - a.x), dy = Math.abs(b.y - a.y);
    const axis = dx >= dy ? "x" : "y";
    return Math.max(0, Math.min(Math.max(a[axis], b[axis]),
      Math.max(c[axis], d[axis])) -
      Math.max(Math.min(a[axis], b[axis]),
        Math.min(c[axis], d[axis]))) * (dx >= dy && dy > EPS ||
          dy > dx && dx > EPS ? Math.SQRT2 : 1);
  }
  function candidates(a, b) {
    const dx = b.x - a.x, dy = b.y - a.y;
    const sx = sign(dx), sy = sign(dy);
    const range = Math.min(Math.abs(dx), Math.abs(dy));
    const paths = [], seen = new Set();
    function record(raw) {
      const points = simplify(raw);
      if (!same(points[0], a) || !same(points[points.length - 1], b) ||
          !isOctilinear(points)) return;
      const key = pathData(points);
      if (!seen.has(key)) { seen.add(key); paths.push(points); }
    }
    // A fixed pair of endpoints can be reached with 0/45/90 segments.
    // Vary diagonal size and reserve horizontal/vertical approach corridor.
    const splits = [0, .35, .65, 1];
    for (const diagonalShare of [1, .8, .55, .35]) {
      const diag = range * diagonalShare;
      const horizontal = Math.abs(dx) - diag;
      const vertical = Math.abs(dy) - diag;
      for (const beforeH of splits) for (const beforeV of splits) {
        let p = pt(a.x, a.y);
        const raw = [p];
        p = pt(p.x + sx * horizontal * beforeH, p.y); raw.push(p);
        p = pt(p.x, p.y + sy * vertical * beforeV); raw.push(p);
        p = pt(p.x + sx * diag, p.y + sy * diag); raw.push(p);
        p = pt(p.x + sx * horizontal * (1 - beforeH), p.y); raw.push(p);
        p = pt(p.x, p.y + sy * vertical * (1 - beforeV)); raw.push(p);
        // Floating-point accumulation must never drift off a canonical node.
        raw[raw.length - 1] = b;
        record(raw);
      }
    }
    // Narrow axial runs may need a cartographic offset to clear a station.
    // These bounded S-shaped detours use only H/V/45 segments, no new stops.
    if (Math.abs(dx) < EPS && Math.abs(dy) > 45) {
      for (const offset of [-20, 20, -34, 34]) {
        const abs = Math.abs(offset);
        const sy0 = sign(dy);
        if (Math.abs(dy) < 2 * abs) continue;
        record([a, pt(a.x + offset, a.y + sy0 * abs),
          pt(a.x + offset, b.y - sy0 * abs), b]);
      }
    }
    if (Math.abs(dy) < EPS && Math.abs(dx) > 55) {
      for (const offset of [-20, 20, -34, 34]) {
        const sx0 = sign(dx), abs = Math.abs(offset);
        if (Math.abs(dx) < 2 * abs) continue;
        record([a, pt(a.x + sx0 * abs, a.y + offset),
          pt(b.x - sx0 * abs, a.y + offset), b]);
      }
    }
    // Baseline is always available. The planner may deliberately retain it.
    record([a, b]);
    return paths;
  }

  function measure(points, opts) {
    const {startId, endId, stations, guides, selected, xBound, yBound} = opts;
    let cost = 0, crossings = 0, minimumClearance = Infinity, lengthTotal = 0;
    const legs = segments(points);
    for (const [a, b] of legs) {
      const dist = length(a, b);
      lengthTotal += dist;
      // Isolated micro-bends look like accidental junctions.
      if (dist < 13) cost += 18;
      const [minX, maxX] = [Math.min(a.x, b.x), Math.max(a.x, b.x)];
      const [minY, maxY] = [Math.min(a.y, b.y), Math.max(a.y, b.y)];
      if (minX < xBound[0] - EPS || maxX > xBound[1] + EPS) cost += 1200;
      if (minY < yBound[0] - EPS || maxY > yBound[1] + EPS) cost += 1200;
      for (const [id, loc] of stations) {
        if (id === startId || id === endId) continue;
        const d = distancePointSegment(loc, a, b);
        minimumClearance = Math.min(minimumClearance, d);
        // Native stop marker radius 4.5; large source rings 14.
        if (d < 13) cost += 1500;
        else if (d < 24) cost += (24 - d) * 11;
      }
      for (const guide of guides) {
        for (const [c, d] of segments(guide)) {
          if (properIntersection(a, b, c, d)) {
            crossings++;
            cost += 36;
          }
          // Colored categories are not source routes. Overlap at coincident
          // coordinates risks confusing the two visual semantics.
          cost += overlapLength(a, b, c, d) * .65;
        }
      }
      for (const prior of selected) {
        for (const [c, d] of segments(prior.points)) {
          if (properIntersection(a, b, c, d)) cost += 150;
          const shared = overlapLength(a, b, c, d);
          if (shared) cost += shared * (
            prior.fromId === startId || prior.toId === endId ? .12 : 2.0);
        }
      }
    }
    cost += lengthTotal * .20 + Math.max(0, points.length - 2) * 10;
    return {score: cost, guideCrossings: crossings,
      length: lengthTotal, bends: Math.max(0, points.length - 2),
      minStationClearance: minimumClearance};
  }

  function plan(sourceEdges, positions, guides, options) {
    const stations = positions instanceof Map
      ? positions : new Map(Object.entries(positions));
    const yValues = [...stations.values()].map(p => p.y);
    const yBound = [Math.min(...yValues) - 38, Math.max(...yValues) + 38];
    const selected = [];
    const result = [];
    for (const edge of sourceEdges) {
      const a = stations.get(edge.fromId), b = stations.get(edge.toId);
      if (!a || !b) throw new Error("Unknown canonical source endpoint " + edge.id);
      const candidatesForEdge = candidates(a, b);
      const xBound = [Math.min(a.x, b.x) - 28, Math.max(a.x, b.x) + 28];
      let chosen = null;
      for (const points of candidatesForEdge) {
        const stats = measure(points, {
          startId: edge.fromId, endId: edge.toId,
          stations, guides, selected, xBound, yBound,
        });
        const candidate = {points, ...stats};
        if (!chosen || candidate.score < chosen.score - EPS ||
            (Math.abs(candidate.score - chosen.score) < EPS &&
              pathData(points) < pathData(chosen.points))) chosen = candidate;
      }
      if (!chosen) throw new Error("No valid octilinear route for " + edge.id);
      result.push({
        id: edge.id, fromId: edge.fromId, toId: edge.toId,
        points: chosen.points, path: pathData(chosen.points),
        score: +chosen.score.toFixed(3),
        guideCrossings: chosen.guideCrossings,
        bends: chosen.bends,
        length: +chosen.length.toFixed(2),
        minStationClearance: Number.isFinite(chosen.minStationClearance)
          ? +chosen.minStationClearance.toFixed(2) : null,
      });
      selected.push({points: chosen.points,
        fromId: edge.fromId, toId: edge.toId});
    }
    return result;
  }
  const api = Object.freeze({plan, candidates, isOctilinear, pathData, measure,
    properIntersection, distancePointSegment});
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.MJourneyCorridorRouter = api;
})(typeof window !== "undefined" ? window : null);
