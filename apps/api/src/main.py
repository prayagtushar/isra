from fastapi import FastAPI

app = FastAPI(title="Indian Startup Ecosystem RAG API")


@app.get("/health")
async def health():
    return {"status": "ok"}
