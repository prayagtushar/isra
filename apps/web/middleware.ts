import { NextRequest, NextResponse } from "next/server";
import { AUTH_SECRET } from "@/lib/env";
import { unsealSession } from "@/lib/auth";

// Retrieval-only surfaces are public so the project can be evaluated without
// signing up: they hit Postgres and the reranker, which cost nothing per
// request. /chat stays gated because every call spends LLM tokens, and
// /ingest and /feedback stay gated because they write.
const PROTECTED_PATHS = ["/chat", "/ingest", "/api"];
const PUBLIC_API_PATHS = [
  "/api/auth/signup",
  "/api/auth/signin",
  "/api/auth/signout",
  "/api/auth/forgot-password",
  "/api/auth/reset-password",
  "/api/auth/me",
  "/api/search",
  "/api/startups",
];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (PUBLIC_API_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const isProtected = PROTECTED_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
  if (!isProtected) {
    return NextResponse.next();
  }

  const token = request.cookies.get("isra-session")?.value;
  const session = token ? await unsealSession(token, AUTH_SECRET) : null;

  if (!session) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname + request.nextUrl.search);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|woff|woff2)$).+)",
  ],
};
