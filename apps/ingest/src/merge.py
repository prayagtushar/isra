from typing import List

from src.schema import Startup

def merge_startups(startups: List[Startup]) -> List[Startup]:
    
    merged: dict[str, Startup] = {}
    for s in startups:
        key = s.normalized_name
        existing = merged.get(key)
        if existing is None:
            merged[key] = s
            continue
        merged[key] = existing.model_copy(
            update={
                "description": (
                    s.description
                    if len(s.description) > len(existing.description)
                    else existing.description
                ),
                "tags": list(set(existing.tags) | set(s.tags)),
                "sectors": list(set(existing.sectors) | set(s.sectors)),
                "founders": list(set(existing.founders) | set(s.founders)),
                "fundings": existing.fundings or s.fundings,
                "founded_year": existing.founded_year or s.founded_year,
                "headquarters": existing.headquarters or s.headquarters,
                "one_liner": existing.one_liner or s.one_liner,
            }
        )
    return list(merged.values())
