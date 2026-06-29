import { NextRequest } from "next/server";
import { proxyJSON } from "@/lib/proxy";
import type { SearchRequest } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: NextRequest): Promise<Response> {
  const body = (await req.json()) as SearchRequest;
  if (!body.query || typeof body.query !== "string") {
    return Response.json({ error: "Missing query" }, { status: 400 });
  }
  return proxyJSON("/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: body.query,
      top_k: body.top_k ?? 5,
      mode: body.mode ?? "hybrid+rerank",
    }),
  });
}
