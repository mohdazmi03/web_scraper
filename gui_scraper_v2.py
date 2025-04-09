import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import pandas as pd
from urllib.parse import urljoin, urlparse
import re
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import queue

# --- Configuration --- (Same as before)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
REQUEST_TIMEOUT = 15
PRIMARY_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'a', 'img', 'th', 'td'}

# --- Helper Functions --- (Mostly same, but modified to log messages)

def log_message(message_queue: queue.Queue, message: str):
    """Puts a message into the queue for GUI display."""
    if message_queue:
        message_queue.put(message)
    else: # Fallback for non-GUI use
        print(message)

def fetch_page(url: str, message_queue: queue.Queue):
    """Fetches the HTML content of a given URL and logs progress."""
    log_message(message_queue, f"[*] Fetching page: {url}...")
    try:
        # Add scheme if missing (simplistic check)
        original_url = url
        if not url.startswith(('http://', 'https://')):
            log_message(message_queue, "[!] URL missing scheme (http/https), attempting to add 'https://'")
            url = 'https://' + url

        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        effective_url = response.url # Get the final URL after redirects
        log_message(message_queue, f"[+] Successfully fetched page (Status: {response.status_code}) Final URL: {effective_url}")
        return response.text, effective_url
    except requests.exceptions.Timeout:
        log_message(message_queue, f"[!] Error: Request timed out after {REQUEST_TIMEOUT} seconds for {original_url}")
        return None, original_url
    except requests.exceptions.RequestException as e:
        log_message(message_queue, f"[!] Error fetching {original_url}: {e}")
        return None, original_url
    except Exception as e:
        log_message(message_queue, f"[!] An unexpected error occurred during fetching {original_url}: {e}")
        return None, original_url

def generate_filename(url: str) -> str:
    """Generates a safe filename from a URL."""
    if not url:
        return "scraped_data_invalid_url.csv"
    try:
        parsed_url = urlparse(url)
        # Use netloc (domain) and path
        filename = f"{parsed_url.netloc}{parsed_url.path}"
        # Remove http/https, www.
        filename = re.sub(r'^https?://', '', filename)
        filename = re.sub(r'^www\.', '', filename)
        # Replace invalid filename characters with underscores
        filename = re.sub(r'[\\/*?:"<>|]+', '_', filename)
        # Replace remaining slashes with underscores
        filename = filename.replace('/', '_')
        # Remove trailing underscores/dots
        filename = filename.strip('_.')
        # Limit length if necessary (optional)
        max_len = 100
        if len(filename) > max_len:
            filename = filename[:max_len] + '...'
        if not filename: # Handle edge case like "http://"
            filename = "scraped_data"
        return f"{filename}.csv"
    except Exception: # Catch potential errors during parsing unusual URLs
         # Fallback based on raw url replacing invalid chars
         safe_url_part = re.sub(r'[\\/*?:"<>|]+', '_', url.split('//')[-1])
         return f"{safe_url_part[:100]}.csv"


def clean_text(text: str) -> str:
    """Cleans whitespace from text."""
    return ' '.join(text.split()).strip()

# --- Main Scraping Logic --- (Modified to log messages)

def scrape_dynamic_content(soup: BeautifulSoup, base_url: str, message_queue: queue.Queue):
    """
    Dynamically scrapes common HTML elements and logs progress.
    """
    scraped_data = []
    processed_elements = set()

    log_message(message_queue, "[*] Starting dynamic content extraction...")
    start_time = time.time()

    if not soup.body:
        log_message(message_queue, "[!] Warning: Could not find the <body> tag. Scraping might be incomplete.")
        container = soup
    else:
        container = soup.body

    # 1. Scrape specific common elements
    elements_found = container.find_all(list(PRIMARY_TAGS))
    log_message(message_queue, f"[*] Found {len(elements_found)} primary elements to analyze.")

    processed_count = 0
    for element in elements_found:
        element_id = id(element)
        if element_id in processed_elements:
            continue

        tag_name = element.name
        text_content = clean_text(element.get_text())
        record = None

        try: # Add try-except for robustness within the loop
            if tag_name.startswith('h') and len(tag_name) == 2 and tag_name[1].isdigit():
                if text_content:
                    record = {"type": f"heading_{tag_name}", "data": text_content}
            elif tag_name == 'p':
                if text_content:
                    record = {"type": "paragraph", "data": text_content}
            elif tag_name == 'li':
                if text_content:
                    record = {"type": "list_item", "data": text_content}
            elif tag_name == 'a':
                href = element.get('href')
                if href:
                    try:
                        absolute_href = urljoin(base_url, href)
                    except ValueError: # Handle malformed base_url or href
                         absolute_href = href # Fallback
                         log_message(message_queue, f"[!] Warning: Could not create absolute URL for href='{href}' with base='{base_url}'. Using original href.")
                    link_text = text_content or clean_text(element.get('title', '')) or absolute_href
                    record = {"type": "link", "data": {"text": link_text, "url": absolute_href}}
            elif tag_name == 'img':
                src = element.get('data-src') or element.get('src')
                if src:
                    try:
                        absolute_src = urljoin(base_url, src)
                    except ValueError:
                        absolute_src = src
                        log_message(message_queue, f"[!] Warning: Could not create absolute URL for src='{src}' with base='{base_url}'. Using original src.")
                    alt_text = clean_text(element.get('alt', ''))
                    record = {"type": "image", "data": {"src": absolute_src, "alt": alt_text}}
            elif tag_name == 'th':
                 if text_content:
                    record = {"type": "table_header", "data": text_content}
            elif tag_name == 'td':
                 if text_content:
                    record = {"type": "table_data", "data": text_content}

        except Exception as e:
             log_message(message_queue, f"[!] Error processing element <{tag_name}>: {e}")
             continue # Skip this element if processing fails

        if record:
            scraped_data.append(record)
            processed_elements.add(element_id)
            processed_count += 1
            # Add descendants to avoid double processing (more aggressive)
            for desc in element.find_all(True):
                 processed_elements.add(id(desc))
            for text_node in element.find_all(string=True, recursive=False):
                processed_elements.add(id(text_node))

    log_message(message_queue, f"[*] Processed {processed_count} primary elements.")

    # 2. Capture remaining significant text nodes
    log_message(message_queue, "[*] Searching for additional text chunks...")
    additional_text_count = 0
    try:
        all_text_nodes = container.find_all(string=True)
        for element in all_text_nodes:
             element_id = id(element)
             if element_id in processed_elements:
                 continue

             # Ignore text inside script, style, or comment tags, etc.
             if isinstance(element, NavigableString) and element.parent.name in ['script', 'style', 'noscript', 'meta', 'link', 'title', 'head', 'html', 'body']:
                 processed_elements.add(element_id) # Mark as processed even if ignored
                 continue

             text = clean_text(element)
             if text:
                 parent_id = id(element.parent) if hasattr(element, 'parent') else None
                 parent_tag_name = element.parent.name if hasattr(element, 'parent') else None

                 # Check if parent was already processed OR is a primary tag we handled
                 if parent_id not in processed_elements and parent_tag_name not in PRIMARY_TAGS:
                     record = {"type": "text_chunk", "data": text}
                     scraped_data.append(record)
                     additional_text_count += 1

             processed_elements.add(element_id) # Mark as processed
    except Exception as e:
        log_message(message_queue, f"[!] Error during additional text search: {e}")


    end_time = time.time()
    log_message(message_queue, f"[+] Found {len(scraped_data)} total content items ({additional_text_count} additional text chunks) in {end_time - start_time:.2f} seconds.")
    return scraped_data


# --- Main Scraping Workflow for a single URL ---
def process_single_url(url: str, message_queue: queue.Queue):
    """Handles fetching, parsing, scraping, and saving for one URL."""
    log_message(message_queue, f"\n--- Processing URL: {url} ---")

    # Fetch
    html_content, effective_url = fetch_page(url, message_queue)
    if not html_content:
        log_message(message_queue, f"[!] Skipping {url} due to fetch error.")
        return # Stop processing this URL

    # Parse
    log_message(message_queue, "[*] Parsing HTML content...")
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        log_message(message_queue, "[+] HTML parsed successfully.")
    except Exception as e:
        log_message(message_queue, f"[!] Error parsing HTML for {effective_url}: {e}")
        return # Stop processing this URL

    # Scrape
    scraped_rows = scrape_dynamic_content(soup, effective_url, message_queue)

    if not scraped_rows:
        log_message(message_queue, "[!] No scrapable content found for this URL.")
        return # Nothing to save

    # Save to CSV
    filename = generate_filename(effective_url)
    log_message(message_queue, f"[*] Preparing to save data to: {filename}")
    try:
        df = pd.DataFrame(scraped_rows)
        # Convert dict data to string for simpler CSV representation
        df['data'] = df['data'].astype(str)
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        log_message(message_queue, f"✅ Successfully saved {len(df)} rows to {filename}")
    except Exception as e:
        log_message(message_queue, f"[!] Error saving data to CSV ({filename}): {e}")

# --- GUI Application Class ---
class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic Web Scraper")
        self.root.geometry("700x550") # Adjusted size

        # Message Queue for thread communication
        self.message_queue = queue.Queue()

        # --- Input Area ---
        input_frame = ttk.Frame(root, padding="10")
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="Enter URLs (one per line or comma-separated):").pack(anchor=tk.W)
        self.url_input = scrolledtext.ScrolledText(input_frame, height=6, width=80, wrap=tk.WORD)
        self.url_input.pack(fill=tk.X, expand=True)

        # --- Control Buttons ---
        button_frame = ttk.Frame(root, padding="5 10")
        button_frame.pack(fill=tk.X)

        self.scrape_button = ttk.Button(button_frame, text="Start Scraping", command=self.start_scraping_thread)
        self.scrape_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="Clear All", command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.progress = ttk.Progressbar(button_frame, orient=tk.HORIZONTAL, length=200, mode='indeterminate')
        # self.progress.pack(side=tk.LEFT, padx=10, pady=5) # Pack later when running

        # --- Status/Output Area ---
        output_frame = ttk.Frame(root, padding="10 0 10 10") # Padding bottom only
        output_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(output_frame, text="Status Log:").pack(anchor=tk.W)
        self.status_output = scrolledtext.ScrolledText(output_frame, height=15, width=80, wrap=tk.WORD, state=tk.DISABLED)
        self.status_output.pack(fill=tk.BOTH, expand=True)

        # Start checking the queue periodically
        self.check_queue()

    def log_to_gui(self, message):
        """Appends a message to the status text widget."""
        self.status_output.config(state=tk.NORMAL)
        self.status_output.insert(tk.END, message + "\n")
        self.status_output.see(tk.END) # Auto-scroll
        self.status_output.config(state=tk.DISABLED)
        self.root.update_idletasks() # Ensure GUI updates promptly

    def check_queue(self):
        """Checks the message queue and updates the GUI."""
        while not self.message_queue.empty():
            try:
                message = self.message_queue.get_nowait()
                self.log_to_gui(message)
            except queue.Empty:
                pass
            except Exception as e:
                 print(f"Error processing queue message: {e}") # Log errors in console
        # Reschedule check
        self.root.after(100, self.check_queue)

    def clear_all(self):
        """Clears input and output fields."""
        self.url_input.delete('1.0', tk.END)
        self.status_output.config(state=tk.NORMAL)
        self.status_output.delete('1.0', tk.END)
        self.status_output.config(state=tk.DISABLED)
        self.log_to_gui("--- Cleared ---")

    def set_ui_state(self, enabled: bool):
        """Enables or disables UI elements during processing."""
        state = tk.NORMAL if enabled else tk.DISABLED
        busy_state = tk.DISABLED if enabled else tk.NORMAL # Opposite for button

        self.url_input.config(state=state)
        self.scrape_button.config(state=busy_state)
        self.clear_button.config(state=busy_state)

        if not enabled:
            self.progress.pack(side=tk.LEFT, padx=10, pady=5) # Show progress bar
            self.progress.start(10) # Start indeterminate progress
        else:
            self.progress.stop()
            self.progress.pack_forget() # Hide progress bar


    def start_scraping_thread(self):
        """Gets URLs and starts the scraping process in a new thread."""
        url_text = self.url_input.get("1.0", tk.END).strip()
        if not url_text:
            messagebox.showwarning("Input Required", "Please enter at least one URL.")
            return

        # Split by newline or comma, remove empty strings and strip whitespace
        urls = [url.strip() for line in url_text.splitlines() for url in line.split(',') if url.strip()]

        if not urls:
             messagebox.showwarning("Input Required", "No valid URLs found in the input.")
             return

        # Disable UI elements and show progress
        self.set_ui_state(enabled=False)
        self.log_to_gui(f"--- Starting scrape for {len(urls)} URL(s) ---")

        # Create and start the worker thread
        self.worker_thread = threading.Thread(target=self.run_scraper_thread, args=(urls,), daemon=True)
        self.worker_thread.start()

    def run_scraper_thread(self, urls):
        """The function executed by the worker thread."""
        total_urls = len(urls)
        for i, url in enumerate(urls, 1):
            self.log_message_threadsafe(f"\n[{i}/{total_urls}] --- Processing URL: {url} ---")
            try:
                process_single_url(url, self.message_queue)
            except Exception as e:
                self.log_message_threadsafe(f"[!!!] UNHANDLED EXCEPTION while processing {url}: {e}")
            # Optional small delay between requests
            # time.sleep(0.5)

        self.log_message_threadsafe("\n--- Scraping process finished ---")

        # Re-enable UI elements (must be done via queue or root.after to be thread-safe)
        self.root.after(0, self.set_ui_state, True) # Pass True to re-enable

    def log_message_threadsafe(self, message):
        """Helper to put messages into the queue from the thread."""
        self.message_queue.put(message)

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()