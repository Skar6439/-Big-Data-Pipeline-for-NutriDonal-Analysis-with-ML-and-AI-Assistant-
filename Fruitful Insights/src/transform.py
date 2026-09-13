import logging
import pandas as pd
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def transform_fruit_data(raw_data: List[Dict]) -> Optional[pd.DataFrame]:
    """
    Transform raw fruit data from Fruityvice API into a clean DataFrame.

    Steps:
    1. Extract only needed columns
    2. Handle missing values
    3. Convert data types
    4. Flag or drop invalid records
    5. Remove duplicates

    Args:
        raw_data: List of fruit dictionaries from the API

    Returns:
        pd.DataFrame: Cleaned data ready for loading, or None if failed
    """
    if not raw_data:
        logger.error("No raw data to transform")
        return None

    logger.info(f"Starting transformation on {len(raw_data)} raw records")

    # Track statistics
    original_count = len(raw_data)
    dropped_missing = 0
    flagged_outliers = 0

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(raw_data)

    # Step 1: Extract nutrition data into separate columns
    nutrition_df = pd.json_normalize(df['nutritions'])
    df = pd.concat([df, nutrition_df], axis=1)

    # Step 2: Keep only the columns we need
    columns_to_keep = ['id', 'name', 'family', 'calories', 'sugar',
                       'carbohydrates', 'protein', 'fat']

    # Check which columns exist
    existing_columns = [col for col in columns_to_keep if col in df.columns]
    missing_columns = [col for col in columns_to_keep if col not in df.columns]

    if missing_columns:
        logger.warning(f"Missing columns: {missing_columns}")

    df = df[existing_columns]

    # Step 3: Handle missing values
    initial_count = len(df)
    df = df.dropna(subset=['calories'])  # Calories is our target variable
    dropped_missing = initial_count - len(df)

    if dropped_missing > 0:
        logger.warning(f"⚠️ Dropped {dropped_missing} rows - missing 'calories' column")

    # Step 4: Check for outliers (negative values)
    numeric_cols = ['calories', 'sugar', 'carbohydrates', 'protein', 'fat']
    for col in numeric_cols:
        if col in df.columns:
            # Flag negative values
            negative_count = (df[col] < 0).sum()
            if negative_count > 0:
                logger.warning(f"⚠️ Found {negative_count} rows with negative {col}")
                flagged_outliers += negative_count
                # Replace negative with NaN (or could drop, but let's use a reasonable default)
                df.loc[df[col] < 0, col] = None

    # Step 5: Check for extreme outliers (optional - using IQR method)
    for col in numeric_cols:
        if col in df.columns and df[col].notna().any():
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            if outliers > 0:
                logger.info(f"Found {outliers} potential outliers in {col}")

    # Step 6: Remove duplicates based on 'id'
    df = df.drop_duplicates(subset=['id'], keep='first')

    # Step 7: Rename columns for clarity (optional)
    df = df.rename(columns={
        'id': 'fruit_id',
        'name': 'name',
        'family': 'family',
        'calories': 'calories',
        'sugar': 'sugar',
        'carbohydrates': 'carbohydrates',
        'protein': 'protein',
        'fat': 'fat'
    })

    # Log transformation results
    final_count = len(df)
    logger.info(f"Transformation complete:")
    logger.info(f"   Original: {original_count} records")
    logger.info(f"   Missing values dropped: {dropped_missing}")
    logger.info(f"   Outliers flagged: {flagged_outliers}")
    logger.info(f"   Final clean records: {final_count}")

    return df

def validate_transformed_data(df: pd.DataFrame) -> bool:
    """
    Validate that the transformed data meets quality standards.

    Args:
        df: The transformed DataFrame to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if df is None or df.empty:
        logger.error("Transformed data is empty or None")
        return False

    # Check required columns
    required_columns = ['fruit_id', 'name', 'calories']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False

    # Check for missing values in critical columns
    missing_calories = df['calories'].isna().sum()
    if missing_calories > 0:
        logger.warning(f"⚠️ {missing_calories} rows still missing calories")

    # Check data types
    if not pd.api.types.is_numeric_dtype(df['calories']):
        logger.error("Calories column is not numeric")
        return False

    logger.info("Transformed data validation passed")
    logger.info(f"   Shape: {df.shape}")
    logger.info(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")

    return True

# Quick test (using sample data from extract)
if __name__ == "__main__":
    print("🧪 Testing transform function...")
    from extract import extract_fruit_data

    raw_data = extract_fruit_data()
    if raw_data:
        clean_df = transform_fruit_data(raw_data)
        if clean_df is not None and validate_transformed_data(clean_df):
            print("\nTransformation successful!")
            print("\nFirst 5 rows:")
            print(clean_df.head())
            print(f"\nData types:")
            print(clean_df.dtypes)
        else:
            print("Transformation failed")