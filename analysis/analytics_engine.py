"""
StartupIQ - Business Intelligence Analytics Engine (analysis/analytics_engine.py)
Aggregates relational MySQL data, NLP text outputs, and data mining clusters
into optimized JSON data payloads for Flask REST endpoints and Plotly visuals.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

# Ensure parent project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_helper import get_connection, close_connection
from text_mining.analyzer import TextMiningAnalyzer
from data_mining.association_rules import AssociationRuleMiner

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class AnalyticsEngine:
    """
    Central Business Intelligence Analytics Engine.
    """

    def get_executive_kpis(self) -> Dict[str, Any]:
        """
        Compute top-level executive metrics for dashboard scorecards.
        """
        conn = get_connection()
        if not conn:
            return {}

        try:
            cursor = conn.cursor(dictionary=True)

            # 1. Total Startups & Status Split
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_startups,
                    SUM(CASE WHEN operating_status = 'operating' THEN 1 ELSE 0 END) as operating_count,
                    SUM(CASE WHEN operating_status = 'acquired' THEN 1 ELSE 0 END) as acquired_count,
                    SUM(CASE WHEN operating_status = 'closed' THEN 1 ELSE 0 END) as closed_count,
                    SUM(CASE WHEN operating_status = 'ipo' THEN 1 ELSE 0 END) as ipo_count,
                    SUM(total_funding_usd) as grand_total_funding,
                    AVG(total_funding_usd) as avg_funding_per_startup
                FROM startups
            """)
            kpi_res = cursor.fetchone() or {}

            # 2. Total Funding Rounds & Avg Round Size
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_rounds,
                    AVG(amount_raised_usd) as avg_round_amount
                FROM funding_rounds
            """)
            round_res = cursor.fetchone() or {}

            # 3. Total Investors
            cursor.execute("SELECT COUNT(*) as total_investors FROM investors")
            inv_res = cursor.fetchone() or {}

            cursor.close()

            total_s = kpi_res.get("total_startups") or 0
            closed_s = kpi_res.get("closed_count") or 0
            acquired_s = kpi_res.get("acquired_count") or 0

            return {
                "total_startups": total_s,
                "operating_startups": kpi_res.get("operating_count") or 0,
                "acquired_startups": acquired_s,
                "closed_startups": closed_s,
                "ipo_startups": kpi_res.get("ipo_count") or 0,
                "failure_rate_percent": round((closed_s / total_s * 100), 2) if total_s > 0 else 0.0,
                "success_rate_percent": round(((acquired_s + kpi_res.get("ipo_count", 0)) / total_s * 100), 2) if total_s > 0 else 0.0,
                "grand_total_funding_usd": float(kpi_res.get("grand_total_funding") or 0.0),
                "avg_funding_per_startup_usd": float(kpi_res.get("avg_funding_per_startup") or 0.0),
                "total_rounds": round_res.get("total_rounds") or 0,
                "avg_round_amount_usd": float(round_res.get("avg_round_amount") or 0.0),
                "total_investors": inv_res.get("total_investors") or 0
            }
        except Exception as e:
            logging.error(f"Error computing KPIs: {e}")
            return {}
        finally:
            close_connection(conn)

    def get_industry_analytics(self) -> List[Dict[str, Any]]:
        """
        Industry-wise startup counts, aggregate funding, and success/failure distribution.
        """
        conn = get_connection()
        if not conn:
            return []

        try:
            query = """
                SELECT 
                    industry,
                    COUNT(*) as startup_count,
                    SUM(total_funding_usd) as total_funding_usd,
                    AVG(total_funding_usd) as avg_funding_usd,
                    SUM(CASE WHEN operating_status = 'closed' THEN 1 ELSE 0 END) as closed_count,
                    SUM(CASE WHEN operating_status = 'acquired' THEN 1 ELSE 0 END) as acquired_count
                FROM startups
                GROUP BY industry
                ORDER BY total_funding_usd DESC
            """
            df = pd.read_sql(query, conn)
            if df.empty:
                return []
            df["total_funding_usd"] = df["total_funding_usd"].astype(float)
            df["avg_funding_usd"] = df["avg_funding_usd"].astype(float)
            return df.to_dict(orient="records")
        except Exception as e:
            logging.error(f"Error fetching industry analytics: {e}")
            return []
        finally:
            close_connection(conn)

    def get_funding_stage_analytics(self) -> List[Dict[str, Any]]:
        """
        Distribution of capital and round counts across funding stages.
        """
        conn = get_connection()
        if not conn:
            return []

        try:
            query = """
                SELECT 
                    round_type,
                    COUNT(*) as round_count,
                    SUM(amount_raised_usd) as total_amount_raised,
                    AVG(amount_raised_usd) as avg_amount_raised,
                    AVG(post_money_valuation_usd) as avg_valuation
                FROM funding_rounds
                GROUP BY round_type
                ORDER BY total_amount_raised DESC
            """
            df = pd.read_sql(query, conn)
            if df.empty:
                return []
            df["total_amount_raised"] = df["total_amount_raised"].astype(float)
            df["avg_amount_raised"] = df["avg_amount_raised"].astype(float)
            df["avg_valuation"] = df["avg_valuation"].fillna(0).astype(float)
            return df.to_dict(orient="records")
        except Exception as e:
            logging.error(f"Error fetching stage analytics: {e}")
            return []
        finally:
            close_connection(conn)

    def get_investor_analytics(self) -> List[Dict[str, Any]]:
        """
        Top investors by portfolio count and deployed capital.
        """
        conn = get_connection()
        if not conn:
            return []

        try:
            query = """
                SELECT 
                    i.investor_id,
                    i.name as investor_name,
                    i.investor_type,
                    i.country,
                    COUNT(DISTINCT si.startup_id) as portfolio_startups_count,
                    SUM(si.investment_amount_usd) as total_capital_deployed
                FROM investors i
                LEFT JOIN startup_investors si ON i.investor_id = si.investor_id
                GROUP BY i.investor_id, i.name, i.investor_type, i.country
                ORDER BY portfolio_startups_count DESC, total_capital_deployed DESC
                LIMIT 15
            """
            df = pd.read_sql(query, conn)
            if df.empty:
                return []
            df["total_capital_deployed"] = df["total_capital_deployed"].fillna(0).astype(float)
            return df.to_dict(orient="records")
        except Exception as e:
            logging.error(f"Error fetching investor analytics: {e}")
            return []
        finally:
            close_connection(conn)

    def get_text_mining_summary(self) -> Dict[str, Any]:
        """
        Sentiment label distribution, average sentiment scores, and WordCloud payload.
        """
        conn = get_connection()
        if not conn:
            return {}

        try:
            query = """
                SELECT 
                    t.sentiment_label,
                    COUNT(*) as count,
                    AVG(t.sentiment_score) as avg_score
                FROM text_analysis t
                GROUP BY t.sentiment_label
            """
            df = pd.read_sql(query, conn)
            sentiment_distribution = df.to_dict(orient="records") if not df.empty else []

            # Fetch long descriptions for WordCloud frequency dictionary
            desc_query = "SELECT long_description FROM startups WHERE long_description IS NOT NULL"
            desc_df = pd.read_sql(desc_query, conn)
            corpus = desc_df["long_description"].tolist() if not desc_df.empty else []

            text_analyzer = TextMiningAnalyzer()
            word_freq = text_analyzer.get_word_cloud_frequencies(corpus, top_n=30)

            return {
                "sentiment_distribution": sentiment_distribution,
                "word_cloud_frequencies": word_freq
            }
        except Exception as e:
            logging.error(f"Error fetching text mining summary: {e}")
            return {}
        finally:
            close_connection(conn)

    def get_cluster_analytics(self) -> Dict[str, Any]:
        """
        Cluster size breakdown and metric profiles from predictions table.
        """
        conn = get_connection()
        if not conn:
            return {}

        try:
            query = """
                SELECT 
                    p.cluster_id,
                    p.cluster_label,
                    COUNT(*) as startup_count,
                    AVG(p.failure_probability) as avg_failure_risk,
                    AVG(s.total_funding_usd) as avg_funding_usd,
                    AVG(s.funding_rounds_count) as avg_rounds
                FROM predictions p
                JOIN startups s ON p.startup_id = s.startup_id
                GROUP BY p.cluster_id, p.cluster_label
                ORDER BY p.cluster_id
            """
            df = pd.read_sql(query, conn)
            if df.empty:
                return {}

            df["avg_funding_usd"] = df["avg_funding_usd"].astype(float)
            df["avg_failure_risk"] = df["avg_failure_risk"].astype(float)
            df["avg_rounds"] = df["avg_rounds"].astype(float)

            return {
                "clusters": df.to_dict(orient="records")
            }
        except Exception as e:
            logging.error(f"Error fetching cluster analytics: {e}")
            return {}
        finally:
            close_connection(conn)

    def get_startups_table_data(self) -> List[Dict[str, Any]]:
        """
        Joined table data for interactive UI startup explorer.
        """
        conn = get_connection()
        if not conn:
            return []

        try:
            query = """
                SELECT 
                    s.startup_id,
                    s.name,
                    s.industry,
                    s.sub_industry,
                    s.country,
                    s.city,
                    s.founding_year,
                    s.operating_status,
                    s.total_funding_usd,
                    s.funding_rounds_count,
                    t.sentiment_label,
                    t.sentiment_score,
                    p.cluster_label,
                    p.failure_probability
                FROM startups s
                LEFT JOIN text_analysis t ON s.startup_id = t.startup_id
                LEFT JOIN predictions p ON s.startup_id = p.startup_id
                ORDER BY s.total_funding_usd DESC
            """
            df = pd.read_sql(query, conn)
            if df.empty:
                return []

            df["total_funding_usd"] = df["total_funding_usd"].astype(float)
            df["sentiment_score"] = df["sentiment_score"].fillna(0.0).astype(float)
            df["failure_probability"] = df["failure_probability"].fillna(0.0).astype(float)
            df["sentiment_label"] = df["sentiment_label"].fillna("neutral")
            df["cluster_label"] = df["cluster_label"].fillna("Unclustered")

            return df.to_dict(orient="records")
        except Exception as e:
            logging.error(f"Error fetching startups table data: {e}")
            return []
        finally:
            close_connection(conn)


if __name__ == "__main__":
    engine = AnalyticsEngine()
    kpis = engine.get_executive_kpis()
    logging.info(f"Executive KPIs: {kpis}")
