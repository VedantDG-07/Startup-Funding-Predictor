"""
StartupIQ - Main Flask Web Application Core & REST API Routing Layer (app.py)
Provides frontend UI routes and REST endpoints delivering JSON data payloads
for Plotly.js charts, executive scorecards, text mining wordclouds, and DMBI insights.
"""

from flask import Flask, render_template, jsonify
from analysis.analytics_engine import AnalyticsEngine
from data_mining.association_rules import AssociationRuleMiner
import threading
from etl.pipeline import run_pipeline
from database.db_helper import get_connection, close_connection

app = Flask(__name__)
analytics_engine = AnalyticsEngine()
rule_miner = AssociationRuleMiner()


# =============================================================================
# HTML PAGE ROUTES
# =============================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/data_collection')
def data_collection():
    return render_template('data_collection.html')

@app.route('/preprocessing')
def preprocessing():
    return render_template('preprocessing.html')

@app.route('/transformation')
def transformation():
    return render_template('transformation.html')

@app.route('/eda')
def eda():
    return render_template('eda.html')

@app.route('/text_mining')
def text_mining():
    return render_template('text_mining.html')

@app.route('/data_mining')
def data_mining():
    return render_template('data_mining.html')

@app.route('/prediction')
def prediction():
    return render_template('prediction.html')

@app.route('/insights')
def insights():
    return render_template('insights.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/etl_monitor')
def etl_monitor():
    return render_template('etl_monitor.html')



# =============================================================================
# REST API DATA ENDPOINTS FOR BI DASHBOARD & PLOTLY
# =============================================================================

@app.route('/api/kpis', methods=['GET'])
def api_kpis():
    """
    Executive scorecard metrics (Total startups, funding sum, failure rate, success rate).
    """
    kpis = analytics_engine.get_executive_kpis()
    return jsonify({"status": "success", "data": kpis})

@app.route('/api/charts/industry', methods=['GET'])
def api_chart_industry():
    """
    Industry funding sum & company count breakdown.
    """
    industry_data = analytics_engine.get_industry_analytics()
    return jsonify({"status": "success", "data": industry_data})

@app.route('/api/charts/funding_stages', methods=['GET'])
def api_chart_funding_stages():
    """
    Funding stages (Pre-Seed, Seed, Series A, B, C) distribution.
    """
    stage_data = analytics_engine.get_funding_stage_analytics()
    return jsonify({"status": "success", "data": stage_data})

@app.route('/api/charts/investors', methods=['GET'])
def api_chart_investors():
    """
    Top investors by portfolio count and capital deployment.
    """
    investor_data = analytics_engine.get_investor_analytics()
    return jsonify({"status": "success", "data": investor_data})

@app.route('/api/charts/text_mining', methods=['GET'])
def api_chart_text_mining():
    """
    NLP sentiment distribution and WordCloud frequency dictionary.
    """
    text_data = analytics_engine.get_text_mining_summary()
    return jsonify({"status": "success", "data": text_data})

@app.route('/api/charts/clustering', methods=['GET'])
def api_chart_clustering():
    """
    K-Means cluster profiles and failure probability distributions.
    """
    cluster_data = analytics_engine.get_cluster_analytics()
    return jsonify({"status": "success", "data": cluster_data})

@app.route('/api/charts/association_rules', methods=['GET'])
def api_chart_association_rules():
    """
    Apriori association rules (Support, Confidence, Lift).
    """
    rules = rule_miner.get_market_pattern_rules()
    return jsonify({"status": "success", "data": rules})

@app.route('/api/startups', methods=['GET'])
def api_startups_table():
    """
    Startup data table payload for interactive UI datatables.
    """
    startups = analytics_engine.get_startups_table_data()
    return jsonify({"status": "success", "data": startups})

# Track background task status in memory
etl_background_status = {"running": False, "last_result": None}

@app.route('/api/etl/run', methods=['POST', 'GET'])
def api_etl_run():
    """
    Triggers the ETL pipeline in a non-blocking background thread.
    """
    global etl_background_status
    if etl_background_status["running"]:
        return jsonify({"status": "error", "message": "ETL pipeline is already running in background."})
        
    def worker():
        global etl_background_status
        try:
            res = run_pipeline(source="web_dashboard")
            etl_background_status["last_result"] = res
        except Exception as e:
            etl_background_status["last_result"] = {"status": "failed", "error": str(e)}
        finally:
            etl_background_status["running"] = False

    etl_background_status["running"] = True
    etl_background_status["last_result"] = None
    thread = threading.Thread(target=worker)
    thread.start()
    
    return jsonify({"status": "success", "message": "ETL pipeline triggered in background."})

@app.route('/api/etl/runs', methods=['GET'])
def api_etl_runs():
    """
    Fetches the history of all ETL pipeline executions and current status.
    """
    global etl_background_status
    conn = get_connection()
    runs = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM etl_runs ORDER BY run_id DESC LIMIT 50")
            runs = cursor.fetchall()
            cursor.close()
        except Exception as e:
            app.logger.error(f"Error fetching ETL runs: {e}")
        finally:
            close_connection(conn)
            
    # Serialize datetime columns
    for r in runs:
        if r.get("started_at"):
            r["started_at"] = r["started_at"].strftime("%Y-%m-%d %H:%M:%S")
        if r.get("completed_at") and r["completed_at"] is not None:
            r["completed_at"] = r["completed_at"].strftime("%Y-%m-%d %H:%M:%S")
            
    return jsonify({
        "status": "success", 
        "data": runs,
        "active_run": etl_background_status
    })



if __name__ == '__main__':
    app.run(debug=True, port=5000)
