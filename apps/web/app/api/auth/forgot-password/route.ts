import { NextRequest, NextResponse } from "next/server";
import { API_URL } from "@/lib/env";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const upstream = await fetch(`${API_URL}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!upstream.ok) {
    const text = await upstream.text().catch(() => "Request failed");
    return NextResponse.json({ error: text }, { status: upstream.status });
  }

  return NextResponse.json({ status: "ok" });
}
