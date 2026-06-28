

from src.merge import merge_startups
from src.schema import Startup

def _startup(name: str, **kw) -> Startup:
    base = dict(
        name=name,
        normalized_name=name,  
        description="placeholder description",
        founders=["Someone"],
        source_url="https://example.com",
    )
    base.update(kw)
    return Startup(**base)

def test_merge_dedupes_and_unions_fields():
    a = _startup(
        "Zomato",
        description="short",
        founders=["Deepinder Goyal"],
        sectors=["Foodtech"],
        fundings=2.5,
        founded_year=2008,
    )
    b = _startup(
        "ZOMATO",
        description="a considerably longer description than the first one",
        founders=["Pankaj Chaddah"],
        sectors=["E-commerce"],
        tags=["food"],
        headquarters="Gurugram",
    )

    merged = merge_startups([a, b])
    assert len(merged) == 1

    m = merged[0]
    assert m.normalized_name == "zomato"
    assert set(m.founders) == {"Deepinder Goyal", "Pankaj Chaddah"}
    assert set(m.sectors) == {"Foodtech", "E-commerce"}
    assert m.description == b.description  
    assert m.fundings == 2.5  
    assert m.founded_year == 2008
    assert m.headquarters == "Gurugram"  

def test_merge_keeps_distinct_startups():
    out = merge_startups([_startup("Ola"), _startup("Cred")])
    assert {s.normalized_name for s in out} == {"ola", "cred"}
