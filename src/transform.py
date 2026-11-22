
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
LOG_DIR = BASE_DIR / "logs"

PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "transformation.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def get_latest_raw_file():
    """Find the latest raw JSON file."""

    files = list(RAW_DATA_DIR.glob("posts_*.json"))

    if not files:
        logger.error("No raw JSON files found")
        return None

    latest_file = max(
        files,
        key=lambda file: file.stat().st_mtime
    )

    logger.info("Latest raw file selected: %s", latest_file)
    return latest_file


def load_raw_data(filepath):
    """Load raw JSON data."""

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Expected a list of records")

        logger.info("Loaded %s raw records", len(data))
        return data

    except (OSError, json.JSONDecodeError, ValueError) as error:
        logger.error("Failed to load raw data: %s", error)
        return None


def validate_record(record):
    """Validate individual records."""

    if not isinstance(record, dict):
        return False

    required_fields = ["userId", "id", "title", "body"]

    for field in required_fields:
        if field not in record:
            return False

    return True


def clean_record(record):
    """Clean and standardize records."""

    if not isinstance(record["title"], str):
        raise ValueError("Title must be a string")

    if not isinstance(record["body"], str):
        raise ValueError("Body must be a string")

    cleaned_record = {
        "user_id": int(record["userId"]),
        "post_id": int(record["id"]),
        "title": record["title"].strip(),
        "body": record["body"].strip()
    }

    if cleaned_record["user_id"] <= 0:
        raise ValueError("Invalid user ID")

    if cleaned_record["post_id"] <= 0:
        raise ValueError("Invalid post ID")

    if not cleaned_record["title"]:
        raise ValueError("Empty title")

    return cleaned_record


def transform_data(raw_data):
    """Validate, clean and deduplicate records."""

    logger.info("Starting data transformation")

    transformed_records = []
    seen_ids = set()

    invalid_records = 0
    duplicate_records = 0

    for record in raw_data:

        if not validate_record(record):
            invalid_records += 1
            continue

        try:
            cleaned_record = clean_record(record)

        except (ValueError, TypeError, OverflowError) as error:
            logger.warning("Invalid record: %s", error)
            invalid_records += 1
            continue

        post_id = cleaned_record["post_id"]

        if post_id in seen_ids:
            duplicate_records += 1
            continue

        seen_ids.add(post_id)
        transformed_records.append(cleaned_record)

    logger.info(
        "Transformation summary | Input: %d | Output: %d | Invalid: %d | Duplicates: %d",
        len(raw_data),
        len(transformed_records),
        invalid_records,
        duplicate_records
    )

    return transformed_records


def save_processed_data(data):
    """Save transformed records."""

    if not data:
        logger.warning("No transformed records to save")
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    filename = f"posts_processed_{timestamp}.json"
    filepath = PROCESSED_DATA_DIR / filename

    try:
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        logger.info("Processed data saved: %s", filepath)
        return filepath

    except OSError as error:
        logger.error("Failed to save processed data: %s", error)
        return None


def main():
    """Execute transformation pipeline."""

    logger.info("Transformation pipeline started")

    raw_filepath = get_latest_raw_file()

    if raw_filepath is None:
        return

    raw_data = load_raw_data(raw_filepath)

    if raw_data is None:
        return

    transformed_data = transform_data(raw_data)

    processed_filepath = save_processed_data(transformed_data)

    if processed_filepath:
        logger.info("Transformation pipeline completed successfully")
    else:
        logger.error("Transformation pipeline failed")


if __name__ == "__main__":
    main()
