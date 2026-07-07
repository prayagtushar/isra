import { NextRequest } from "next/server";
import { proxyJSON } from "@/lib/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest): Promise<Response> {
  const qs = new URL(req.url).searchParams.toString();
  return proxyJSON(`/startups${qs ? `?${qs}` : ""}`);
}
