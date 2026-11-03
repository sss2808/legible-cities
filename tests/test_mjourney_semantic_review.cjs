/* Offline, source-snapshot regression tests for TM-01b semantic review.
 * No browser, network, mutated fixtures, or private evidence dependencies.
 */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {classify} = require("../src/schematic/page/mjourney_semantic_review.js");

const fixture = JSON.parse(fs.readFileSync(path.join(__dirname,
  "../fixtures/mjourney/equipment-sanitized-v1.json"), "utf8"));
const contract = {
  schema: "mjourney-system-research-contract/v1",
  integrity: {passed: true},
  canonical: {
    moments: fixture.moments.map(m => ({
      id: m.id, layerId: m.layerId, stageId: m.stageId})),
    relationships: fixture.connections.map(e => ({
      id: e.id, fromId: e.fromId, toId: e.toId, kind: e.kind})),
  },
};
const result = classify(contract);
assert.equal(result.sourceMomentCount, 67);
assert.equal(result.sourceRelationCount, 87);
assert.deepEqual(result.handoffs.map(e => e.id),
  ["edge71", "edge78", "edge84"]);
assert.deepEqual(result.handoffs.map(e => e.crossLayer),
  [false, true, true]);
assert.equal(result.returns.length, 1);
assert.deepEqual(result.returns[0], {
  id: "edge87", fromId: "eq67", toId: "eq01",
  kind: "lifecycle_return", crossLayer: false,
});
assert.equal(result.handoffs.length + result.returns.length, 4);

// Source edge and membership counts are unmodified by the classification.
assert.equal(fixture.connections.length, 87);
assert.equal(fixture.moments.length, 67);
const guides = fixture.layers.reduce((n, layer) =>
  n + Math.max(0, fixture.moments.filter(m => m.layerId === layer.id).length - 1), 0);
assert.equal(guides, 60);
assert.equal(fixture.layers.length, 7);
assert.equal(fixture.stages.length, 10);

// Public starter and future maps must not assume specific hardcoded edge IDs.
const starter = JSON.parse(fs.readFileSync(path.join(__dirname,
  "../fixtures/mjourney/b2b-starter-v1.json"), "utf8"));
const sample = classify({
  schema: contract.schema, integrity: {passed: true},
  canonical: {
    moments: starter.moments.map(m => ({id: m.id, layerId: m.layerId})),
    relationships: starter.connections.map(e =>
      ({id:e.id, fromId:e.fromId, toId:e.toId, kind:e.kind})),
  },
});
assert.equal(sample.sourceMomentCount, 19);
assert.equal(sample.sourceRelationCount, 18);

// Invalid source cannot quietly become a rendered transfer.
for (const bad of [
  {...contract, schema: "unapproved"},
  {...contract, integrity: {passed: false}},
  {...contract, canonical: {...contract.canonical, relationships: [
    ...contract.canonical.relationships, contract.canonical.relationships[0]]}},
  {...contract, canonical: {...contract.canonical, relationships: [{
    id: "fabricated", fromId: "eq01", toId: "missing", kind: "handoff"}]}},
  {...contract, canonical: {...contract.canonical, relationships: [{
    id: "self", fromId: "eq01", toId: "eq01", kind: "handoff"}]}},
]) assert.throws(() => classify(bad));

console.log("TM-01b source-backed semantic classification PASS: 67/87; handoffs 71/78/84; return 87; negative cases");
