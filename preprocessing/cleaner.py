"""
StartupIQ - Preprocessing & Feature Engineering Module (preprocessing/cleaner.py)
Handles raw data extraction from MySQL, missing value imputation, outlier handling,
data transformation, and feature engineering for Data Mining and BI engines.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np

# Ensure parent project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_helper import get_connection, close_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class StartupDataCleaner:
    """
    Data Cleaning and Feature Engineering pipeline for StartupIQ.
    """

    def __init__(self):
        self.current_year = datetime.now().year

    def fetch_raw_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Fetch raw tables (startups, funding_rounds, investors) from startup_db.
        """
        conn = get_connection()
        if not conn:
            logging.error("Failed to connect to MySQL database.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        try:
            startups_df = pd.read_sql("SELECT * FROM startups", conn)
            rounds_df = pd.read_sql("SELECT * FROM funding_rounds", conn)
            investors_df = pd.read_sql("SELECT * FROM investors", conn)
            logging.info(f"Loaded {len(startups_df)} startups, {len(rounds_df)} rounds, {len(investors_df)} investors from DB.")
            return startups_df, rounds_df, investors_df
        except Exception as e:
            logging.error(f"Error fetching data from MySQL: {e}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        finally:
            close_connection(conn)

    def clean_startups(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and impute startups dataframe.
        """
        if df.empty:
            return df

        cleaned_df = df.copy()

        # Handle missing string fields
        cleaned_df["legal_name"] = cleaned_df["legal_name"].fillna(cleaned_df["name"])
        cleaned_df["domain"] = cleaned_df["domain"].fillna("")
        cleaned_df["sub_industry"] = cleaned_df["sub_industry"].fillna("General")
        cleaned_df["country"] = cleaned_df["country"].fillna("Unknown")
        cleaned_df["city"] = cleaned_df["city"].fillna("Unknown")
        cleaned_df["short_description"] = cleaned_df["short_description"].fillna("")
        cleaned_df["long_description"] = cleaned_df["long_description"].fillna(cleaned_df["short_description"])
        cleaned_df["employee_count_range"] = cleaned_df["employee_count_range"].fillna("1-10")

        # Handle numeric fields & types
        cleaned_df["founding_year"] = pd.to_numeric(cleaned_df["founding_year"], errors="coerce").fillna(2018).astype(int)
        cleaned_df["total_funding_usd"] = pd.to_numeric(cleaned_df["total_funding_usd"], errors="coerce").fillna(0.0)
        cleaned_df["funding_rounds_count"] = pd.to_numeric(cleaned_df["funding_rounds_count"], errors="coerce").fillna(0).astype(int)

        return cleaned_df

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer domain features for clustering, trend analysis, and BI metrics.
        """
        if df.empty:
            return df

        featured_df = df.copy()

        # 1. Company Age / Years Active
        featured_df["years_active"] = self.current_year - featured_df["founding_year"]
        featured_df["years_active"] = featured_df["years_active"].clip(lower=1)

        # 2. Funding per round
        featured_df["funding_per_round"] = np.where(
            featured_df["funding_rounds_count"] > 0,
            featured_df["total_funding_usd"] / featured_df["funding_rounds_count"],
            0.0
        )

        # 3. Annual Funding Velocity (Intensity)
        featured_df["annual_funding_velocity"] = featured_df["total_funding_usd"] / featured_df["years_active"]

        # 4. Operational Status Flags
        featured_df["is_closed"] = (featured_df["operating_status"] == "closed").astype(int)
        featured_df["is_acquired"] = (featured_df["operating_status"] == "acquired").astype(int)
        featured_df["is_ipo"] = (featured_df["operating_status"] == "ipo").astype(int)
        featured_df["is_operating"] = (featured_df["operating_status"] == "operating").astype(int)

        # 5. Funding Log Scale (for clustering stability)
        featured_df["log_total_funding"] = np.log1p(featured_df["total_funding_usd"])

        return featured_df

    def get_processed_dataset(self) -> pd.DataFrame:
        """
        Full pipeline: Fetch -> Clean -> Feature Engineer.
        """
        startups_df, _, _ = self.fetch_raw_data()
        if startups_df.empty:
            logging.warning("No data retrieved for preprocessing.")
            return pd.DataFrame()

        cleaned = self.clean_startups(startups_df)
        processed = self.engineer_features(cleaned)
        logging.info(f"Preprocessing completed. Dataset shape: {processed.shape}")
        return processed


if __name__ == "__main__":
    cleaner = StartupDataCleaner()
    dataset = cleaner.get_processed_dataset()
    if not dataset.empty:
        logging.info(f"Sample Columns: {list(dataset.columns)}")
        logging.info(f"\n{dataset[['name', 'industry', 'years_active', 'total_funding_usd', 'annual_funding_velocity']].head()}")
