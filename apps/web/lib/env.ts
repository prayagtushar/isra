export function getApiUrl(
  envValue: string | undefined,
  nodeEnv: string | undefined,
): string {
  if (typeof envValue === "string" && envValue) {
    return envValue;
  }
  if (nodeEnv === "production") {
    throw new Error("API_URL environment variable is required in production");
  }
  return "http://localhost:8000";
}

export const API_URL = getApiUrl(process.env.API_URL, process.env.NODE_ENV);

export function getAuthSecret(
  envValue: string | undefined,
  nodeEnv: string | undefined,
): string {
  if (typeof envValue === "string" && envValue.length >= 32) {
    return envValue;
  }
  if (nodeEnv === "production") {
    throw new Error("AUTH_SECRET must be at least 32 characters in production");
  }
  return "dev-secret-isra-please-change-in-production";
}

export const AUTH_SECRET = getAuthSecret(
  process.env.AUTH_SECRET,
  process.env.NODE_ENV,
);
