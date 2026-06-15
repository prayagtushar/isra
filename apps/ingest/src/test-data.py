from src.schema import Startup


def sample_startups() -> list[Startup]:
    return [
        Startup(
            name="Ola Electric",
            normalized_name="olaelectric",
            source_url="https://olaelectric.com",
            one_liner="We manufacture electric two wheelers",
            description="Ola Electric designs and manufactures electric two-wheelers "
            "for the Indian market. It operates a large battery innovation center "
            "and a gigafactory in Tamil Nadu.",
            founded_year=2017,
            headquarters="Bangalore, India",
            founders=["Bhavish Aggarwal"],
            fundings=1_000_000_000,
            sectors=["Electric Vehicles", "Manufacturing"],
            tags=["ev", "scooter", "battery"],
            scraped_date="01/02/2000",

        ),
        Startup(
            name="PharmEasy",
            normalized_name="pharmeasy",
            source_url="https://pharmeasy.in",
            description="PharmEasy is an online pharmacy and healthcare delivery platform. "
            "It connects users with diagnostic centers and delivers medicines to their homes.",
            founded_year=2015,
            headquarters="Mumbai, India",
            founders=["Dhaval Shah", "Dharmil Sheth"],
            fundings=1_200_000_000,
            sectors=["Healthtech", "E-commerce"],
            tags=["pharmacy", "diagnostics", "delivery"],
        ),
    ]
