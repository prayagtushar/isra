import argparse
import os

from dotenv import load_dotenv

from src.runner import run_ingest

load_dotenv()

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Indian startup data into Postgres")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cache and re-scrape")
    parser.add_argument("--chunker", default="naive", choices=["naive", "semantic"], help="Chunking strategy")
    parser.add_argument("--progress", action="store_true", help="Emit progress events as JSON lines")
    args = parser.parse_args()

    if not os.environ.get("DATABASE_URL"):
        raise ValueError("DATABASE_URL environment variable is not set")

    run_ingest(use_cache=not args.no_cache, chunker=args.chunker)

if __name__ == "__main__":
    main()
