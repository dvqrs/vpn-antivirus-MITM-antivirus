from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time


def create_browser_with_proxy(proxy_address):
    chrome_options = Options()
    # Use HTTP since the TCP proxy is forwarding raw traffic.
    chrome_options.add_argument(f"--proxy-server=http://{proxy_address}")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


if __name__ == "__main__":
    # Use the external TCP proxy endpoint provided by Railway.
    proxy = "maglev.proxy.rlwy.net:56449"
    print("[*] Starting Selenium browser with proxy:", proxy)

    driver = create_browser_with_proxy(proxy)

    # Keep the browser open for testing
    time.sleep(1000000)
    driver.quit()
