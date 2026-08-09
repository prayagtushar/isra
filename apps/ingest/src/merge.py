from typing import List

from src.schema import Startup

def merge_startups(startups: List[Startup]) -> List[Startup]:
    """Combine records for one company from several sources.

    The description and the source URL move together. They used to be decided
    separately -- the longer description won, while source_url was whatever the
    first source happened to be -- so a record could carry Wikipedia's text
    above a Y Combinator link. Zepto shipped that way. In a system whose whole
    claim is that answers cite the chunk they came from, a citation pointing at
    a page that does not contain the text is the one defect that undermines
    everything else it says.
    """
    merged: dict[str, Startup] = {}
    for s in startups:
        key = s.normalized_name
        existing = merged.get(key)
        if existing is None:
            merged[key] = s
            continue

        incoming_wins = len(s.description) > len(existing.description)
        winner = s if incoming_wins else existing

        merged[key] = existing.model_copy(
            update={
                "description": winner.description,
                "source_url": winner.source_url,
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
