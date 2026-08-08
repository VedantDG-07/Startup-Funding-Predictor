import os
import sys
import time
from typing import Dict, Any, List

# Path setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from etl.logger import logger
from etl.extract import ExtractorOrchestrator, SeedExtractorSource, WebDirectoryScraperSource, HackerNewsAPIExtractorSource
from etl.transform import TransformOrchestrator
from etl.load import DatabaseLoader
from database.db_helper import get_connection, close_connection

# Conditional model update classes
from text_mining.analyzer import TextMiningAnalyzer
from data_mining.clustering import StartupClusteringEngine

def run_pipeline(source: str = "manual") -> Dict[str, Any]:
    """
    Independent orchestrator executing Extract -> Transform -> Load.
    Reruns downstream analytics only if new records were inserted or updated.
    """
    start_time = time.time()
    logger.info("Initializing StartupIQ ETL Pipeline...")
    
    loader = DatabaseLoader()
    run_id = loader.log_run_start(source)
    if not run_id:
        logger.error("Failed to initialize ETL run log. Aborting.")
        return {"status": "failed", "error": "Log initialization failed"}
        
    stats = {
        "extracted": 0,
        "transformed": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "duration": "0s",
        "total_startups": 0
    }
    
    try:
        # 1. EXTRACT REAL DATA
        orchestrator = ExtractorOrchestrator()
        
        # Check if database is empty to decide if seed loading is required
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM startups")
            count = cursor.fetchone()[0]
            cursor.close()
            close_connection(conn)
            
            if count == 0:
                logger.info("Database is empty. Adding real SeedExtractorSource to pipeline.")
                orchestrator.add_source(SeedExtractorSource(target_num=30))
        
        # Add real live extractor sources (TechCrunch RSS & HackerNews API)
        orchestrator.add_source(HackerNewsAPIExtractorSource(limit=30, query="funding"))
        orchestrator.add_source(WebDirectoryScraperSource(limit=30))
        
        raw_records = orchestrator.run_all()
        stats["extracted"] = len(raw_records)

        
        # 2. TRANSFORM
        transformer = TransformOrchestrator()
        transformed_records = transformer.transform(raw_records)
        stats["transformed"] = len(transformed_records)
        
        # 3. LOAD
        load_stats = loader.load_records(run_id, transformed_records)
        stats.update({
            "inserted": load_stats.get("inserted", 0),
            "updated": load_stats.get("updated", 0),
            "skipped": load_stats.get("skipped", 0),
            "failed": load_stats.get("failed", 0) + (len(raw_records) - len(transformed_records))
        })
        
        # 4. CONDITIONAL DOWNSTREAM RECOMPUTATION
        total_changed = stats["inserted"] + stats["updated"]
        if total_changed > 0:
            logger.info(f"Detected {total_changed} modified startups. Recalculating models...")
            
            # Recalculate Sentiment & Keywords
            logger.info("Executing Text Mining re-analysis...")
            TextMiningAnalyzer().process_and_store_text_analysis()
            
            # Recalculate Clusters & Risk Profiles
            logger.info("Executing K-Means re-clustering...")
            StartupClusteringEngine(n_clusters=4).run_clustering_and_store()
            
            logger.info("Analytics update complete.")
        else:
            logger.info("No new or modified startups loaded. Skipping downstream analytics recomputation.")
            
        # Get final total startup count
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM startups")
            stats["total_startups"] = cursor.fetchone()[0]
            cursor.close()
            close_connection(conn)
            
        duration = time.time() - start_time
        duration_str = f"{duration:.2f}s"
        stats["duration"] = duration_str
        
        # Save run log
        loader.log_run_end(run_id, stats, "success")
        
        # Output final terminal statistics
        print("\n" + "="*45)
        print("           ETL RUN PIPELINE COMPLETED")
        print("="*45)
        print(f"Run ID             : {run_id}")
        print(f"Source             : {source}")
        print(f"Records Extracted  : {stats['extracted']}")
        print(f"Records Transformed: {stats['transformed']}")
        print(f"Inserted           : {stats['inserted']}")
        print(f"Updated            : {stats['updated']}")
        print(f"Duplicates Skipped : {stats['skipped']}")
        print(f"Failed             : {stats['failed']}")
        print(f"Current Total      : {stats['total_startups']}")
        print(f"Execution Time     : {duration_str}")
        print("="*45 + "\n")
        
        return {"status": "success", "run_id": run_id, "data": stats}
        
    except Exception as e:
        logger.error(f"ETL pipeline execution failed: {e}")
        duration = time.time() - start_time
        stats["duration"] = f"{duration:.2f}s"
        loader.log_run_end(run_id, stats, "failed", str(e))
        return {"status": "failed", "error": str(e), "data": stats}

if __name__ == "__main__":
    run_pipeline("cli_scheduler")
