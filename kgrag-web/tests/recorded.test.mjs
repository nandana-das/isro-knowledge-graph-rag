import test from "node:test";
import assert from "node:assert/strict";

const FILE = {
  generated_utc: "2026-10-28T10:00:00+00:00",
  model: "mistral:7b-instruct-q4_K_M",
  code_commit: "abc1234",
  examples: [{ question: "Which launch vehicle launched AstroSat?", mission: "AstroSat", category: "DIRECT_CONTROL" }],
  answers: {
    "which launch vehicle launched astrosat?": { question: "Which launch vehicle launched AstroSat?", answer: "PSLV-C30 (XL)", mode: "recorded" },
  },
};

test("recorded answers: lookup ignores case and spacing, misses return null", async () => {
  const originalFetch = globalThis.fetch;
  let requested = null;
  globalThis.fetch = async (url) => {
    requested = url;
    return new Response(JSON.stringify(FILE), { status: 200, headers: { "Content-Type": "application/json" } });
  };
  try {
    const { normalizeQuestion, recordedAnswer } = await import("../src/recorded.ts");
    assert.equal(normalizeQuestion("  Which   launch vehicle\tlaunched AstroSat? "), "which launch vehicle launched astrosat?");
    const hit = await recordedAnswer("WHICH launch vehicle launched  AstroSat?");
    assert.equal(hit.answer, "PSLV-C30 (XL)");
    assert.equal(hit.mode, "recorded");
    assert.equal(await recordedAnswer("What is a question nobody recorded?"), null);
    assert.ok(requested.endsWith("recorded_answers.json"));
  } finally {
    globalThis.fetch = originalFetch;
  }
});
