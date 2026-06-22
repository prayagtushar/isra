from typing import List
from src.schema import Startup


def merge_startups(startups: List[Startup]) -> List[Startup]:

    merged_results: dict[str, Startup] = {}
    for s in startups:
        key = s.normalized_name
        if key not in merged_results:
            merged_results[key] = s
        else:
            exisitng = merged_results[key]
            merged_results[key] = exisitng.model_copy(
                update={
                    "description": (
                        s.description
                        if len(s.description) > len(exisitng.description)
                        else exisitng.description
                    ),
                    "tags": list(set(exisitng.tags) | set(s.tags)),
                    "sectors": list(set(exisitng.sectors) | set(s.sectors)),
                    "founders": list(set(exisitng.founders) | set(s.founders)),
                    "fundings": set(exisitng.fundings) or set(s.fundings),
                    "founded_year": set(exisitng.founded_year) or set(s.founded_year),
                    "headquarters": set(exisitng.headquarters) or set(s.headquarters),
                    "one_liner": set(exisitng.one_liner) or set(s.one_liner),
                }
            )
    return list(merged_results.values())
