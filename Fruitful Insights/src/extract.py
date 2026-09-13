import logging
import requests
import json
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def extract_fruit_data(max_retries=3, retry_delay=2, save_raw=True):
    """
    Extract fruit data from Fruityvice API with retry logic.

    Args:
        max_retries (int): Number of retry attempts before giving up
        retry_delay (int): Seconds to wait between retries
        save_raw (bool): Whether to save raw JSON to a file

    Returns:
        list: List of fruit data dictionaries, or None if extraction fails
    """
    # API endpoint for all fruits
    url = "https://www.fruityvice.com/api/fruit/all"

    logger.info(f"Starting extract from Fruityvice API: {url}")

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Request attempt {attempt}/{max_retries}")

            # Make the API request with a timeout
            response = requests.get(url, timeout=10)

            # Check if request was successful
            if response.status_code == 200:
                data = response.json()
                fruit_count = len(data)
                logger.info(f"Request succeeded on attempt {attempt} - {fruit_count} fruits received")

                # Save raw data to file if requested
                if save_raw:
                    raw_dir = Path("data/raw")
                    raw_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y-%m-%d")
                    filename = raw_dir / f"fruityvice_{timestamp}.json"
                    with open(filename, 'w') as f:
                        json.dump(data, f, indent=2)
                    logger.info(f"💾 Saved raw response to {filename}")

                return data

            else:
                logger.warning(f"Attempt {attempt} failed - HTTP {response.status_code}: {response.text[:100]}")

        except requests.exceptions.Timeout:
            logger.warning(f"Attempt {attempt} failed - Timeout")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Attempt {attempt} failed - Connection error")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt} failed - {str(e)[:100]}")
        except json.JSONDecodeError as e:
            logger.warning(f"Attempt {attempt} failed - Invalid JSON response: {e}")

        # If this wasn't the last attempt, wait before retrying
        if attempt < max_retries:
            logger.info(f"⏳ Waiting {retry_delay} seconds before retry...")
            time.sleep(retry_delay)

    # All retries failed
    logger.error(f"Extraction failed after {max_retries} attempts")
    return None

def validate_extracted_data(data):
    """
    Validate that the extracted data has the expected structure.

    Args:
        data (list): The extracted data to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not data:
        logger.error("Data is empty or None")
        return False

    if not isinstance(data, list):
        logger.error(f"Data is not a list (type: {type(data)})")
        return False

    if len(data) == 0:
        logger.error("Data list is empty")
        return False

    # Check first item structure
    first_item = data[0]
    required_keys = ['id', 'name', 'nutritions']
    missing_keys = [key for key in required_keys if key not in first_item]

    if missing_keys:
        logger.error(f"Missing required keys in data: {missing_keys}")
        return False

    logger.info(f"Data validation passed - {len(data)} fruits found")
    return True

# Quick test
if __name__ == "__main__":
    print("🧪 Testing extract function...")
    data = extract_fruit_data()

    if data and validate_extracted_data(data):
        print(f"Successfully extracted {len(data)} fruits!")
        # Preview first fruit
        first_fruit = data[0]
        print(f"\nFirst fruit preview:")
        print(f"   Name: {first_fruit.get('name')}")
        print(f"   Family: {first_fruit.get('family')}")
        print(f"   Calories: {first_fruit.get('nutritions', {}).get('calories')}")
    else:
        print("Extraction failed or data is invalid")