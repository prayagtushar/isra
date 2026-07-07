import { describe, expect, it } from "vitest";
import { sealSession, unsealSession } from "./auth";

const SECRET = "test-secret-must-be-at-least-32-bytes-long";

describe("auth", () => {
  it("seals and unseals a user session", async () => {
    const token = await sealSession(
      { userId: "user-123", email: "test@example.com" },
      SECRET,
    );
    expect(typeof token).toBe("string");
    const session = await unsealSession(token, SECRET);
    expect(session?.userId).toBe("user-123");
    expect(session?.email).toBe("test@example.com");
  });

  it("rejects a tampered token", async () => {
    const token = await sealSession(
      { userId: "user-123", email: "test@example.com" },
      SECRET,
    );
    const [payloadB64, sigB64] = token.split(".");
    const tamperedPayload =
      payloadB64.slice(0, -1) + (payloadB64.endsWith("A") ? "B" : "A");
    const session = await unsealSession(`${tamperedPayload}.${sigB64}`, SECRET);
    expect(session).toBeNull();
  });

  it("rejects a token with the wrong secret", async () => {
    const token = await sealSession(
      { userId: "user-123", email: "test@example.com" },
      SECRET,
    );
    const session = await unsealSession(
      token,
      "different-secret-32-bytes-long",
    );
    expect(session).toBeNull();
  });

  it("rejects an expired session", async () => {
    const token = await sealSession(
      { userId: "user-123", email: "test@example.com", exp: Date.now() - 1000 },
      SECRET,
    );
    const session = await unsealSession(token, SECRET);
    expect(session).toBeNull();
  });
});
