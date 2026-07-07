import { API_URL } from "./env";

export async function proxyJSON(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  try {
    const upstream = await fetch(`${API_URL}${path}`, init);
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
