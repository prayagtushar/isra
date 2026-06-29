export function getApiUrl(envValue: string | undefined, nodeEnv: string | undefined): string {
  if (typeof envValue === "string" && envValue) {
    return envValue;
  }
  if (nodeEnv === "production") {
    throw new Error("API_URL environment variable is required in production");
  }
  return "http://localhost:8000";
}

export const API_URL = getApiUrl(process.env.API_URL, process.env.NODE_ENV);
