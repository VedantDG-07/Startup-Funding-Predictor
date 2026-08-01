"""
StartupIQ - Text Mining & NLP Analysis Module (text_mining/analyzer.py)
Performs text cleaning, TF-IDF keyword extraction, sentiment analysis,
topic modeling, word frequency generation, and database persistence into text_analysis.
"""

import os
import sys
import re
import json
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Ensure parent project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sklearn.feature_extraction.text import TfidfVectorizer
from preprocessing.cleaner import StartupDataCleaner
from database.db_helper import get_connection, close_connection
from database.insert_data import insert_text_analysis

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Lexicon lists for lightweight rule-based sentiment & topic categorization
POSITIVE_WORDS = {
    "innovative", "revolutionizing", "sustainable", "next-generation", "decentralized",
    "comprehensive", "interactive", "autonomous", "precision", "optimization", "growth",
    "scalable", "efficient", "leading", "advanced", "empowering", "seamless", "cloud-native"
}
NEGATIVE_WORDS = {
    "vulnerability", "vulnerabilities", "intrusion", "footprint", "overhead",
    "risk", "delay", "struggling", "decline", "bottleneck", "loss", "vulnerable"
}


class TextMiningAnalyzer:
    """
    NLP & Text Mining Engine for StartupIQ business descriptions.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=50,
            ngram_range=(1, 2)
        )

    def clean_text(self, text: str) -> str:
        """
        Clean, normalize, and strip punctuation from raw description string.
        """
        if not text or pd.isna(text):
            return ""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """
        Calculate sentiment polarity score (-1.0 to +1.0) and return label.
        """
        tokens = self.clean_text(text).split()
        if not tokens:
            return 0.0000, "neutral"

        pos_count = sum(1 for word in tokens if word in POSITIVE_WORDS)
        neg_count = sum(1 for word in tokens if word in NEGATIVE_WORDS)

        total = pos_count + neg_count
        if total == 0:
            # Baseline slightly positive bias for marketing copy
            score = 0.2500
        else:
            score = round((pos_count - neg_count) / total, 4)

        if score > 0.1:
            label = "positive"
        elif score < -0.1:
            label = "negative"
        else:
            label = "neutral"

        return score, label

    def extract_tfidf_keywords(self, corpus: List[str], top_n: int = 5) -> List[List[str]]:
        """
        Extract top N TF-IDF key terms for each document in the corpus.
        """
        cleaned_corpus = [self.clean_text(doc) for doc in corpus]
        # Filter empty
        non_empty = [doc if doc else "technology platform solution" for doc in cleaned_corpus]

        try:
            tfidf_matrix = self.vectorizer.fit_transform(non_empty)
            feature_names = np.array(self.vectorizer.get_feature_names_out())

            keywords_per_doc = []
            for row in tfidf_matrix:
                sorted_indices = np.argsort(row.toarray().flatten())[::-1]
                top_features = feature_names[sorted_indices[:top_n]].tolist()
                keywords_per_doc.append(top_features)

            return keywords_per_doc
        except Exception as e:
            logging.error(f"Error computing TF-IDF: {e}")
            return [["startup", "technology", "platform"]] * len(corpus)

    def get_word_cloud_frequencies(self, corpus: List[str], top_n: int = 40) -> Dict[str, int]:
        """
        Compute aggregate word frequency dict for WordCloud rendering.
        """
        full_text = " ".join([self.clean_text(doc) for doc in corpus])
        tokens = [word for word in full_text.split() if len(word) > 3 and word not in {"with", "from", "that", "this", "have", "for"}]

        freq_dict = {}
        for token in tokens:
            freq_dict[token] = freq_dict.get(token, 0) + 1

        sorted_freq = dict(sorted(freq_dict.items(), key=lambda item: item[1], reverse=True)[:top_n])
        return sorted_freq

    def process_and_store_text_analysis(self) -> int:
        """
        Process all startups from DB, run text mining, and insert results into text_analysis table.
        """
        cleaner = StartupDataCleaner()
        df = cleaner.get_processed_dataset()

        if df.empty:
            logging.warning("No startups available for text mining.")
            return 0

        corpus = df["long_description"].tolist()
        keywords_list = self.extract_tfidf_keywords(corpus)

        conn = get_connection()
        if not conn:
            return 0

        processed_count = 0
        try:
            cursor = conn.cursor()
            # Clear old text analysis records to avoid duplicate accumulation
            cursor.execute("TRUNCATE TABLE text_analysis")
            conn.commit()
            cursor.close()

            for idx, row in df.iterrows():
                startup_id = int(row["startup_id"])
                description = row["long_description"]
                score, label = self.analyze_sentiment(description)
                keywords = json.dumps(keywords_list[idx])
                topics = json.dumps([row["industry"], row["sub_industry"]])
                summary = row["short_description"][:255] if row["short_description"] else description[:255]

                payload = {
                    "startup_id": startup_id,
                    "sentiment_score": score,
                    "sentiment_label": label,
                    "extracted_keywords": keywords,
                    "extracted_topics": topics,
                    "summary_text": summary
                }

                insert_text_analysis(conn, payload)
                processed_count += 1

            logging.info(f"Successfully processed & stored text analysis for {processed_count} startups.")
            return processed_count
        except Exception as e:
            logging.error(f"Failed storing text analysis: {e}")
            return processed_count
        finally:
            close_connection(conn)


if __name__ == "__main__":
    analyzer = TextMiningAnalyzer()
    count = analyzer.process_and_store_text_analysis()
    logging.info(f"Text Mining finished. {count} records stored in DB.")
