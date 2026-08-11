import { NextRequest } from "next/server";
import { API_URL } from "./env";

/** Forwards the real visitor so the API can rate-limit them, not the hosting egress address. */
export function clientHeaders(req?: NextRequest): Record<string, string> {
  if (!req) return {};

  const forwarded = req.headers.get("x-forwarded-for");
  const clientIp = forwarded?.split(",")[0]?.trim();
  if (!clientIp) return {};

  const headers: Record<string, string> = { "x-isra-client-ip": clientIp };
  const secret = process.env.ISRA_PROXY_SECRET;
  if (secret) headers["x-isra-proxy-secret"] = secret;
  return headers;
}

export async function proxyJSON(
  path: string,
  init?: RequestInit,
  req?: NextRequest,
): Promise<Response> {
  try {
    const upstream = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { ...(init?.headers as Record<string, string>), ...clientHeaders(req) },
    });
    const text = await upstream.text();
    return new Response(text, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return Response.json(
      { error: `Cannot reach the API at ${API_URL}. Is it running?` },
      { status: 502 },
    );
  }
}
