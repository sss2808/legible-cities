"use strict";
const assert = require("node:assert/strict");
const {plan, candidates, isOctilinear, properIntersection} =
  require("../src/schematic/page/mjourney_corridor_router.js");

function test(title, fn) {
  try { fn(); process.stdout.write("PASS " + title + "\n"); }
  catch (err) { process.stderr.write("FAIL " + title + "\n"); throw err; }
}
function equalPoint(a, b) {
  return Math.abs(a.x - b.x) < 1e-5 && Math.abs(a.y - b.y) < 1e-5;
}

test("all candidate segments are horizontal, vertical or 45 degrees", () => {
  for (const [a, b] of [
    [{x: 10, y: 10}, {x: 200, y: 180}],
    [{x: 200, y: 10}, {x: 10, y: 150}],
    [{x: 0, y: 0}, {x: 0, y: 100}],
    [{x: 0, y: 100}, {x: 130, y: 100}],
    [{x: 0, y: 0}, {x: 60, y: 60}],
  ]) {
    const routes = candidates(a, b);
    assert.ok(routes.length);
    for (const points of routes) {
      assert.ok(isOctilinear(points), JSON.stringify(points));
      assert.ok(equalPoint(points[0], a));
      assert.ok(equalPoint(points[points.length - 1], b));
    }
  }
});

test("detours around unrelated canonical stations without inventing stops", () => {
  const stations = new Map([
    ["from", {x: 0, y: 0}], ["to", {x: 0, y: 120}],
    ["bystander", {x: 0, y: 60}],
  ]);
  const source = [{id:"edge1", fromId:"from", toId:"to"}];
  const planA = plan(source, stations, []);
  assert.equal(planA.length, 1);
  assert.equal(planA[0].id, "edge1");
  assert.ok(planA[0].minStationClearance >= 13, planA[0].minStationClearance);
  assert.ok(planA[0].bends >= 2);
  assert.ok(isOctilinear(planA[0].points));
});

test("preserves exact endpoints even with reverse-x convergences", () => {
  const stations = new Map([
    ["origin", {x: 96.5, y: 75.25}],
    ["later", {x: 40.25, y: 132.5}],
    ["other", {x: 40.25, y: 75.25}],
  ]);
  const source = [{id:"edgeZ", fromId:"origin", toId:"later"}];
  const result = plan(source, stations, []);
  assert.deepEqual(result.map(e=>e.id), ["edgeZ"]);
  assert.ok(equalPoint(result[0].points[0], stations.get("origin")));
  assert.ok(equalPoint(result[0].points.at(-1), stations.get("later")));
});

test("same inputs return byte-for-byte identical paths and scores", () => {
  const stations = new Map([
    ["from", {x: 0, y: 0}], ["mid", {x: 70, y: 60}],
    ["to", {x: 120, y: 110}], ["bystander", {x: 65, y: 65}],
  ]);
  const edges = [{id:"edgeA", fromId:"from", toId:"mid"},
                 {id:"edgeB", fromId:"mid", toId:"to"}];
  const guide = [[{x: 10, y: 80}, {x: 110, y: 80}]];
  const a = plan(edges, stations, guide);
  const b = plan(edges, stations, guide);
  assert.deepEqual(a, b);
  assert.ok(a.every(e => isOctilinear(e.points)));
});

test("crossing detection requires interior intersection, never shared endpoint", () => {
  assert.ok(properIntersection(
    {x: 0, y: 0}, {x: 100, y: 100},
    {x: 0, y: 100}, {x: 100, y: 0}));
  assert.ok(!properIntersection(
    {x: 0, y: 0}, {x: 100, y: 100},
    {x: 100, y: 100}, {x: 150, y: 100}));
});
console.log("Corridor router unit tests passed");
