"""
StartupIQ - Main Flask Web Application Core & REST API Routing Layer (app.py)
Provides frontend UI routes and REST endpoints delivering JSON data payloads
for Plotly.js charts, executive scorecards, text mining wordclouds, and DMBI insights.
"""

from flask import Flask, render_template, jsonify
from analysis.analytics_engine import AnalyticsEngine
from data_mining.association_rules import AssociationRuleMiner

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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
