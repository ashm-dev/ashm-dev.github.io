import test from "node:test";
import assert from "node:assert/strict";
import { projectSummary } from "../contributions.js";

const t = {
  sections: { "Pull requests": "PR", Issues: "Issues", Commits: "Commits" },
  states: {
    "Pull requests": { done: "merged", open: "open" },
    Issues: { done: "completed", open: "open" },
    Commits: { done: "committed", open: "open" },
  },
};

test("shows accepted and open counts separately", () => {
  const project = { sections: [
    { title: "Pull requests", items: [{ state: "done" }, { state: "done" }, { state: "open" }] },
    { title: "Issues", items: [{ state: "open" }] },
  ] };
  assert.equal(projectSummary(project, t), "PR: 2 merged, 1 open · Issues: 1 open");
});

test("handles commits and a single section", () => {
  assert.equal(projectSummary({ sections: [{ title: "Commits", items: [{ state: "done" }] }] }, t), "Commits: 1 committed");
});

test("omits empty legacy sections without an empty separator", () => {
  assert.equal(projectSummary({ sections: [
    { title: "Pull requests", items: [] }, { title: "Issues", items: [{ state: "open" }] },
  ] }, t), "Issues: 1 open");
});
