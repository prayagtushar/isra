import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from psycopg.rows import dict_row
from pydantic import BaseModel

from isra_retrieval import retrieve
from isra_retrieval.db import get_conn

from src.config import settings
from src.llm import stream_answer

try:
    from langfuse import Langfuse

    _langfuse = Langfuse(
        public_key=settings.langfuse_public_key or None,
        secret_key=settings.langfuse_secret_key or None,
        host=settings.langfuse_host,
    ) if (settings.langfuse_public_key and settings.langfuse_secret_key) else None
except Exception:
    _langfuse = None

app = FastAPI(title="Indian Startup Ecosystem RAG API")

class HealthResponse(BaseModel):
    status: str

@app.get("/health", response_model=HealthResponse)
async def health():
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok"}

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    mode: Literal["vector", "hybrid", "hybrid+rerank"] = "hybrid+rerank"

class SearchResult(BaseModel):
    id: int
    startup_name: str
    chunk_index: int
    text: str
    source_url: str
    score: float

class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]

@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    trace = None
    if _langfuse:
        trace = _langfuse.trace(name="search", input={"query": req.query, "mode": req.mode})

    chunks = await asyncio.to_thread(retrieve, req.query, req.top_k, req.mode)

    results = [
        SearchResult(
            id=c.id,
            startup_name=c.startup_name,
            chunk_index=c.chunk_index,
            text=c.text,
            source_url=c.source_url,
            score=c.score,
        )
        for c in chunks
    ]

    if trace:
        trace.update(output={"results": [r.model_dump() for r in results]})

    return SearchResponse(query=req.query, results=results)

class HistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    question: str
    history: list[HistoryTurn] | None = None
    top_k: int = 5
    mode: Literal["vector", "hybrid", "hybrid+rerank"] = "hybrid+rerank"

_CITATION_RE = re.compile(r"\[Source\s+(\d+)\]")

def _extract_citations(answer: str, sources: list[dict]) -> list[dict]:
    cited = set()
    for match in _CITATION_RE.finditer(answer):
        try:
            idx = int(match.group(1)) - 1
        except ValueError:
            continue
        if 0 <= idx < len(sources):
            cited.add(idx)
    return [sources[i] for i in sorted(cited)]

async def _chat_stream(
    question: str, top_k: int, mode: str, history: list[dict] | None = None
):
    try:
        chunks = await asyncio.to_thread(retrieve, question, top_k, mode)
    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
        return

    sources = [
        {
            "id": c.id,
            "startup_name": c.startup_name,
            "chunk_index": c.chunk_index,
            "text": c.text,
            "source_url": c.source_url,
            "score": c.score,
        }
        for c in chunks
    ]
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

    answer = ""
    try:
        async for token in stream_answer(question, chunks, history=history):
            answer += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
        return

    citations = _extract_citations(answer, sources)
    yield f"data: {json.dumps({'type': 'done', 'answer': answer, 'citations': citations})}\n\n"

@app.post("/chat")
async def chat(req: ChatRequest):
    history = [{"role": h.role, "content": h.content} for h in (req.history or [])]
    stream = _chat_stream(req.question, req.top_k, req.mode, history)

    if _langfuse:
        trace = _langfuse.trace(
            name="chat", input={"question": req.question, "mode": req.mode, "history": history}
        )

        async def _wrapped():
            answer = ""
            async for event in stream:
                yield event
                try:
                    data = json.loads(event.removeprefix("data: "))
                except Exception:
                    continue
                if data.get("type") == "token":
                    answer += data.get("content", "")
                elif data.get("type") == "done":
                    trace.update(output={"answer": answer, "citations": data.get("citations", [])})

        stream = _wrapped()

    return StreamingResponse(stream, media_type="text/event-stream")

class FeedbackRequest(BaseModel):
    query: str
    answer: str | None = None
    thumbs: bool
    comment: str | None = None

@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO feedback (query, answer, thumbs, comment) VALUES (%s, %s, %s, %s)",
                (req.query, req.answer, req.thumbs, req.comment),
            )
            conn.commit()
    return {"status": "ok"}

class StartupOut(BaseModel):
    id: int
    name: str
    normalized_name: str | None = None
    one_liner: str | None = None
    description: str
    sectors: list[str] = []
    tags: list[str] = []
    founders: list[str] = []
    founded_year: int | None = None
    headquarters: str | None = None
    fundings: float | None = None
    source_url: str

class StartupsResponse(BaseModel):
    total: int
    startups: list[StartupOut]

_STARTUP_COLUMNS = (
    "id, name, normalized_name, one_liner, description, "
    "sectors, tags, founders, founded_year, headquarters, fundings, source_url"
)

@app.get("/startups", response_model=StartupsResponse)
async def list_startups(
    limit: int = Query(24, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = None,
    sector: str | None = None,
):
    conditions: list[str] = []
    params: list = []
    if q:
        conditions.append("(name ILIKE %s OR one_liner ILIKE %s OR description ILIKE %s)")
        like = f"%{q}%"
        params += [like, like, like]
    if sector:
        conditions.append("%s = ANY(sectors)")
        params.append(sector)
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""

    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"SELECT COUNT(*) AS n FROM startups{where}", params)
            total = cur.fetchone()["n"]
            cur.execute(
                f"SELECT {_STARTUP_COLUMNS} FROM startups{where}"
                " ORDER BY name ASC NULLS LAST, id ASC LIMIT %s OFFSET %s",
                [*params, limit, offset],
            )
            rows = cur.fetchall()

    items = [
        StartupOut(
            id=r["id"],
            name=r["name"] or "",
            normalized_name=r["normalized_name"],
            one_liner=r["one_liner"],
            description=r["description"] or "",
            sectors=r["sectors"] or [],
            tags=r["tags"] or [],
            founders=r["founders"] or [],
            founded_year=r["founded_year"],
            headquarters=r["headquarters"],
            fundings=r["fundings"],
            source_url=r["source_url"],
        )
        for r in rows
    ]
    return StartupsResponse(total=total, startups=items)

_INGEST_DIR = Path(__file__).resolve().parents[2] / "ingest"
_ingest_running = False

class IngestRequest(BaseModel):
    limit: int | None = None
    refresh: bool = True  

async def _ingest_stream(limit: int | None, refresh: bool):
    global _ingest_running
    cmd = [sys.executable, "-m", "src", "--progress"]
    if refresh:
        cmd.append("--no-cache")
    if limit is not None:
        cmd += ["--limit", str(limit)]
    env = {**os.environ, "PYTHONPATH": str(_INGEST_DIR)}

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(_INGEST_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        assert proc.stdout is not None
        async for raw in proc.stdout:
            line = raw.decode(errors="replace").strip()
            if not line:
                continue
            try:
                json.loads(line)
            except ValueError:
                continue
            yield f"data: {line}\n\n"
        await proc.wait()
        if proc.returncode != 0:
            tail = ""
            if proc.stderr is not None:
                tail = (await proc.stderr.read()).decode(errors="replace")[-500:]
            msg = tail.strip() or f"Ingest exited with code {proc.returncode}."
            yield f"data: {json.dumps({'type': 'error', 'message': msg})}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
    finally:
        if proc is not None and proc.returncode is None:
            proc.terminate()
        _ingest_running = False

@app.post("/ingest")
async def ingest(req: IngestRequest):
    global _ingest_running
    if _ingest_running:
        body = json.dumps(
            {"type": "error", "message": "An ingest is already running."}
        )
        return StreamingResponse(
            iter([f"data: {body}\n\n"]), media_type="text/event-stream"
        )
    _ingest_running = True
    return StreamingResponse(
        _ingest_stream(req.limit, req.refresh), media_type="text/event-stream"
    )
