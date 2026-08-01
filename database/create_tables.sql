-- =============================================================================
-- StartupIQ: Startup Funding Intelligence & Failure Analysis
-- Database Schema Creation Script (Phase 1.4)
-- Database Engine: MySQL 8.0+
-- Database Name: startup_db
-- =============================================================================

CREATE DATABASE IF NOT EXISTS startup_db;
USE startup_db;

-- Drop tables in reverse dependency order for clean recreation if re-executed
DROP TABLE IF EXISTS predictions;
DROP TABLE IF EXISTS text_analysis;
DROP TABLE IF EXISTS startup_investors;
DROP TABLE IF EXISTS funding_rounds;
DROP TABLE IF EXISTS scraping_logs;
DROP TABLE IF EXISTS investors;
DROP TABLE IF EXISTS startups;

-- =============================================================================
-- 1. STARTUPS TABLE
-- Core entity storing profile, operational, and aggregate funding metrics
-- =============================================================================
CREATE TABLE startups (
    startup_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255) DEFAULT NULL,
    domain VARCHAR(255) DEFAULT NULL,
    industry VARCHAR(100) NOT NULL,
    sub_industry VARCHAR(100) DEFAULT NULL,
    country VARCHAR(100) DEFAULT NULL,
    state VARCHAR(100) DEFAULT NULL,
    city VARCHAR(100) DEFAULT NULL,
    founding_year INT DEFAULT NULL,
    operating_status ENUM('operating', 'acquired', 'closed', 'ipo') NOT NULL DEFAULT 'operating',
    short_description TEXT DEFAULT NULL,
    long_description TEXT DEFAULT NULL,
    employee_count_range VARCHAR(50) DEFAULT NULL,
    total_funding_usd DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    funding_rounds_count INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_startups_industry (industry),
    INDEX idx_startups_status (operating_status),
    INDEX idx_startups_founding_year (founding_year),
    INDEX idx_startups_location (country, city),
    INDEX idx_startups_funding (total_funding_usd)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 2. INVESTORS TABLE
-- Entities (VCS, Angels, Corporate VCs, Accelerators) funding startups
-- =============================================================================
CREATE TABLE investors (
    investor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    investor_type ENUM('vc', 'angel', 'accelerator', 'corporate', 'pe', 'other') NOT NULL DEFAULT 'vc',
    country VARCHAR(100) DEFAULT NULL,
    city VARCHAR(100) DEFAULT NULL,
    investment_stage_preference VARCHAR(100) DEFAULT NULL,
    total_investments_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_investors_name (name),
    INDEX idx_investors_type (investor_type),
    INDEX idx_investors_country (country)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 3. FUNDING_ROUNDS TABLE
-- Individual financing events per startup
-- =============================================================================
CREATE TABLE funding_rounds (
    round_id INT AUTO_INCREMENT PRIMARY KEY,
    startup_id INT NOT NULL,
    round_type ENUM('pre_seed', 'seed', 'series_a', 'series_b', 'series_c', 'series_d_plus', 'grant', 'debt', 'angel', 'other') NOT NULL,
    amount_raised_usd DECIMAL(18, 2) DEFAULT NULL,
    pre_money_valuation_usd DECIMAL(18, 2) DEFAULT NULL,
    post_money_valuation_usd DECIMAL(18, 2) DEFAULT NULL,
    funding_date DATE DEFAULT NULL,
    source_url VARCHAR(512) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_funding_rounds_startup 
        FOREIGN KEY (startup_id) REFERENCES startups(startup_id) ON DELETE CASCADE,
        
    INDEX idx_funding_rounds_startup (startup_id),
    INDEX idx_funding_rounds_date (funding_date),
    INDEX idx_funding_rounds_type (round_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 4. STARTUP_INVESTORS TABLE (Junction / Many-to-Many Table)
-- Relates investors to startups and specific funding rounds
-- =============================================================================
CREATE TABLE startup_investors (
    startup_investor_id INT AUTO_INCREMENT PRIMARY KEY,
    startup_id INT NOT NULL,
    investor_id INT NOT NULL,
    round_id INT DEFAULT NULL,
    is_lead_investor BOOLEAN NOT NULL DEFAULT FALSE,
    investment_amount_usd DECIMAL(18, 2) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_si_startup 
        FOREIGN KEY (startup_id) REFERENCES startups(startup_id) ON DELETE CASCADE,
    CONSTRAINT fk_si_investor 
        FOREIGN KEY (investor_id) REFERENCES investors(investor_id) ON DELETE CASCADE,
    CONSTRAINT fk_si_round 
        FOREIGN KEY (round_id) REFERENCES funding_rounds(round_id) ON DELETE SET NULL,
        
    CONSTRAINT uq_startup_investor_round 
        UNIQUE KEY (startup_id, investor_id, round_id),
        
    INDEX idx_si_startup (startup_id),
    INDEX idx_si_investor (investor_id),
    INDEX idx_si_round (round_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 5. SCRAPING_LOGS TABLE
-- Audit log for web scrapers tracking source pipeline execution & health
-- =============================================================================
CREATE TABLE scraping_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    target_url VARCHAR(512) DEFAULT NULL,
    status ENUM('pending', 'in_progress', 'success', 'failed') NOT NULL DEFAULT 'pending',
    records_scraped INT NOT NULL DEFAULT 0,
    error_message TEXT DEFAULT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_scraping_logs_status (status),
    INDEX idx_scraping_logs_source (source_name),
    INDEX idx_scraping_logs_date (scraped_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 6. TEXT_ANALYSIS TABLE
-- NLP outputs (Sentiment analysis, keyword extraction, topic mining)
-- =============================================================================
CREATE TABLE text_analysis (
    analysis_id INT AUTO_INCREMENT PRIMARY KEY,
    startup_id INT NOT NULL,
    sentiment_score DECIMAL(5, 4) DEFAULT NULL, -- Score between -1.0000 and +1.0000
    sentiment_label ENUM('positive', 'neutral', 'negative') DEFAULT NULL,
    extracted_keywords TEXT DEFAULT NULL,
    extracted_topics TEXT DEFAULT NULL,
    summary_text TEXT DEFAULT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_text_analysis_startup 
        FOREIGN KEY (startup_id) REFERENCES startups(startup_id) ON DELETE CASCADE,
        
    INDEX idx_text_analysis_startup (startup_id),
    INDEX idx_text_analysis_sentiment (sentiment_label)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 7. PREDICTIONS TABLE
-- Machine Learning model outputs (Failure prediction risk & Clustering)
-- =============================================================================
CREATE TABLE predictions (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    startup_id INT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    predicted_status ENUM('operating', 'closed', 'acquired') NOT NULL,
    failure_probability DECIMAL(5, 4) NOT NULL, -- Score between 0.0000 and 1.0000
    cluster_id INT DEFAULT NULL,
    cluster_label VARCHAR(100) DEFAULT NULL,
    prediction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_predictions_startup 
        FOREIGN KEY (startup_id) REFERENCES startups(startup_id) ON DELETE CASCADE,
        
    INDEX idx_predictions_startup (startup_id),
    INDEX idx_predictions_model (model_name, model_version),
    INDEX idx_predictions_status (predicted_status),
    INDEX idx_predictions_cluster (cluster_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
