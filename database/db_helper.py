"""
database/db_helper.py – MySQL connection helper for StartupIQ.
"""
import os
import sys
import logging
import mysql.connector
from mysql.connector import Error

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_connection():
    """Establish and return a MySQL database connection."""
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        if connection.is_connected():
            print("[+] Connected to MySQL Database")
            return connection
    except Error as e:
        logging.error(f"Database Connection Error: {e}")
        return None


def close_connection(connection):
    """Close the database connection safely."""
    if connection and connection.is_connected():
        connection.close()
        print("[*] Database Connection Closed")
