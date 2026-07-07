

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

from openai import AsyncOpenAI

from src.config import settings
from src.generation_eval import evaluate_generation
from src.golden import load_golden
from src.report import write_report
from src.retrieval_eval import evaluate_modes

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_MODES = ["vector", "hybrid", "hybrid+rerank"]
_GEN_MODE = "hybrid+rerank"

def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="evals")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--no-generation", action="store_true")
    p.add_argument("--modes", type=str, default=",".join(_DEFAULT_MODES))
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--out", type=str, default=str(_REPO_ROOT / "EVALUATION.md"))
    return p.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]

    items = load_golden()
    if args.limit is not None:
        items = items[: args.limit]
    if not items:
        print("No golden items found.", file=sys.stderr)
        return 1

    print(f"Evaluating {len(items)} questions across modes: {', '.join(modes)} ...")
    try:
        mode_results = evaluate_modes(items, modes, top_k=args.top_k)
    except Exception as exc:  
        print(
            f"Retrieval failed: {exc}\n"
            "Is Postgres running? Try: docker compose -f infra/compose.yml up -d",
            file=sys.stderr,
        )
        return 1

    for r in mode_results:
        print(f"  {r.mode:>14}  hit@{args.top_k}={r.hit_at_k:.3f}  MRR={r.mrr:.3f}")

    gen = None
    if args.no_generation:
        print("Generation scoring skipped (--no-generation).")
    elif not settings.openrouter_api_key:
        print("ISRA_OPENROUTER_API_KEY not set; skipping generation scoring.")
    else:
        print(f"Scoring generation on `{_GEN_MODE}` with LLM-judge ...")
        client = AsyncOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
        )
        from src.judge import OpenRouterJudge

        judge = OpenRouterJudge(client=client)
        gen = asyncio.run(
            evaluate_generation(
                items,
                mode=_GEN_MODE,
                top_k=args.top_k,
                judge=judge,
                client=client,
                model=settings.llm_model,
            )
        )
        for attr in ("faithfulness", "answer_relevancy", "context_precision"):
            scored, total = gen.coverage(attr)
            print(f"  {attr:>18}  mean={gen.mean(attr)}  coverage={scored}/{total}")

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n": len(items),
        "top_k": args.top_k,
        "model": settings.llm_model,
    }
    out = write_report(Path(args.out), meta, mode_results, gen)
    print(f"Wrote {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
