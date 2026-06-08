// Auto-generated from FastAPI OpenAPI spec via `bun run gen:contracts`
// Run `bun run gen` after starting the API to regenerate.

export interface SearchResponse {
  results: Array<{
    id: string;
    name: string;
    score: number;
    snippet: string;
  }>;
  total: number;
}

export interface ChatRequest {
  query: string;
  history?: Array<{ role: "user" | "assistant"; content: string }>;
}

export interface ChatResponse {
  answer: string;
  sources: Array<{ id: string; name: string; score: number }>;
}

export interface FeedbackRequest {
  search_id: string;
  rating: number;
  comment?: string;
}
