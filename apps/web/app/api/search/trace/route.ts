import { NextRequest } from "next/server";
import { API_URL } from "@/lib/env";
import { clientHeaders } from "@/lib/proxy";
import type { SearchRequest } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * Streams the retrieval stages through, rather than buffering them.
 *
 * The whole point of the endpoint is that vector and keyword search land in
 * milliseconds while the cross-encoder takes seconds, so the body is passed
 * along untouched and `no-transform` is set: a proxy that buffers this would
 * deliver all four stages at once and turn a live pipeline back into a
 * slideshow.
 */
export async function POST(req: NextRequest): Promise<Response> {
  const body = (await req.json()) as SearchRequest;

  if (!body.query || typeof body.query !== "string") {
    return Response.json({ error: "Missing query" }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${API_URL}/search/trace`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...clientHeaders(req) },
      body: JSON.stringify({
        query: body.query,
        top_k: body.top_k ?? 5,
        mode: body.mode ?? "hybrid+rerank",
      }),
    });
  } catch {
    return Response.json(
      { error: `Cannot reach the API at ${API_URL}. Is it running?` },
      { status: 502 },
    );
  }

  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => "Upstream error");
    return new Response(text || "Upstream error", {
      status: upstream.status || 502,
      headers: { "Content-Type": "application/json" },
    });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
