import { NextRequest } from "next/server";
import { API_URL } from "./env";

/**
 * Headers that let the API rate-limit the real visitor.
 *
 * Every browser request reaches the API through this server-side proxy, so the
 * API only ever sees the hosting platform's egress address. Without forwarding
 * the caller, one visitor would spend the budget for everyone. The shared
 * secret is what makes the forwarded address trustworthy — the API ignores it
 * otherwise, since anyone could claim any address.
 */
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
