

export type RetrievalMode = "vector" | "hybrid" | "hybrid+rerank";

export const RETRIEVAL_MODES: RetrievalMode[] = [
  "vector",
  "hybrid",
  "hybrid+rerank",
];

export interface Source {
  id: number;
  startup_name: string;
  chunk_index: number;
  text: string;
  source_url: string;
  score: number;
}

export interface HistoryTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  question: string;
  history?: HistoryTurn[];
  top_k?: number;
  mode?: RetrievalMode;
  trace?: boolean;
}

export type StageName = "vector" | "keyword" | "fusion" | "rerank" | "generate";

export interface TraceStage {
  name: Exclude<StageName, "generate">;
  results: Source[];
}

export interface RetrievalTrace {
  mode: RetrievalMode;
  latency_ms: number;
  stages: TraceStage[];
}

export type ChatEvent =
  | { type: "sources"; sources: Source[] }
  | { type: "token"; content: string }
  | { type: "done"; answer: string }
  | { type: "error"; message: string }
  | { type: "stage"; name: StageName; status: "start" | "done" }
  | { type: "trace"; trace: RetrievalTrace };

export interface SearchRequest {
  query: string;
  top_k?: number;
  mode?: RetrievalMode;
}

export interface SearchResponse {
  query: string;
  results: Source[];
}

export interface FeedbackRequest {
  query: string;
  answer?: string;
  thumbs: boolean;
  comment?: string;
}

export interface Startup {
  id: number;
  name: string;
  normalized_name?: string;
  one_liner?: string | null;
  description: string;
  sectors: string[];
  tags: string[];
  founders: string[];
  founded_year?: number | null;
  headquarters?: string | null;
  fundings?: number | null;
  source_url: string;
}

export interface StartupsResponse {
  total: number;
  startups: Startup[];
}

export type IngestStage = "discover" | "scrape" | "embed" | "load";

export type IngestEvent =
  | {
      type: "stage";
      stage: IngestStage;
      status: "start" | "progress" | "done";
      count?: number;
      done?: number;
      total?: number;
      name?: string;
      chunks?: number;
      cached?: boolean;
    }
  | { type: "done"; startups: number; chunks: number }
  | { type: "error"; message: string };
