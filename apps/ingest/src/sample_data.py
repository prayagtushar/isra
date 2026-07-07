from datetime import datetime

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
            scraped_date=datetime(2025, 1, 2),
        ),
        Startup(
            name="Zomato",
            normalized_name="zomato",
            source_url="https://zomato.com",
            one_liner="Food delivery and restaurant discovery platform",
            description="Zomato is a food delivery and restaurant discovery platform "
            "operating across India and multiple international markets. "
            "It connects users with restaurants for online ordering and table reservations.",
            founded_year=2008,
            headquarters="Gurugram, India",
            founders=["Deepinder Goyal", "Pankaj Chaddah"],
            fundings=2_500_000_000,
            sectors=["Foodtech", "E-commerce"],
            tags=["food delivery", "restaurant", "discovery"],
            scraped_date=datetime(2025, 1, 2),
        ),
        Startup(
            name="Paytm",
            normalized_name="paytm",
            source_url="https://paytm.com",
            one_liner="Digital payments and financial services platform",
            description="Paytm is India's leading digital payments and financial services company. "
            "It offers mobile wallet, UPI payments, banking, insurance, and commerce services.",
            founded_year=2010,
            headquarters="Noida, India",
            founders=["Vijay Shekhar Sharma"],
            fundings=4_000_000_000,
            sectors=["Fintech", "Payments"],
            tags=["wallet", "upi", "financial services"],
            scraped_date=datetime(2025, 1, 2),
        ),
        Startup(
            name="PharmEasy",
            normalized_name="pharmeasy",
            source_url="https://pharmeasy.in",
            one_liner="Pharmacy made easy",
            description="PharmEasy is an online pharmacy and healthcare delivery platform. "
            "It connects users with diagnostic centers and delivers medicines to their homes.",
            founded_year=2015,
            headquarters="Mumbai, India",
            founders=["Dhaval Shah", "Dharmil Sheth"],
            fundings=1_200_000_000,
            sectors=["Healthtech", "E-commerce"],
            tags=["pharmacy", "diagnostics", "delivery"],
            scraped_date=datetime(2025, 1, 2),
        ),
    ]
