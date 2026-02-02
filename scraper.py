import time
import json
import random
import os
import logging
from typing import Optional, Dict, List, Set
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- CONFIGURATION ---
OUTPUT_FILE = "output.jsonl"
LOG_FILE = "scraper.log"
TARGET_URL = "https://scraping-trial-test.vercel.app/"
MAX_RETRIES = 3

# --- LOGGING SETUP ---
# Requirement: Include logging of errors or important events to a log file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # This also prints to console
    ]
)

class EniScraper:
    """
    A robust Selenium scraper designed to extract business data with
    resume capability, retry logic, and stealth mechanisms.
    """

    def __init__(self):
        self.driver = None
        self.scraped_ids: Set[str] = self.load_existing_progress()
        logging.info(f"Initialized Scraper. Found {len(self.scraped_ids)} existing records.")

    def load_existing_progress(self) -> Set[str]:
        """
        Bonus Feature: Resume Capability.
        Reads the output file to populate a set of already scraped business names.
        """
        ids = set()
        if os.path.exists(OUTPUT_FILE):
            try:
                with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                ids.add(data.get("business_name")) 
                            except json.JSONDecodeError:
                                logging.warning("Skipped malformed line in output file.")
            except Exception as e:
                logging.error(f"Failed to load progress: {e}")
        return ids

    def setup_driver(self):
        """Initializes the undetected_chromedriver with stealth options."""
        logging.info("Setting up Chrome driver...")
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-popup-blocking")
        # options.add_argument("--headless") # Uncomment if GUI is not needed
        try:
            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 30)
            logging.info("Driver started successfully.")
        except Exception as e:
            logging.critical(f"Failed to initialize driver: {e}")
            raise

    def human_bypass_gate(self):
        """
        Pauses execution to allow manual handling of reCAPTCHA and Search initiation.
        """
        logging.info("Navigating to target URL for manual interaction.")
        self.driver.get(TARGET_URL)
        
        # Attempt to pre-fill search box for convenience
        try:
            search_box = self.wait.until(EC.element_to_be_clickable((By.ID, "q")))
            search_box.click()
            search_box.clear()
            search_box.send_keys("LLC")
            logging.info("Search box pre-filled with 'LLC'.")
        except TimeoutException:
            logging.warning("Could not auto-focus search box. Please check manually.")

        print("\n" + "="*60)
        print("ACTION REQUIRED: MANUAL BYPASS")
        print("1. Solve the reCAPTCHA in the browser.")
        print("2. Click the 'Search' button.")
        print("3. Ensure the RESULTS TABLE is visible.")
        print("="*60 + "\n")
        
        input("Press ENTER in this terminal once the data table is visible...")
        logging.info("User confirmed table visibility. Starting automated extraction.")

    def parse_row(self, row_element) -> Optional[Dict]:
        """
        Separation of Logic: Extracts text data from a specific <tr> element.
        Uses JavaScript execution to bypass potential visibility/rendering issues.
        """
        try:
            # JavaScript is used to ensure all text content is captured, 
            # even if hidden by CSS or deeply nested.
            cells = self.driver.execute_script("""
                var cells = arguments[0].getElementsByTagName('td');
                var texts = [];
                for(var i=0; i<cells.length; i++){
                    texts.push(cells[i].textContent.trim());
                }
                return texts;
            """, row_element)

            if not cells or len(cells) < 1:
                return None

            # Data Mapping based on table structure
            # Indices: 0=Name, 1=ID, 2=Status, 3=Date, 4+=Agent Info
            data = {
                "business_name": cells[0],
                "registration_id": cells[1] if len(cells) > 1 else "N/A",
                "status": cells[2] if len(cells) > 2 else "N/A",
                "filing_date": cells[3] if len(cells) > 3 else "N/A",
                "agent_details": " | ".join(cells[4:]) if len(cells) > 4 else "N/A"
            }
            
            # Refined parsing for agent columns if structure allows
            if len(cells) >= 7:
                 data["agent_name"] = cells[4]
                 data["agent_address"] = cells[5]
                 data["agent_email"] = cells[6]

            return data
        except Exception as e:
            logging.error(f"Error parsing row: {e}")
            return None

    def save_record(self, record: Dict):
        """
        Appends a valid record to the JSONL output file.
        Updates the in-memory set to prevent duplicates during this run.
        """
        if record["business_name"] in self.scraped_ids:
            return 

        try:
            with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record) + "\n")
            
            self.scraped_ids.add(record["business_name"])
            logging.info(f"Successfully scraped: {record['business_name']}")
        except IOError as e:
            logging.error(f"File I/O Error while saving: {e}")

    def polite_sleep(self):
        """Implements random delays to mimic human behavior (Rate Limiting)."""
        delay = random.uniform(2.0, 4.0)
        time.sleep(delay)

    def run(self):
        """Main execution flow."""
        self.setup_driver()
        
        try:
            self.human_bypass_gate()
            
            page = 1
            while True:
                logging.info(f"Processing Page {page}...")
                
                # Bonus: Retry Logic for Page Load
                rows = []
                for attempt in range(MAX_RETRIES):
                    try:
                        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
                        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                        if rows: break
                    except TimeoutException:
                        logging.warning(f"Attempt {attempt + 1}/{MAX_RETRIES}: Table rows not found yet...")
                        time.sleep(2)
                
                if not rows:
                    logging.info("No more data rows found. Assuming end of pagination.")
                    break

                # Extraction Loop
                new_records_count = 0
                for row in rows:
                    record = self.parse_row(row)
                    if record:
                        self.save_record(record)
                        new_records_count += 1
                
                if new_records_count == 0:
                    logging.warning(f"Page {page} processed but no new unique records found.")

                # Pagination Logic
                try:
                    next_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Next') or contains(., '>')]")
                    if next_btns and next_btns[0].is_enabled():
                        self.driver.execute_script("arguments[0].click();", next_btns[0])
                        page += 1
                        self.polite_sleep()
                    else:
                        logging.info("Next button disabled or not found. Pagination complete.")
                        break
                except Exception as e:
                    logging.error(f"Pagination error: {e}")
                    break

        except Exception as main_e:
            logging.critical(f"Critical execution failure: {main_e}")
        finally:
            if self.driver:
                logging.info("Closing browser session.")
                self.driver.quit()

if __name__ == "__main__":
    scraper = EniScraper()

    scraper.run()
