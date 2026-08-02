import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import mysql.connector
from mysql.connector import Error

# Path setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from etl.logger import logger
from database.db_helper import get_connection, close_connection
from etl.transform.normalizer import DataNormalizer

class DatabaseLoader:
    """
    Handles incremental loading, duplicate detection, upserts, and metrics logging into MySQL.
    """
    def __init__(self):
        self.normalizer = DataNormalizer()
        self._ensure_etl_runs_table()

    def _ensure_etl_runs_table(self):
        """
        Creates the etl_runs table dynamically if it doesn't exist.
        """
        conn = get_connection()
        if not conn:
            logger.error("Could not verify/create etl_runs table due to database connection issue.")
            return
            
        try:
            cursor = conn.cursor()
            query = """
                CREATE TABLE IF NOT EXISTS etl_runs (
                    run_id INT AUTO_INCREMENT PRIMARY KEY,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    records_extracted INT DEFAULT 0,
                    records_transformed INT DEFAULT 0,
                    records_inserted INT DEFAULT 0,
                    records_updated INT DEFAULT 0,
                    duplicates_skipped INT DEFAULT 0,
                    failed_records INT DEFAULT 0,
                    execution_time VARCHAR(50) DEFAULT NULL,
                    status ENUM('success', 'failed', 'running') NOT NULL DEFAULT 'running',
                    source VARCHAR(100) DEFAULT 'manual',
                    error_message TEXT DEFAULT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            cursor.execute(query)
            conn.commit()
            cursor.close()
            logger.info("Checked/Verified etl_runs table in MySQL.")
        except Error as e:
            logger.error(f"Error creating etl_runs table: {e}")
        finally:
            close_connection(conn)

    def log_run_start(self, source: str) -> Optional[int]:
        """
        Create a new run entry in etl_runs and return its ID.
        """
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            query = "INSERT INTO etl_runs (source, status) VALUES (%s, 'running')"
            cursor.execute(query, (source,))
            conn.commit()
            run_id = cursor.lastrowid
            cursor.close()
            return run_id
        except Error as e:
            logger.error(f"Failed to initialize run log: {e}")
            return None
        finally:
            close_connection(conn)

    def log_run_end(self, run_id: int, stats: Dict[str, Any], status: str = "success", error_msg: Optional[str] = None):
        """
        Complete the run log with all metrics and duration.
        """
        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            query = """
                UPDATE etl_runs 
                SET completed_at = CURRENT_TIMESTAMP,
                    records_extracted = %s,
                    records_transformed = %s,
                    records_inserted = %s,
                    records_updated = %s,
                    duplicates_skipped = %s,
                    failed_records = %s,
                    execution_time = %s,
                    status = %s,
                    error_message = %s
                WHERE run_id = %s
            """
            cursor.execute(query, (
                stats.get("extracted", 0),
                stats.get("transformed", 0),
                stats.get("inserted", 0),
                stats.get("updated", 0),
                stats.get("skipped", 0),
                stats.get("failed", 0),
                stats.get("duration", "0s"),
                status,
                error_msg,
                run_id
            ))
            conn.commit()
            cursor.close()
            logger.info(f"ETL run {run_id} updated with status: {status}")
        except Error as e:
            logger.error(f"Failed to finalize run log: {e}")
        finally:
            close_connection(conn)

    def find_existing_startup(self, cursor, norm_name: str, norm_domain: str, country: str) -> Optional[int]:
        """
        Identifies duplicate startups using:
        1. Base domain match (highest confidence).
        2. Normalized name + Country combination.
        """
        # 1. Match by domain if domain is valid
        if norm_domain:
            query = "SELECT startup_id FROM startups WHERE LOWER(domain) LIKE %s LIMIT 1"
            cursor.execute(query, (f"%{norm_domain}%",))
            res = cursor.fetchone()
            if res:
                return res[0]

        # 2. Match by normalized name + country
        if norm_name and country:
            query = "SELECT startup_id FROM startups WHERE name LIKE %s AND country = %s LIMIT 1"
            cursor.execute(query, (f"%{norm_name}%", country))
            res = cursor.fetchone()
            if res:
                return res[0]
                
        return None

    def load_records(self, run_id: int, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Incremental loader implementing UPSERT with duplicate detection.
        """
        stats = {"inserted": 0, "updated": 0, "skipped": 0, "failed": 0}
        
        conn = get_connection()
        if not conn:
            logger.error("Load failed: No connection to database.")
            stats["failed"] = len(records)
            return stats

        try:
            cursor = conn.cursor()
            
            for r in records:
                try:
                    norm_name = r.get("normalized_name", "")
                    norm_domain = r.get("normalized_domain", "")
                    country = r.get("country", "")
                    
                    # Duplicate check
                    existing_id = self.find_existing_startup(cursor, norm_name, norm_domain, country)
                    
                    if existing_id:
                        # Perform UPDATE (only filling in missing fields to preserve data)
                        update_query = """
                            UPDATE startups 
                            SET legal_name = COALESCE(NULLIF(legal_name, ''), %s),
                                domain = COALESCE(NULLIF(domain, ''), %s),
                                short_description = COALESCE(NULLIF(short_description, ''), %s),
                                long_description = COALESCE(NULLIF(long_description, ''), %s),
                                employee_count_range = COALESCE(NULLIF(employee_count_range, ''), %s)
                            WHERE startup_id = %s
                        """
                        cursor.execute(update_query, (
                            r.get("legal_name"),
                            r.get("domain"),
                            r.get("short_description"),
                            r.get("long_description"),
                            r.get("employee_count_range"),
                            existing_id
                        ))
                        stats["updated"] += 1
                    else:
                        # Perform INSERT
                        insert_query = """
                            INSERT INTO startups (
                                name, legal_name, domain, industry, sub_industry,
                                country, state, city, founding_year, operating_status,
                                short_description, long_description, employee_count_range,
                                total_funding_usd, funding_rounds_count, is_active
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(insert_query, (
                            r.get("name"),
                            r.get("legal_name"),
                            r.get("domain"),
                            r.get("industry"),
                            r.get("sub_industry"),
                            r.get("country"),
                            r.get("state"),
                            r.get("city"),
                            r.get("founding_year"),
                            r.get("operating_status"),
                            r.get("short_description"),
                            r.get("long_description"),
                            r.get("employee_count_range"),
                            r.get("total_funding_usd"),
                            r.get("funding_rounds_count"),
                            r.get("is_active")
                        ))
                        stats["inserted"] += 1
                        
                except Error as record_error:
                    logger.error(f"Record loading failed for '{r.get('name')}': {record_error}")
                    stats["failed"] += 1
                    
            conn.commit()
            cursor.close()
            
        except Error as global_error:
            logger.error(f"Database error during load operation: {global_error}")
            stats["failed"] += len(records) - sum(stats.values())
        finally:
            close_connection(conn)
            
        return stats
