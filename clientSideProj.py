from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import threading
import requests
import base64

# --- VirusTotal API helper functions ---
def encode_url(url):
    """
    Encode the URL using URL-safe Base64 encoding without padding.
    VirusTotal API requires this encoding for the URL ID.
    """
    encoded = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    return encoded

def check_url_with_virustotal(url):
    """
    Check the URL using the VirusTotal API.
    Encodes the URL as required, calls the API, and returns True 
    only if the malicious count is greater than zero.
    """
    vt_api_key = "YOUR_VIRUSTOTAL_API_KEY"  # Replace with your API key
    url_id = encode_url(url)
    headers = {"x-apikey": vt_api_key}
    vt_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
    
    try:
        response = requests.get(vt_url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            stats = result.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            malicious_count = stats.get("malicious", 0)
            if malicious_count > 0:
                return True
        else:
            print(f"VirusTotal API error for {url}: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Exception during VirusTotal check for {url}: {e}")
    
    return False

# --- Polling function to check new URLs ---
def poll_tabs(seen_urls, driver):
    """
    Poll the Chrome remote debugging endpoint to get a list of open tabs
    and detect when a new URL is visited.
    
    When a new URL is detected, it is checked with the VirusTotal API.
    If the URL is malicious, the code uses Selenium's window_handles to
    determine its placement (i.e. its order in the list) and then closes the tab.
    """
    debug_url = "http://127.0.0.1:9222/json"
    while True:
        try:
            r = requests.get(debug_url)
            tabs = r.json()
            for tab in tabs:
                url = tab.get("url", "")
                if url and url.startswith("http") and url not in seen_urls:
                    seen_urls.add(url)
                    if check_url_with_virustotal(url):
                        # Use Selenium's window_handles to determine the placement.
                        placement = None
                        for i, handle in enumerate(driver.window_handles, 1):
                            try:
                                driver.switch_to.window(handle)
                                # Normalize URLs (removing trailing slashes) for comparison.
                                if driver.current_url.rstrip('/') == url.rstrip('/'):
                                    placement = i
                                    break
                            except Exception as e:
                                print(f"Error switching to window handle: {e}")
                        if placement:
                            print(f"Malicious tab detected at placement {placement}: {url}")
                        else:
                            print(f"Malicious URL detected (placement unknown): {url}")
                        # Now close the malicious tab.
                        for handle in driver.window_handles:
                            try:
                                driver.switch_to.window(handle)
                                if driver.current_url.rstrip('/') == url.rstrip('/'):
                                    driver.close()
                                    break
                            except Exception as e:
                                print(f"Error closing window handle: {e}")
            time.sleep(5)  # Poll every 5 seconds; adjust as needed
        except Exception as e:
            print("Error polling tabs:", e)
            time.sleep(5)

# --- Function to create the browser with TLS proxy and remote debugging enabled ---
def create_browser_with_tls_proxy(proxy_address):
    chrome_options = Options()
    chrome_options.add_argument(f"--proxy-server=https://{proxy_address}")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.set_capability("acceptInsecureCerts", True)
    
    # Enable remote debugging so we can poll tabs outside of Selenium.
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

if __name__ == "__main__":
    proxy = "shortline.proxy.rlwy.net:22343"
    print("[*] Starting Selenium browser with TLS proxy at:", proxy)
    
    driver = create_browser_with_tls_proxy(proxy)
    
    # A set to keep track of URLs we've already checked.
    seen_urls = set()
    
    # Start a thread to poll Chrome's remote debugging interface.
    poll_thread = threading.Thread(target=poll_tabs, args=(seen_urls, driver), daemon=True)
    poll_thread.start()
    
    try:
        # Keep the main thread alive (or run additional automation logic)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        driver.quit()
