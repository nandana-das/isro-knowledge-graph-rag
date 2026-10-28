import type { AskResponse, Example } from "./api";

// Answers the live system gave to the example questions, saved by
// `python -m src.api.export_recorded`. They keep the site useful while the
// live API (on a laptop, behind a tunnel) is offline.
export interface RecordedFile {
  generated_utc: string;
  model: string;
  code_commit: string;
  examples: Example[];
  answers: Record<string, AskResponse>;
}

const BASE_URL = (typeof import.meta !== "undefined" && import.meta.env?.BASE_URL) || "/";

// Must match norm() in src/api/export_recorded.py.
export const normalizeQuestion = (q: string) => q.toLowerCase().split(/\s+/).filter(Boolean).join(" ");

let cache: Promise<RecordedFile | null> | null = null;

export function loadRecorded(): Promise<RecordedFile | null> {
  cache ??= fetch(`${BASE_URL}recorded_answers.json`)
    .then((r) => (r.ok ? (r.json() as Promise<RecordedFile>) : null))
    .catch(() => null);
  return cache;
}

export async function recordedAnswer(question: string): Promise<AskResponse | null> {
  const file = await loadRecorded();
  return file?.answers[normalizeQuestion(question)] ?? null;
}
