# 🚀 StartupIQ — Startup Funding Predictor

> A full-stack Business Intelligence web application for analyzing, mining, and predicting startup funding outcomes using real-world data.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.x-orange?logo=mysql)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Pages & Routes](#-pages--routes)
- [Modules](#-modules)
- [ETL Pipeline](#-etl-pipeline)

---

## 🧠 Overview

**StartupIQ** is a data-driven analytics platform that scrapes, processes, mines, and visualizes startup funding data. It provides an interactive BI dashboard powered by Plotly.js, alongside a REST API backend built on Flask and MySQL.

The platform covers the full data lifecycle:

```
Web Scraping → ETL Pipeline → MySQL Database → Analytics Engine → REST API → Interactive Dashboard
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **BI Dashboard** | Interactive Plotly.js charts for funding trends, industry breakdowns & investor analytics |
| 🕷️ **Web Scraping** | Automated startup data collection via `scraping/scraper.py` |
| 🔄 **ETL Pipeline** | Extract → Transform → Load pipeline with background thread execution & run history logging |
| 🔍 **EDA** | Exploratory Data Analysis visualizations across industries, stages, and geographies |
| 🧹 **Preprocessing** | Data cleaning and normalization via `preprocessing/cleaner.py` |
| 🤖 **Data Mining** | K-Means clustering and Apriori association rule mining for market pattern discovery |
| 📝 **Text Mining** | NLP sentiment analysis and WordCloud generation from startup descriptions |
| 💡 **Prediction** | Startup funding success/failure probability prediction |
| 📈 **Insights** | Executive scorecard KPIs: total startups, total funding, success rate, failure rate |
| 🖥️ **ETL Monitor** | Real-time ETL pipeline status monitoring and run history UI |

---

## 🛠️ Tech Stack

### Backend
- **Python 3.10+**
- **Flask** — Web framework & REST API
- **MySQL** — Primary relational database
- **mysql-connector-python** — Database driver
- **python-dotenv** — Environment configuration

### Data & ML
- **pandas / numpy** — Data manipulation
- **scikit-learn** — K-Means clustering, ML preprocessing
- **mlxtend** — Apriori association rule mining
- **NLTK / TextBlob** — Natural language processing & sentiment analysis
- **wordcloud** — WordCloud generation
- **matplotlib / seaborn** — Statistical visualizations

### Frontend
- **Jinja2** — Server-side HTML templating
- **Plotly.js** — Interactive charts and BI visuals
- **Bootstrap 5** — Responsive layout & UI components

---

## 📁 Project Structure

```
Startup-Funding-Predictor/
│
├── app.py                  # Flask application entry point & REST API routes
├── config.py               # Centralized configuration (reads from .env)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
│
├── scraping/
│   └── scraper.py          # Web scraper for startup funding data
│
├── etl/
│   ├── pipeline.py         # Main ETL orchestrator
│   ├── extract.py          # Data extraction logic
│   ├── transform.py        # Data transformation logic
│   ├── load.py             # Database loading logic
│   └── logger.py           # ETL run logger
│
├── preprocessing/
│   └── cleaner.py          # Data cleaning & normalization
│
├── text_mining/
│   └── analyzer.py         # NLP sentiment analysis & WordCloud
│
├── data_mining/
│   ├── clustering.py       # K-Means clustering
│   └── association_rules.py # Apriori market pattern rules
│
├── analysis/
│   └── analytics_engine.py # Core analytics engine (KPIs, charts, tables)
│
├── database/
│   └── db_helper.py        # MySQL connection helper
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   ├── data_collection.html
│   ├── preprocessing.html
│   ├── transformation.html
│   ├── eda.html
│   ├── text_mining.html
│   ├── data_mining.html
│   ├── prediction.html
│   ├── insights.html
│   ├── etl_monitor.html
│   └── about.html
│
├── static/                 # CSS, JS, images
├── dashboard/              # Dashboard-specific assets
├── reports/                # Generated report outputs
├── logs/                   # Application & ETL logs
└── .venv/                  # Python virtual environment
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- MySQL 8.x
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/VedantDG-07/Startup-Funding-Predictor.git
cd Startup-Funding-Predictor
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and fill in your MySQL credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_NAME=startup_db
```

### 5. Set Up the Database

Create the MySQL database:

```sql
CREATE DATABASE startup_db;
```

Then run the ETL pipeline to populate it (see [ETL Pipeline](#-etl-pipeline)).

### 6. Run the Application

```bash
python app.py
```

The app will start at **http://127.0.0.1:5000**

---

## ⚙️ Configuration

All configuration is managed via `config.py` and environment variables in `.env`:

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `localhost` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | _(empty)_ | MySQL password |
| `DB_NAME` | `startup_db` | MySQL database name |
| `SECRET_KEY` | `startupiq-dev-secret` | Flask secret key |
| `FLASK_DEBUG` | `True` | Flask debug mode |
| `FLASK_HOST` | `127.0.0.1` | Flask host |
| `FLASK_PORT` | `5000` | Flask port |
| `REQUEST_TIMEOUT` | `10` | HTTP scraper timeout (seconds) |
| `REQUEST_DELAY` | `1.0` | Delay between scraper requests |
| `MAX_RETRIES` | `3` | Scraper max retry attempts |

---

## 📡 API Reference

All endpoints return JSON with the shape `{ "status": "success", "data": ... }`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/kpis` | Executive scorecard KPIs |
| `GET` | `/api/charts/industry` | Industry funding & company count breakdown |
| `GET` | `/api/charts/funding_stages` | Funding stages distribution (Seed → Series C) |
| `GET` | `/api/charts/investors` | Top investors by portfolio & capital |
| `GET` | `/api/charts/text_mining` | NLP sentiment distribution & WordCloud data |
| `GET` | `/api/charts/clustering` | K-Means cluster profiles & failure probability |
| `GET` | `/api/charts/association_rules` | Apriori rules (Support, Confidence, Lift) |
| `GET` | `/api/startups` | Full startup data table |
| `POST` | `/api/etl/run` | Trigger ETL pipeline in background |
| `GET` | `/api/etl/runs` | ETL pipeline run history & current status |

---

## 🖥️ Pages & Routes

| Route | Page | Description |
|---|---|---|
| `/` | Home | Landing page |
| `/dashboard` | Dashboard | BI charts & KPI scorecard |
| `/data_collection` | Data Collection | Scraping status & data sources |
| `/preprocessing` | Preprocessing | Data cleaning overview |
| `/transformation` | Transformation | ETL transformation steps |
| `/eda` | EDA | Exploratory data analysis visuals |
| `/text_mining` | Text Mining | Sentiment analysis & WordCloud |
| `/data_mining` | Data Mining | Clustering & association rules |
| `/prediction` | Prediction | Funding success predictor |
| `/insights` | Insights | Executive insights & summaries |
| `/etl_monitor` | ETL Monitor | Real-time pipeline status |
| `/about` | About | Project & team information |

---

## 🔬 Modules

### `analysis/analytics_engine.py`
Central analytics hub. Provides:
- `get_executive_kpis()` — Total startups, funding sum, success/failure rates
- `get_industry_analytics()` — Funding by industry sector
- `get_funding_stage_analytics()` — Pre-Seed → Series C distributions
- `get_investor_analytics()` — Top investor rankings
- `get_text_mining_summary()` — Sentiment + WordCloud data
- `get_cluster_analytics()` — K-Means cluster profiles
- `get_startups_table_data()` — Full paginated startup table

### `data_mining/clustering.py`
K-Means clustering to segment startups by funding amount, stage, and success probability.

### `data_mining/association_rules.py`
Apriori algorithm to discover market patterns (e.g., *"startups in FinTech at Series A → 85% likely to reach Series B"*).

### `text_mining/analyzer.py`
NLP pipeline: tokenization, stopword removal, sentiment scoring (positive/neutral/negative), and WordCloud frequency mapping.

### `preprocessing/cleaner.py`
Handles missing values, outlier detection, data type normalization, and feature engineering.

### `scraping/scraper.py`
HTTP-based web scraper with retry logic, request throttling, and structured data extraction.

---

## 🔄 ETL Pipeline

The ETL pipeline (`etl/pipeline.py`) runs as a **non-blocking background thread** and covers:

1. **Extract** (`etl/extract.py`) — Pull raw startup data from scraped sources or CSV
2. **Transform** (`etl/transform/`) — Clean, normalize, and feature-engineer the data
3. **Load** (`etl/load.py`) — Persist processed records into MySQL
4. **Log** (`etl/logger.py`) — Record run metadata to the `etl_runs` table

### Trigger via API

```bash
curl -X POST http://127.0.0.1:5000/api/etl/run
```

### Monitor via API

```bash
curl http://127.0.0.1:5000/api/etl/runs
```

Or navigate to **http://127.0.0.1:5000/etl_monitor** for the live UI.

---

## 📄 License

This project is licensed under the **MIT License**.

---

<div align="center">
  Built with love by <strong>Vedant</strong>
</div>
