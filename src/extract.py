import requests
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
LOG_DIR = BASE_DIR / "logs"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# logging configuration
logging.basicConfig(
    level= logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "extraction.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# API configuration
API_URL = "https://jsonplaceholder.typicode.com/posts"
TIMEOUT = 30

def extract_data():
    """
    Extracts data from the API and saves it to a JSON file in the raw data directory.
    """
    logger.info("Starting API extraction")

    try:
        response = requests.get(
            API_URL,
            timeout=TIMEOUT
        )

        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            raise ValueError("Expected API response to be list")

        logger.info(
            "Succesfully extracted %s records",
            len(data)
        )
        return data
    except requests.exceptions.Timeout:
        logger.error("Request timed out after %s seconds", TIMEOUT)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error occurred while trying to connect to the API")
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error occurred: %s", e)
    except requests.exceptions.RequestException as e:
        logger.error("API request failed: %s", e)
    
    return None


def save_raw_data(data):
    """
    Save extracted API data as raw JSON.
    """
    if not data:
        logger.waring("No data available to save")
        return  None
    
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = f'posts_{timestamp}.json'

    filepath = RAW_DATA_DIR / filename

    try:
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

        logger.info("Raw data saved to %s", filepath)

        return filepath

    except OSError as error:
        logger.error("Failed to save raw data: %s", error)

        return None
    
def main():
    """
    Main execution function.
    """

    data = extract_data()

    if data is not None:
        filepath = save_raw_data(data)

        if filepath:
            logger.info("Extraction pipeline completed successfully")
        else:
            logger.error("Extraction completed but saving failed")

    else:
        logger.error("Extraction pipeline failed")


if __name__ == "__main__":
    main()