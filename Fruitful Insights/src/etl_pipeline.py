import logging
import sys
from extract import extract_fruit_data, validate_extracted_data
from transform import transform_fruit_data, validate_transformed_data
from load import load_raw_data, load_clean_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def run_etl_pipeline():
    """
    Run the complete ETL pipeline:
    1. Extract from Fruityvice API
    2. Transform data
    3. Load into PostgreSQL
    """
    logger.info("Starting ETL Pipeline")
    logger.info("=" * 50)

    # Step 1: Extract
    logger.info("Step 1: Extracting data...")
    raw_data = extract_fruit_data()

    if not raw_data:
        logger.error("ETL Pipeline failed at Extraction stage")
        return False

    if not validate_extracted_data(raw_data):
        logger.error("ETL Pipeline failed - Invalid extracted data")
        return False

    # Step 2: Transform
    logger.info("Step 2: Transforming data...")
    clean_df = transform_fruit_data(raw_data)

    if clean_df is None:
        logger.error("ETL Pipeline failed at Transformation stage")
        return False

    if not validate_transformed_data(clean_df):
        logger.error("ETL Pipeline failed - Invalid transformed data")
        return False

    # Step 3: Load
    logger.info("💾 Step 3: Loading data...")
    raw_count = load_raw_data(raw_data)
    clean_count = load_clean_data(clean_df)

    if clean_count == 0 and raw_count == 0:
        logger.error("ETL Pipeline failed at Loading stage")
        return False

    # Summary
    logger.info("=" * 50)
    logger.info("ETL Pipeline completed successfully!")
    logger.info(f"Summary:")
    logger.info(f"   Raw records extracted: {len(raw_data)}")
    logger.info(f"   Raw records loaded: {raw_count}")
    logger.info(f"   Clean records loaded: {clean_count}")
    logger.info("=" * 50)

    return True

if __name__ == "__main__":
    success = run_etl_pipeline()
    sys.exit(0 if success else 1)