import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { API_URL, AUTH_SECRET } from "@/lib/env";
import { sealSession } from "@/lib/auth";

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
  maxAge: 60 * 60 * 24 * 7,
};

async function setUserCookie(user: { id: string; email: string }) {
  const token = await sealSession(
    { userId: user.id, email: user.email },
    AUTH_SECRET,
  );
  const cookieStore = await cookies();
  cookieStore.set("isra-session", token, COOKIE_OPTIONS);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const upstream = await fetch(`${API_URL}/auth/signin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!upstream.ok) {
    const text = await upstream.text().catch(() => "Invalid email or password");
    return NextResponse.json({ error: text }, { status: upstream.status });
  }

  const user = (await upstream.json()) as { id: string; email: string };
  await setUserCookie(user);
  return NextResponse.json(user);
}
