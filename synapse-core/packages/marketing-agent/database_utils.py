import os
import sqlite3
import json  # Import json module for handling JSON data

DATABASE_FILE = "synapse.db"  # Define the SQLite database file name


def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite database: {e}")
        return None


def retrieve_brand_dna(user_id: str) -> dict:
    """
    Retrieves the brand_dna parameters for a given user from the database.
    """
    conn = None
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Assuming brand_dna table has a user_id column and parameters TEXT column storing JSON
            cursor.execute(
                "SELECT parameters FROM brand_dna WHERE user_id = ?", (user_id,)
            )
            result = cursor.fetchone()
            if result:
                # SQLite stores JSON as TEXT, so we need to parse it
                return json.loads(result["parameters"]) if result["parameters"] else {}
            else:
                print(f"No brand_dna found for user_id: {user_id}")
                return {}
    except sqlite3.Error as e:
        print(f"Error retrieving brand DNA: {e}")
        return {}
    finally:
        if conn:
            conn.close()
