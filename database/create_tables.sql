-- Schema definition for Startup Funding Predictor database tables

CREATE DATABASE IF NOT EXISTS startup_funding_db;
USE startup_funding_db;

-- Startup Companies Table
CREATE TABLE IF NOT EXISTS startups (
    startup_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    location VARCHAR(100),
    founding_year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Funding Rounds Table
CREATE TABLE IF NOT EXISTS funding_rounds (
    round_id INT AUTO_INCREMENT PRIMARY KEY,
    startup_id INT,
    stage VARCHAR(50),
    amount_raised DECIMAL(15, 2),
    funding_date DATE,
    FOREIGN KEY (startup_id) REFERENCES startups(startup_id) ON DELETE CASCADE
);
