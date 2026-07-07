import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { AUTH_SECRET } from "@/lib/env";
import { unsealSession } from "@/lib/auth";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get("isra-session")?.value;
  const session = token ? await unsealSession(token, AUTH_SECRET) : null;

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  return NextResponse.json({ userId: session.userId, email: session.email });
}
