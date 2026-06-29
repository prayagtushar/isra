import { NextRequest } from "next/server";
import { API_URL } from "@/lib/env";
import type { ChatRequest } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: NextRequest): Promise<Response> {
  const body = (await req.json()) as ChatRequest;

  if (!body.question || typeof body.question !== "string") {
    return Response.json({ error: "Missing question" }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: body.question,
        history: body.history ?? [],
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
