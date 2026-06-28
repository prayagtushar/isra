from datetime import datetime

from src.schema import Startup

def test_startup_normalization():
    s = Startup(
        name="OlA Electrics Scooter",
        normalized_name="Ola Electric",
        one_liner="Run like a sting like a bee",
        description="OLA Electric scooters are the next gen upgrade",
        founders=["Bhavish Aggarwal"],
        source_url="https://yc.com",
        scraped_date=datetime.now(),
    )

    assert s.normalized_name == "olaelectric"

def test_startup_by_name():
    a = Startup(
        name="Ola",
        normalized_name="ola",
        description="Electric mobility startup",
        founders=["Bhavish Aggarwal"],
        source_url="https://a.com",
        scraped_date=datetime.now(),
    )
    b = Startup(
        name="OLA",
        normalized_name="ola",
        description="Mobility company",
        founders=["Bhavish Aggarwal", "Ankit Bhati"],
        source_url="https://b.com",
        scraped_date=datetime.now(),
    )

    assert {a, b} == {a}
