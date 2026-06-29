import { describe, expect, it } from "vitest";
import { getApiUrl } from "./env";

describe("getApiUrl", () => {
  it("returns the provided URL", () => {
    expect(getApiUrl("https://api.example.com", "production")).toBe("https://api.example.com");
  });

  it("falls back to localhost in development", () => {
    expect(getApiUrl(undefined, "development")).toBe("http://localhost:8000");
  });

  it("throws in production when missing", () => {
    expect(() => getApiUrl(undefined, "production")).toThrow("API_URL environment variable is required");
  });
});
