
import json
import logging
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv


# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Logging configuration
logging.basicConfig(
    filename=LOG_DIR / "loading.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_latest_processed_file():
    """Find the latest processed JSON file."""

    files = list(PROCESSED_DIR.glob("*.json"))

    if not files:
        raise FileNotFoundError(
            "No processed JSON files found."
        )

    return max(files, key=lambda file: file.stat().st_mtime)


def load_processed_data(file_path):
    """Read processed JSON data."""

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Expected a JSON list of records.")

    return data


def create_connection():
    """Establish MySQL connection."""

    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


def load_data(records):
    """Insert or update records in MySQL."""

    if not records:
        logging.info("No records to load.")
        print("No records to load.")
        return

    connection = None
    cursor = None

    insert_query = """
        INSERT INTO posts (post_id, user_id, title, body)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            user_id = VALUES(user_id),
            title = VALUES(title),
            body = VALUES(body)
    """

    try:
        connection = create_connection()
        cursor = connection.cursor()

        values = [
            (
                record["post_id"],
                record["user_id"],
                record["title"],
                record["body"]
            )
            for record in records
        ]

        cursor.executemany(insert_query, values)
        connection.commit()

        logging.info(
            "Successfully processed %s records.",
            len(values)
        )

        print(f"Successfully processed {len(values)} records.")

    except Exception as error:
        if connection and connection.is_connected():
            connection.rollback()

        logging.exception("Data loading failed.")
        print(f"Data loading failed: {error}")
        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def main():
    try:
        file_path = get_latest_processed_file()

        print(f"Reading: {file_path.name}")

        records = load_processed_data(file_path)

        print(f"Records found: {len(records)}")

        load_data(records)

    except Exception:
        logging.exception("Loading pipeline failed.")
        raise


if __name__ == "__main__":
    main()
