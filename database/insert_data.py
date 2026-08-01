"""
StartupIQ - Database Ingestion Engine
Handles normalized insertion of startups, investors, funding rounds, junction records,
text mining payloads, and scraping pipeline audit logs into MySQL (startup_db).
"""

import logging
from typing import Dict, Any, Optional, List
import mysql.connector
from mysql.connector import Error
from database.db_helper import get_connection, close_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def log_scraping_activity(
    source_name: str,
    target_url: Optional[str],
    status: str,
    records_scraped: int = 0,
    error_message: Optional[str] = None
) -> Optional[int]:
    """
    Log scraping pipeline execution metadata to scraping_logs table.
    """
    connection = get_connection()
    if not connection:
        logging.error("Failed to connect to DB for logging scraping activity.")
        return None

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO scraping_logs (source_name, target_url, status, records_scraped, error_message)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (source_name, target_url, status, records_scraped, error_message))
        connection.commit()
        log_id = cursor.lastrowid
        cursor.close()
        return log_id
    except Error as e:
        logging.error(f"Error inserting scraping log: {e}")
        return None
    finally:
        close_connection(connection)


def insert_startup(connection, startup: Dict[str, Any]) -> Optional[int]:
    """
    Insert a startup record into the startups table or fetch existing ID by name/domain.
    """
    try:
        cursor = connection.cursor(dictionary=True)
        # Check if startup already exists
        check_query = "SELECT startup_id FROM startups WHERE name = %s LIMIT 1"
        cursor.execute(check_query, (startup["name"],))
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            return existing["startup_id"]

        query = """
            INSERT INTO startups (
                name, legal_name, domain, industry, sub_industry,
                country, state, city, founding_year, operating_status,
                short_description, long_description, employee_count_range,
                total_funding_usd, funding_rounds_count, is_active
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
        """
        values = (
            startup.get("name"),
            startup.get("legal_name"),
            startup.get("domain"),
            startup.get("industry", "Unknown"),
            startup.get("sub_industry"),
            startup.get("country"),
            startup.get("state"),
            startup.get("city"),
            startup.get("founding_year"),
            startup.get("operating_status", "operating"),
            startup.get("short_description"),
            startup.get("long_description"),
            startup.get("employee_count_range"),
            startup.get("total_funding_usd", 0.00),
            startup.get("funding_rounds_count", 0),
            startup.get("is_active", True)
        )
        cursor.execute(query, values)
        connection.commit()
        startup_id = cursor.lastrowid
        cursor.close()
        return startup_id
    except Error as e:
        logging.error(f"Error inserting startup '{startup.get('name')}': {e}")
        return None


def insert_investor(connection, investor: Dict[str, Any]) -> Optional[int]:
    """
    Insert an investor record into the investors table or return existing ID.
    """
    try:
        cursor = connection.cursor(dictionary=True)
        check_query = "SELECT investor_id FROM investors WHERE name = %s LIMIT 1"
        cursor.execute(check_query, (investor["name"],))
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            return existing["investor_id"]

        query = """
            INSERT INTO investors (
                name, investor_type, country, city, investment_stage_preference, total_investments_count
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            investor.get("name"),
            investor.get("investor_type", "vc"),
            investor.get("country"),
            investor.get("city"),
            investor.get("investment_stage_preference"),
            investor.get("total_investments_count", 0)
        )
        cursor.execute(query, values)
        connection.commit()
        investor_id = cursor.lastrowid
        cursor.close()
        return investor_id
    except Error as e:
        logging.error(f"Error inserting investor '{investor.get('name')}': {e}")
        return None


def insert_funding_round(connection, round_data: Dict[str, Any]) -> Optional[int]:
    """
    Insert a funding round event associated with a startup.
    """
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO funding_rounds (
                startup_id, round_type, amount_raised_usd,
                pre_money_valuation_usd, post_money_valuation_usd,
                funding_date, source_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            round_data["startup_id"],
            round_data.get("round_type", "seed"),
            round_data.get("amount_raised_usd"),
            round_data.get("pre_money_valuation_usd"),
            round_data.get("post_money_valuation_usd"),
            round_data.get("funding_date"),
            round_data.get("source_url")
        )
        cursor.execute(query, values)
        connection.commit()
        round_id = cursor.lastrowid
        cursor.close()
        return round_id
    except Error as e:
        logging.error(f"Error inserting funding round for startup_id {round_data.get('startup_id')}: {e}")
        return None


def insert_startup_investor(connection, si_data: Dict[str, Any]) -> Optional[int]:
    """
    Insert a record linking a startup, investor, and optional funding round.
    """
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO startup_investors (
                startup_id, investor_id, round_id, is_lead_investor, investment_amount_usd
            ) VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                is_lead_investor = VALUES(is_lead_investor),
                investment_amount_usd = VALUES(investment_amount_usd)
        """
        values = (
            si_data["startup_id"],
            si_data["investor_id"],
            si_data.get("round_id"),
            si_data.get("is_lead_investor", False),
            si_data.get("investment_amount_usd")
        )
        cursor.execute(query, values)
        connection.commit()
        si_id = cursor.lastrowid
        cursor.close()
        return si_id
    except Error as e:
        logging.error(f"Error linking startup {si_data.get('startup_id')} with investor {si_data.get('investor_id')}: {e}")
        return None


def insert_text_analysis(connection, text_data: Dict[str, Any]) -> Optional[int]:
    """
    Insert text mining / NLP payload for a startup.
    """
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO text_analysis (
                startup_id, sentiment_score, sentiment_label,
                extracted_keywords, extracted_topics, summary_text
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            text_data["startup_id"],
            text_data.get("sentiment_score"),
            text_data.get("sentiment_label"),
            text_data.get("extracted_keywords"),
            text_data.get("extracted_topics"),
            text_data.get("summary_text")
        )
        cursor.execute(query, values)
        connection.commit()
        analysis_id = cursor.lastrowid
        cursor.close()
        return analysis_id
    except Error as e:
        logging.error(f"Error inserting text analysis for startup {text_data.get('startup_id')}: {e}")
        return None
