import { NextRequest } from "next/server";
import { proxyJSON } from "@/lib/proxy";
import type { FeedbackRequest } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: NextRequest): Promise<Response> {
  const body = (await req.json()) as FeedbackRequest;
  if (typeof body.query !== "string" || typeof body.thumbs !== "boolean") {
    return Response.json(
      { error: "Missing query or thumbs" },
      { status: 400 },
    );
  }
  return proxyJSON("/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: body.query,
      answer: body.answer ?? null,
      thumbs: body.thumbs,
      comment: body.comment ?? null,
    }),
  });
}
