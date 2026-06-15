# ISRA Web

Next.js 16 chat UI for the Indian Startup Ecosystem RAG API.

## Development

Run from the repo root:

```bash
bun run dev:web
```

This starts the dev server on `http://localhost:3000`.

The UI expects the API to be running at `http://localhost:8000`. Start it with:

```bash
bun run dev:api
```

## Routes

- `/chat` — streaming chat interface with sources and inline citations.
- `/api/chat` — Next.js route handler that forwards requests to the API and streams SSE events back to the browser.
- `/api/feedback` — forwards thumbs up/down feedback to the API.

## Tech

- Next.js 16 App Router
- React 19
- TypeScript
- Tailwind CSS
- `@isra/contracts` for shared API types

## Type generation

After changing the FastAPI request/response models, regenerate TypeScript contracts:

```bash
bun run gen:contracts
```

This requires the API to be running on `localhost:8000`.

## Deployment

This app is designed for **Vercel**. Set the `API_URL` environment variable to the deployed FastAPI endpoint.
