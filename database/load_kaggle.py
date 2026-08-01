"""
StartupIQ - Data Ingestion Loader (database/load_kaggle.py)
Populates startup_db with startup funding datasets, investor profiles, funding rounds,
many-to-many investment mappings, and textual descriptions.
"""

import os
import sys
import random
import logging
from datetime import datetime, timedelta

# Ensure parent project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from database.db_helper import get_connection, close_connection
from database.insert_data import (
    insert_startup,
    insert_investor,
    insert_funding_round,
    insert_startup_investor,
    log_scraping_activity
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

INDUSTRIES = [
    "Fintech", "Artificial Intelligence", "Healthtech", "E-commerce",
    "Edtech", "Clean Energy", "Cybersecurity", "SaaS", "Biotech", "Logistics"
]

SUB_INDUSTRIES = {
    "Fintech": ["Digital Banking", "Payments", "Insurtech", "DeFi"],
    "Artificial Intelligence": ["Generative AI", "Computer Vision", "NLP", "Robotics"],
    "Healthtech": ["Telemedicine", "Digital Health", "Medical Devices", "Health Analytics"],
    "E-commerce": ["D2C Brands", "Marketplaces", "Quick Commerce", "Social Commerce"],
    "Edtech": ["K-12 Learning", "Skill Development", "Language Learning", "Higher Ed"],
    "Clean Energy": ["Solar Tech", "Battery Storage", "EV Infrastructure", "Wind Power"],
    "Cybersecurity": ["Identity Management", "Cloud Security", "Threat Detection", "Zero Trust"],
    "SaaS": ["CRM", "HR Tech", "Developer Tools", "Project Management"],
    "Biotech": ["Genomics", "Drug Discovery", "Synthetic Biology", "Therapeutics"],
    "Logistics": ["Last-mile Delivery", "Supply Chain Analytics", "Freight Tech", "Warehousing"]
}

COUNTRIES = ["United States", "India", "United Kingdom", "Germany", "Singapore", "Canada", "Israel"]
CITIES = {
    "United States": ["San Francisco", "New York", "Austin", "Boston", "Seattle"],
    "India": ["Bengaluru", "Mumbai", "Delhi NCR", "Hyderabad", "Pune"],
    "United Kingdom": ["London", "Cambridge", "Manchester"],
    "Germany": ["Berlin", "Munich"],
    "Singapore": ["Singapore"],
    "Canada": ["Toronto", "Vancouver"],
    "Israel": ["Tel Aviv"]
}

STATUSES = ["operating", "acquired", "closed", "ipo"]
STATUS_WEIGHTS = [0.65, 0.15, 0.15, 0.05]

INVESTOR_TYPES = ["vc", "angel", "accelerator", "corporate", "pe"]

SAMPLE_DESCRIPTIONS = [
    "Next-generation platform revolutionizing enterprise automated decision-making and operational efficiency using scalable AI algorithms.",
    "Decentralized payment infrastructure streamlining international cross-border transactions for small and medium businesses with low overhead.",
    "Comprehensive digital healthcare suite connecting patients directly with board-certified medical specialists via real-time encrypted video consultations.",
    "Sustainable clean energy storage framework accelerating smart grid transition through high-density lithium-iron batteries.",
    "Cloud-native cybersecurity architecture protecting multi-cloud environments against zero-day vulnerabilities and unauthorized intrusion.",
    "Direct-to-consumer e-commerce brand offering hyper-personalized wellness products powered by machine learning recommendation engines.",
    "Interactive STEM learning solution empowering students with immersive hands-on gamified coding challenges and virtual labs.",
    "Autonomous last-mile logistics dispatch service reducing urban carbon footprint and delivery turnaround times by 40%.",
    "Precision drug discovery platform combining high-throughput biological assays with structural computational modeling.",
    "Developer-first workflow optimization engine automating CI/CD pipeline deployments and static code vulnerability auditing."
]


def generate_seed_data(num_startups: int = 60, num_investors: int = 30):
    """
    Generate synthetic seed dataset mimicking Kaggle Crunchbase funding records.
    """
    connection = get_connection()
    if not connection:
        logging.error("Database connection failed. Ensure MySQL is running.")
        return

    logging.info(f"Starting seed data population into startup_db...")
    log_id = log_scraping_activity("kaggle_seed_loader", "local_seed", "in_progress", 0)

    try:
        # 1. Insert Investors
        investor_ids = []
        investor_names = [
            "Sequoia Capital", "Accel Partners", "Y Combinator", "Andreessen Horowitz",
            "Tiger Global", "SoftBank Vision Fund", "Lightspeed Venture Partners",
            "Matrix Partners", "Bessemer Venture Partners", "Index Ventures",
            "Founders Fund", "Benchmark", "GGV Capital", "Insight Partners",
            "General Catalyst", "Elevation Capital", "Kalaari Capital", "Nexus Venture Partners",
            "Blume Ventures", "IvyCap Ventures", "Unicorn India Ventures", "Antler",
            "Techstars", "500 Global", "Peak XV Partners", "Founders Factory",
            "Greylock Partners", "CRV", "First Round Capital", "Sutter Hill Ventures"
        ]

        for i, name in enumerate(investor_names[:num_investors]):
            country = random.choice(COUNTRIES)
            city = random.choice(CITIES[country])
            inv_data = {
                "name": name,
                "investor_type": random.choice(INVESTOR_TYPES),
                "country": country,
                "city": city,
                "investment_stage_preference": random.choice(["seed", "series_a", "series_b"]),
                "total_investments_count": random.randint(5, 50)
            }
            inv_id = insert_investor(connection, inv_data)
            if inv_id:
                investor_ids.append(inv_id)

        logging.info(f"Inserted {len(investor_ids)} investors.")

        # 2. Insert Startups & Funding Rounds
        startups_created = 0
        rounds_created = 0
        links_created = 0

        startup_prefixes = ["Apex", "Nova", "Cyber", "Bio", "Eco", "Data", "Quantum", "Nexus", "Zenith", "Omni", "Velo", "Pulse", "Strat", "Aero", "Hyper"]
        startup_suffixes = ["Tech", "Labs", "AI", "Health", "Pay", "Grid", "Secure", "Logic", "Dynamics", "Systems", "Flow", "IQ", "Wave", "Hub", "Scale"]

        for i in range(1, num_startups + 1):
            s_name = f"{random.choice(startup_prefixes)}{random.choice(startup_suffixes)} {i}"
            industry = random.choice(INDUSTRIES)
            sub_ind = random.choice(SUB_INDUSTRIES[industry])
            country = random.choice(COUNTRIES)
            city = random.choice(CITIES[country])
            founding_yr = random.randint(2012, 2023)
            status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
            desc = random.choice(SAMPLE_DESCRIPTIONS)

            startup_payload = {
                "name": s_name,
                "legal_name": f"{s_name} Inc.",
                "domain": f"https://www.{s_name.lower().replace(' ', '')}.io",
                "industry": industry,
                "sub_industry": sub_ind,
                "country": country,
                "state": f"{city} Region",
                "city": city,
                "founding_year": founding_yr,
                "operating_status": status,
                "short_description": desc,
                "long_description": f"{desc} Founded in {founding_yr} in {city}, {country}, targeting {sub_ind}.",
                "employee_count_range": random.choice(["1-10", "11-50", "51-200", "201-500", "500+"]),
                "total_funding_usd": 0.00,
                "funding_rounds_count": 0,
                "is_active": True if status == "operating" else False
            }

            s_id = insert_startup(connection, startup_payload)
            if not s_id:
                continue

            startups_created += 1

            # Determine funding rounds based on founding year & status
            possible_rounds = ["pre_seed", "seed", "series_a", "series_b", "series_c"]
            if status == "closed":
                num_rounds = random.randint(1, 2)
            elif status == "acquired" or status == "ipo":
                num_rounds = random.randint(3, 5)
            else:
                num_rounds = random.randint(1, 4)

            total_raised = 0.0
            rounds_list = possible_rounds[:num_rounds]
            curr_date = datetime(founding_yr, random.randint(1, 6), random.randint(1, 28))

            for r_type in rounds_list:
                curr_date += timedelta(days=random.randint(180, 450))
                if curr_date > datetime.now():
                    break

                if r_type == "pre_seed":
                    amount = round(random.uniform(50000, 500000), 2)
                elif r_type == "seed":
                    amount = round(random.uniform(500000, 2500000), 2)
                elif r_type == "series_a":
                    amount = round(random.uniform(3000000, 15000000), 2)
                elif r_type == "series_b":
                    amount = round(random.uniform(15000000, 45000000), 2)
                else:
                    amount = round(random.uniform(50000000, 120000000), 2)

                round_payload = {
                    "startup_id": s_id,
                    "round_type": r_type,
                    "amount_raised_usd": amount,
                    "pre_money_valuation_usd": round(amount * random.uniform(3.0, 5.0), 2),
                    "post_money_valuation_usd": round(amount * random.uniform(4.0, 6.0), 2),
                    "funding_date": curr_date.strftime("%Y-%m-%d"),
                    "source_url": f"https://crunchbase.com/funding_round/{s_id}_{r_type}"
                }

                r_id = insert_funding_round(connection, round_payload)
                if r_id:
                    rounds_created += 1
                    total_raised += amount

                    # Select 1 to 3 investors for this round
                    participating_investors = random.sample(investor_ids, k=min(len(investor_ids), random.randint(1, 3)))
                    for idx, inv_id in enumerate(participating_investors):
                        si_payload = {
                            "startup_id": s_id,
                            "investor_id": inv_id,
                            "round_id": r_id,
                            "is_lead_investor": (idx == 0),
                            "investment_amount_usd": round(amount / len(participating_investors), 2)
                        }
                        insert_startup_investor(connection, si_payload)
                        links_created += 1

            # Update startup totals
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE startups SET total_funding_usd = %s, funding_rounds_count = %s WHERE startup_id = %s",
                (total_raised, len(rounds_list), s_id)
            )
            connection.commit()
            cursor.close()

        logging.info(f"Seed data insertion complete!")
        logging.info(f"Summary: {startups_created} Startups, {rounds_created} Funding Rounds, {links_created} Investment Links.")

        # Update log
        if log_id:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE scraping_logs SET status = %s, records_scraped = %s WHERE log_id = %s",
                ("success", startups_created, log_id)
            )
            connection.commit()
            cursor.close()

    except Exception as e:
        logging.error(f"Failed to populate seed data: {e}")
    finally:
        close_connection(connection)


if __name__ == "__main__":
    generate_seed_data()
