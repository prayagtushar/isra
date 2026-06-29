
import { parseSSE } from "./sse";
import type {
  ChatEvent,
  ChatRequest,
  FeedbackRequest,
  IngestEvent,
  SearchRequest,
  SearchResponse,
  StartupsResponse,
} from "./types";

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(detail || `Request to ${path} failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export async function* streamChat(
  req: ChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent, void, unknown> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal,
  });
  if (!res.ok || !res.body) {
    const detail = await res.text().catch(() => "");
    throw new Error(detail || `Chat request failed (${res.status})`);
  }
  yield* parseSSE<ChatEvent>(res.body);
}

export function search(req: SearchRequest): Promise<SearchResponse> {
  return postJSON<SearchResponse>("/api/search", req);
}

export async function* streamIngest(
  req: { limit?: number | null; refresh?: boolean },
  signal?: AbortSignal,
): AsyncGenerator<IngestEvent, void, unknown> {
  const res = await fetch("/api/ingest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal,
  });
  if (!res.ok || !res.body) {
    const detail = await res.text().catch(() => "");
    throw new Error(detail || `Ingest request failed (${res.status})`);
  }
  yield* parseSSE<IngestEvent>(res.body);
}

export async function sendFeedback(req: FeedbackRequest): Promise<void> {
  await postJSON<{ status: string }>("/api/feedback", req);
}

export interface StartupsQuery {
  limit?: number;
  offset?: number;
  q?: string;
  sector?: string;
}

export async function fetchStartups(
  query: StartupsQuery = {},
  signal?: AbortSignal,
): Promise<StartupsResponse> {
  const params = new URLSearchParams();
  if (query.limit != null) params.set("limit", String(query.limit));
  if (query.offset != null) params.set("offset", String(query.offset));
  if (query.q) params.set("q", query.q);
  if (query.sector) params.set("sector", query.sector);

  const res = await fetch(`/api/startups?${params.toString()}`, { signal });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(detail || `Startups request failed (${res.status})`);
  }
  return (await res.json()) as StartupsResponse;
}
