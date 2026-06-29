

export interface paths {
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/search": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        
        post: operations["search_search_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/chat": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        
        post: operations["chat_chat_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/feedback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        
        post: operations["feedback_feedback_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/startups": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        
        get: operations["list_startups_startups_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/ingest": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        
        post: operations["ingest_ingest_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        
        ChatRequest: {
            
            question: string;
            
            history?: components["schemas"]["HistoryTurn"][] | null;
            
            top_k: number;
            
            mode: string;
        };
        
        FeedbackRequest: {
            
            query: string;
            
            answer?: string | null;
            
            thumbs: boolean;
            
            comment?: string | null;
        };
        
        HTTPValidationError: {
            
            detail?: components["schemas"]["ValidationError"][];
        };
        
        HealthResponse: {
            
            status: string;
        };
        
        HistoryTurn: {
            
            role: string;
            
            content: string;
        };
        
        IngestRequest: {
            
            limit?: number | null;
            
            refresh: boolean;
        };
        
        SearchRequest: {
            
            query: string;
            
            top_k: number;
            
            mode: string;
        };
        
        SearchResponse: {
            
            query: string;
            
            results: components["schemas"]["SearchResult"][];
        };
        
        SearchResult: {
            
            id: number;
            
            startup_name: string;
            
            chunk_index: number;
            
            text: string;
            
            source_url: string;
            
            score: number;
        };
        
        StartupOut: {
            
            id: number;
            
            name: string;
            
            normalized_name?: string | null;
            
            one_liner?: string | null;
            
            description: string;
            
            sectors: string[];
            
            tags: string[];
            
            founders: string[];
            
            founded_year?: number | null;
            
            headquarters?: string | null;
            
            fundings?: number | null;
            
            source_url: string;
        };
        
        StartupsResponse: {
            
            total: number;
            
            startups: components["schemas"]["StartupOut"][];
        };
        
        ValidationError: {
            
            loc: (string | number)[];
            
            msg: string;
            
            type: string;
            
            input?: unknown;
            
            ctx?: Record<string, never>;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HealthResponse"];
                };
            };
        };
    };
    search_search_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SearchRequest"];
            };
        };
        responses: {
            
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SearchResponse"];
                };
            };
            
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    chat_chat_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChatRequest"];
            };
        };
        responses: {
            
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    feedback_feedback_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FeedbackRequest"];
            };
        };
        responses: {
            
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_startups_startups_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                q?: string | null;
                sector?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StartupsResponse"];
                };
            };
            
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    ingest_ingest_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["IngestRequest"];
            };
        };
        responses: {
            
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
