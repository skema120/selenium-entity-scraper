# Silver Tech Scraper

A robust, class-based web scraper built with Python and Selenium. This tool is designed to extract business registry data (specifically "Silver Tech" entities) from a target Vercel application, handling dynamic content, pagination, and network resilience.

## 📋 Features (Meeting Requirements)

### Core Functionality
* **Dynamic Scraping:** Uses `undetected-chromedriver` to handle dynamic JavaScript rendering and reCAPTCHA flows.
* **Pagination Handling:** Automatically detects and clicks the "Next" button until all pages are traversed.
* **Data Extraction:** robustly extracts Business Name, ID, Status, Filing Date, and Agent Details.
* **Output:** Saves data to `output.jsonl` (JSON Lines format) for easy streaming and appending.

### 🌟 Bonus Features Implemented
1.  **Resume Capability:** The script checks `output.jsonl` on startup. If the script stops, running it again will resume scraping without duplicating records.
2.  **Retry Logic:** Implements a retry mechanism (3 attempts) for finding table rows in case of network lag.
3.  **Rate Limiting:** Includes `polite_sleep()` to randomize delays (2-4 seconds) between pages.
4.  **Separation of Concerns:** Parsing logic (`parse_row`) is decoupled from the navigation loop (`run`).
5.  **Logging:** Full logging implemented (info, warning, error) saving to `scraper.log`.

## 🛠️ Installation

1.  **Prerequisites:**
    * Python 3.x installed.
    * Google Chrome installed.

2.  **Install Dependencies:**
    ```bash
    pip install undetected-chromedriver selenium
    ```

## 🚀 How to Run

1.  Clone this repository.
2.  Run the script:
    ```bash
    python scraper.py
    ```
3.  **Manual Bypass Step:**
    * The browser will open and navigate to the target site.
    * **Action Required:** You must manually solve the reCAPTCHA and click the "Search" button for "Silver Tech".
    * Once the table data is visible in the browser, press **ENTER** in the terminal to let the scraper take over.

## 📂 Output Structure

The data is saved to `output.jsonl`. Each line is a valid JSON object:

```json
{
    "business_name": "Silver Tech Ltd",
    "registration_id": "12345",
    "status": "Active",
    "filing_date": "2023-01-01",
    "agent_details": "John Doe | 123 Main St | john@example.com",
    "agent_name": "John Doe",
    "agent_address": "123 Main St",
    "agent_email": "john@example.com"
}
