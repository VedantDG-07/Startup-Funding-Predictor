"""
StartupIQ - Data Mining: Association Rule Mining Module (data_mining/association_rules.py)
Discovers market patterns, investor co-investment syndicates, and sector-funding associations
using the Apriori pattern mining algorithm.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Tuple
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

# Ensure parent project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_helper import get_connection, close_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class AssociationRuleMiner:
    """
    Apriori Pattern Mining Engine for Investor Syndicates & Funding Associations.
    """

    def fetch_investor_baskets(self) -> List[List[str]]:
        """
        Fetch investor co-investment baskets per startup from database.
        """
        conn = get_connection()
        if not conn:
            return []

        try:
            query = """
                SELECT si.startup_id, i.name as investor_name
                FROM startup_investors si
                JOIN investors i ON si.investor_id = i.investor_id
            """
            df = pd.read_sql(query, conn)
            if df.empty:
                return []

            baskets = df.groupby("startup_id")["investor_name"].apply(list).tolist()
            # Filter baskets with at least 2 investors
            co_baskets = [b for b in baskets if len(b) >= 2]
            return co_baskets
        except Exception as e:
            logging.error(f"Error fetching investor baskets: {e}")
            return []
        finally:
            close_connection(conn)

    def fetch_market_pattern_transactions(self) -> List[List[str]]:
        """
        Fetch market attribute transactions combining Industry, Country, Stage, and Status.
        """
        conn = get_connection()
        if not conn:
            return []

        try:
            query = """
                SELECT 
                    s.industry, 
                    s.country, 
                    s.operating_status,
                    fr.round_type
                FROM startups s
                JOIN funding_rounds fr ON s.startup_id = fr.startup_id
            """
            df = pd.read_sql(query, conn)
            if df.empty:
                return []

            transactions = []
            for _, row in df.iterrows():
                tx = [
                    f"Industry:{row['industry']}",
                    f"Country:{row['country']}",
                    f"Status:{row['operating_status']}",
                    f"Stage:{row['round_type']}"
                ]
                transactions.append(tx)

            return transactions
        except Exception as e:
            logging.error(f"Error fetching market transactions: {e}")
            return []
        finally:
            close_connection(conn)

    def mine_association_rules(
        self,
        transactions: List[List[str]],
        min_support: float = 0.05,
        min_confidence: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Run Apriori algorithm and extract association rules (Antecedent -> Consequent).
        """
        if not transactions or len(transactions) < 5:
            logging.warning("Insufficient transactions for Apriori mining.")
            return []

        try:
            te = TransactionEncoder()
            te_ary = te.fit(transactions).transform(transactions)
            df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

            frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)
            if frequent_itemsets.empty:
                logging.warning("No frequent itemsets found with given min_support.")
                return []

            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
            if rules.empty:
                return []

            rules_list = []
            for _, row in rules.iterrows():
                antecedents = list(row["antecedents"])
                consequents = list(row["consequents"])
                rules_list.append({
                    "antecedents": antecedents,
                    "consequents": consequents,
                    "antecedent_str": ", ".join(antecedents),
                    "consequent_str": ", ".join(consequents),
                    "support": round(float(row["support"]), 4),
                    "confidence": round(float(row["confidence"]), 4),
                    "lift": round(float(row["lift"]), 4)
                })

            # Sort by lift descending
            rules_list.sort(key=lambda x: x["lift"], reverse=True)
            return rules_list

        except Exception as e:
            logging.error(f"Error executing Apriori algorithm: {e}")
            return []

    def get_investor_syndicate_rules(self) -> List[Dict[str, Any]]:
        """
        Mine co-investment rules between investors.
        """
        baskets = self.fetch_investor_baskets()
        return self.mine_association_rules(baskets, min_support=0.03, min_confidence=0.2)

    def get_market_pattern_rules(self) -> List[Dict[str, Any]]:
        """
        Mine associations between sector, stage, country, and status.
        """
        txs = self.fetch_market_pattern_transactions()
        return self.mine_association_rules(txs, min_support=0.05, min_confidence=0.3)


if __name__ == "__main__":
    miner = AssociationRuleMiner()
    market_rules = miner.get_market_pattern_rules()
    logging.info(f"Mined {len(market_rules)} market association rules.")
    if market_rules:
        logging.info(f"Top Rule: {market_rules[0]['antecedent_str']} => {market_rules[0]['consequent_str']} (Lift: {market_rules[0]['lift']})")
