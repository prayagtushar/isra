export interface Session {
  userId: string;
  email: string;
  exp?: number;
}

const COOKIE_NAME = "isra-session";
const SESSION_TTL_MS = 7 * 24 * 60 * 60 * 1000;

function b64urlEncode(input: string): string {
  return btoa(input).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function b64urlDecode(input: string): string {
  const padded =
    input.replace(/-/g, "+").replace(/_/g, "/") +
    "=".repeat((4 - (input.length % 4)) % 4);
  return atob(padded);
}

async function importKey(secret: string): Promise<CryptoKey> {
  const encoder = new TextEncoder();
  return crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"],
  );
}

export async function sealSession(
  session: Session,
  secret: string,
): Promise<string> {
  const payload = JSON.stringify({
    ...session,
    exp: session.exp ?? Date.now() + SESSION_TTL_MS,
  });
  const key = await importKey(secret);
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(payload),
  );
  const sigBytes = Array.from(new Uint8Array(signature))
    .map((b) => String.fromCharCode(b))
    .join("");
  return `${b64urlEncode(payload)}.${b64urlEncode(sigBytes)}`;
}

export async function unsealSession(
  token: string,
  secret: string,
): Promise<Session | null> {
  const [payloadB64, sigB64] = token.split(".");
  if (!payloadB64 || !sigB64) return null;

  let payload: string;
  let signature: Uint8Array;
  try {
    payload = b64urlDecode(payloadB64);
    signature = Uint8Array.from(
      b64urlDecode(sigB64).split("").map((c) => c.charCodeAt(0)),
    );
  } catch {
    return null;
  }

  const key = await importKey(secret);
  const valid = await crypto.subtle.verify(
    "HMAC",
    key,
    signature as BufferSource,
    new TextEncoder().encode(payload),
  );
  if (!valid) return null;

  let session: Session;
  try {
    session = JSON.parse(payload) as Session;
  } catch {
    return null;
  }
  if (
    !session.userId ||
    !session.email ||
    (session.exp && session.exp < Date.now())
  ) {
    return null;
  }
  return session;
}

export { COOKIE_NAME };
export { SESSION_TTL_MS };
