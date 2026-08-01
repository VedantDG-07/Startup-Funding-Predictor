"""
StartupIQ - Data Mining: K-Means Clustering Engine (data_mining/clustering.py)
Segments startups into distinct strategic clusters based on funding capital, round velocity,
company age, and operational metrics. Stores cluster profiles into database.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# Ensure parent project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from preprocessing.cleaner import StartupDataCleaner
from database.db_helper import get_connection, close_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CLUSTER_LABELS = {
    0: "Early-Stage Seed Venture",
    1: "High-Growth Scaleup",
    2: "Capital-Intensive Unicorn",
    3: "Mature Steady Performer"
}


class StartupClusteringEngine:
    """
    K-Means Data Mining Engine for Startup Market Segmentation.
    """

    def __init__(self, n_clusters: int = 4):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)

    def prepare_cluster_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        Select and scale numerical features for clustering.
        """
        feature_cols = [
            "total_funding_usd",
            "funding_rounds_count",
            "years_active",
            "annual_funding_velocity"
        ]

        features_df = df[feature_cols].copy()
        # Handle log transform for skewed funding amounts
        features_df["log_total_funding"] = np.log1p(features_df["total_funding_usd"])
        features_df["log_velocity"] = np.log1p(features_df["annual_funding_velocity"])

        cols_to_scale = ["log_total_funding", "funding_rounds_count", "years_active", "log_velocity"]
        scaled_features = self.scaler.fit_transform(features_df[cols_to_scale])
        return scaled_features, cols_to_scale

    def run_clustering_and_store(self) -> Dict[str, Any]:
        """
        Execute K-Means algorithm, profile clusters, and insert results into predictions table.
        """
        cleaner = StartupDataCleaner()
        df = cleaner.get_processed_dataset()

        if df.empty:
            logging.warning("No dataset retrieved for clustering.")
            return {}

        scaled_data, feature_names = self.prepare_cluster_features(df)
        cluster_assignments = self.kmeans.fit_predict(scaled_data)

        df["cluster_id"] = cluster_assignments
        df["cluster_label"] = df["cluster_id"].map(CLUSTER_LABELS)

        # Compute synthetic risk/failure probability score based on funding velocity and operating status
        # Closed companies get higher failure probability, well-funded operating ones get lower failure risk
        df["failure_probability"] = np.where(
            df["operating_status"] == "closed",
            np.random.uniform(0.80, 0.95, size=len(df)),
            np.where(
                df["operating_status"] == "acquired",
                np.random.uniform(0.05, 0.15, size=len(df)),
                np.clip(1.0 - (df["total_funding_usd"] / (df["total_funding_usd"].max() + 1.0)), 0.10, 0.70)
            )
        )
        df["failure_probability"] = df["failure_probability"].round(4)

        # Save to MySQL predictions table
        conn = get_connection()
        if not conn:
            return {}

        stored_count = 0
        try:
            cursor = conn.cursor()
            cursor.execute("TRUNCATE TABLE predictions")
            conn.commit()
            cursor.close()

            for idx, row in df.iterrows():
                cursor = conn.cursor()
                query = """
                    INSERT INTO predictions (
                        startup_id, model_name, model_version,
                        predicted_status, failure_probability,
                        cluster_id, cluster_label
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    int(row["startup_id"]),
                    "KMeans_RiskProfiler",
                    "v1.0",
                    row["operating_status"] if row["operating_status"] in ["operating", "closed", "acquired"] else "operating",
                    float(row["failure_probability"]),
                    int(row["cluster_id"]),
                    str(row["cluster_label"])
                ))
                conn.commit()
                cursor.close()
                stored_count += 1

            logging.info(f"Clustering complete. {stored_count} predictions stored in predictions table.")

            # Compute cluster summary metrics
            cluster_summary = df.groupby("cluster_label").agg(
                startup_count=("startup_id", "count"),
                avg_funding_usd=("total_funding_usd", "mean"),
                avg_rounds=("funding_rounds_count", "mean"),
                avg_years_active=("years_active", "mean")
            ).reset_index().to_dict(orient="records")

            return {
                "total_clustered": stored_count,
                "cluster_summary": cluster_summary
            }

        except Exception as e:
            logging.error(f"Error persisting cluster predictions: {e}")
            return {}
        finally:
            close_connection(conn)


if __name__ == "__main__":
    engine = StartupClusteringEngine(n_clusters=4)
    res = engine.run_clustering_and_store()
    logging.info(f"Clustering Engine Output: {res}")
