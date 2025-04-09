# Dynamic GUI Web Scraper

A user-friendly Python application with a Graphical User Interface (GUI) designed to scrape content from one or multiple websites dynamically. It attempts to extract common content elements like headings, paragraphs, links, images, and table data without requiring site-specific rules, saving the results into separate CSV files for each successfully scraped URL.

Project Repository: [https://github.com/mohdazmi03/web_scraper_from_urls/](https://github.com/mohdazmi03/web_scraper_from_urls/)

## Features

*   **Graphical User Interface (GUI):** Built with Tkinter for ease of use.
*   **Multiple URL Input:** Accepts a list of URLs (separated by newlines or commas) in a text box.
*   **Dynamic Content Extraction:** Attempts to scrape common HTML elements (`h1`-`h6`, `p`, `li`, `a`, `img`, `th`, `td`) and significant text chunks, making it adaptable to various website structures.
*   **Asynchronous Scraping:** Uses threading to perform scraping in the background, keeping the GUI responsive.
*   **Status Logging:** Displays real-time progress and status messages directly within the GUI.
*   **CSV Output:** Saves the scraped data for each URL into a separate, automatically named `.csv` file in the same directory as the script.
*   **User-Friendly Controls:** Includes buttons to start scraping and clear inputs/logs.

## Prerequisites

*   **Python 3.x:** Ensure you have Python 3 installed. You can download it from [python.org](https://www.python.org/).
*   **pip:** Python's package installer (usually comes with Python 3).
*   **Tkinter:** Usually included with Python on Windows and macOS. On some Linux distributions, you might need to install it separately (e.g., `sudo apt-get update && sudo apt-get install python3-tk`).

## Installation

1.  **Clone or Download:** Get the project files onto your local machine.
    ```bash
    # Clone the repository
    git clone https://github.com/mohdazmi03/web_scraper_from_urls.git
    cd web_scraper
    ```
    Or download the source code as a ZIP file from the repository page and extract it.

2.  **Install Dependencies:** Navigate to the project directory (`web_scraper`) in your terminal and install the required libraries using pip and the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the Script:** Open your terminal, ensure you are in the `web_scraper` directory, and execute the main Python script:
    ```bash
    python gui_scraper_v2.py
    ```
    *(Based on the file currently in your repository)*

2.  **Enter URLs:** The application window will appear. Paste the full URLs (including `http://` or `https://`) you want to scrape into the text box. You can enter multiple URLs, separated by commas or on new lines.

3.  **Start Scraping:** Click the "Start Scraping" button.

4.  **Monitor Progress:** Watch the "Status Log" area for real-time updates on fetching, parsing, scraping, and saving for each URL. The GUI will remain responsive while scraping occurs in the background.

5.  **Find Output Files:** Once the process completes for a URL, a corresponding `.csv` file will be saved in the same `web_scraper` directory where you ran the script. The filename will be automatically generated based on the URL (e.g., `www.example.com_path_page.csv`).

## Output Format

Each generated CSV file contains the scraped data with the following columns:

*   **type:** Indicates the type of content found (e.g., `heading_h1`, `paragraph`, `link`, `image`, `list_item`, `table_header`, `table_data`, `text_chunk`).
*   **data:** Contains the extracted text content.
    *   For simple text elements (headings, paragraphs, list items, table cells, text chunks), this is the cleaned text.
    *   For links and images, this column contains a string representation of a dictionary holding more details (e.g., `{'text': 'Link Text', 'url': 'https://...'}` or `{'src': 'https://...', 'alt': 'Image Alt Text'}`).

## How It Works (Briefly)

1.  **Fetch:** Uses the `requests` library to download the HTML source code of the provided URL(s).
2.  **Parse:** Uses `BeautifulSoup4` to parse the raw HTML into a structured format.
3.  **Extract:** Iterates through common HTML tags (`h1`-`h6`, `p`, `li`, `a`, `img`, `th`, `td`) within the `<body>` of the page. It extracts relevant information (text, links, image sources/alt text). It also attempts to capture significant text nodes not contained within these primary tags.
4.  **Structure & Save:** Organizes the extracted data into a list, converts it to a Pandas DataFrame, and saves it as a CSV file.

## Limitations & Disclaimer

*   **Ethical Use:** Web scraping can be resource-intensive for websites. Always check a website's `robots.txt` file and Terms of Service before scraping. Scrape responsibly and avoid overloading servers.
*   **JavaScript-Rendered Content:** This scraper primarily works on the initial HTML source code returned by the server. Websites that heavily rely on JavaScript to load or render content *after* the initial page load may not be fully scraped. Tools like Selenium or Playwright might be needed for such sites.
*   **Dynamic Nature:** While designed to be dynamic, the quality and completeness of the scrape depend heavily on the target website's HTML structure and semantic correctness. It may not capture *everything* perfectly from *all* websites.
*   **Login Walls:** This script cannot scrape content hidden behind login pages.
*   **Anti-Scraping Measures:** Websites may employ measures to detect and block scrapers. Excessive scraping could lead to your IP address being temporarily or permanently blocked.

## Contributing

Contributions, issues, and feature requests are welcome. Please check the [Issues page](https://github.com/mohdazmi03/web_scraper/issues) if you want to report a bug or suggest an enhancement.

