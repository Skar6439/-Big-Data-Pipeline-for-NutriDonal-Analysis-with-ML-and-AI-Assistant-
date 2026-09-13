import logging
import pandas as pd
from sqlalchemy import create_engine, text
from database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def load_raw_data(raw_data, endpoint="Fruityvice API"):
    """
    Load raw JSON data into the raw_fruits table.

    Args:
        raw_data: List of fruit dictionaries
        endpoint: API endpoint name for reference

    Returns:
        int: Number of rows loaded, or 0 if failed
    """
    if not raw_data:
        logger.warning("No raw data to load")
        return 0

    import json
    conn = get_db_connection()
    if not conn:
        return 0

    try:
        cursor = conn.cursor()

        # Insert raw data as JSONB
        raw_json = json.dumps(raw_data)
        insert_query = """
            INSERT INTO raw_fruits (raw_data, api_endpoint, extracted_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            RETURNING id
        """

        cursor.execute(insert_query, (raw_json, endpoint))
        raw_id = cursor.fetchone()[0]
        conn.commit()

        logger.info(f"Loaded raw data into raw_fruits (id: {raw_id}, {len(raw_data)} fruits)")
        cursor.close()
        return len(raw_data)

    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def load_clean_data(df: pd.DataFrame):
    """
    Load clean DataFrame into the clean_fruits table.
    Handles duplicates using ON CONFLICT (upsert).

    Args:
        df: Clean DataFrame to load

    Returns:
        int: Number of rows loaded or updated
    """
    if df is None or df.empty:
        logger.warning("No clean data to load")
        return 0

    logger.info(f"Starting load of {len(df)} clean records into PostgreSQL")

    conn = get_db_connection()
    if not conn:
        return 0

    try:
        cursor = conn.cursor()

        # Track statistics
        inserted = 0
        updated = 0

        # Insert each row individually to handle conflicts
        for _, row in df.iterrows():
            # Check if fruit already exists
            check_query = "SELECT fruit_id FROM clean_fruits WHERE fruit_id = %s"
            cursor.execute(check_query, (row['fruit_id'],))
            exists = cursor.fetchone()

            if exists:
                # Update existing record
                update_query = """
                    UPDATE clean_fruits 
                    SET name = %s, family = %s, calories = %s, sugar = %s, 
                        carbohydrates = %s, protein = %s, fat = %s, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE fruit_id = %s
                """
                cursor.execute(update_query, (
                    row['name'], row['family'], row['calories'], row['sugar'],
                    row['carbohydrates'], row['protein'], row['fat'],
                    row['fruit_id']
                ))
                updated += 1
            else:
                # Insert new record
                insert_query = """
                    INSERT INTO clean_fruits 
                    (fruit_id, name, family, calories, sugar, carbohydrates, protein, fat)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    row['fruit_id'], row['name'], row['family'], row['calories'],
                    row['sugar'], row['carbohydrates'], row['protein'], row['fat']
                ))
                inserted += 1

        conn.commit()
        cursor.close()

        logger.info(f"Clean data loaded successfully:")
        logger.info(f"   Inserted: {inserted} new records")
        logger.info(f"   Updated: {updated} existing records")
        logger.info(f"   Total: {inserted + updated} records processed")

        return inserted + updated

    except Exception as e:
        logger.error(f"Failed to load clean data: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

# Quick test
if __name__ == "__main__":
    print("🧪 Testing load functions...")
    from extract import extract_fruit_data
    from transform import transform_fruit_data

    # Test with sample data
    raw_data = extract_fruit_data()
    if raw_data:
        clean_df = transform_fruit_data(raw_data)
        if clean_df is not None:
            # Test raw load
            raw_count = load_raw_data(raw_data)
            print(f"Loaded {raw_count} raw records")

            # Test clean load
            clean_count = load_clean_data(clean_df)
            print(f"Loaded {clean_count} clean records")