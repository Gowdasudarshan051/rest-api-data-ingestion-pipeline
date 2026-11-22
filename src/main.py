
import logging

from src import extract, transform, load


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def run_pipeline():
    try:
        logging.info("========== PIPELINE STARTED ==========")

        # Stage 1: Extract
        logging.info("Starting extraction...")
        extract.main()

        # Stage 2: Transform
        logging.info("Starting transformation...")
        transform.main()

        # Stage 3: Load
        logging.info("Starting MySQL loading...")
        load.main()

        logging.info("========== PIPELINE COMPLETED ==========")
        print("\nPipeline executed successfully!")

    except Exception:
        logging.exception("Pipeline execution failed.")
        print("\nPipeline failed. Check the logs for details.")
        raise


if __name__ == "__main__":
    run_pipeline()
