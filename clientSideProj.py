from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time


def create_browser_with_tls_proxy(proxy_address):
    chrome_options = Options()

    chrome_options.add_argument(f"--proxy-server=https://{proxy_address}")


    chrome_options.add_argument("--ignore-certificate-errors")

    chrome_options.set_capability("acceptInsecureCerts", True)

    driver = webdriver.Chrome(options=chrome_options)
    return driver


if __name__ == "__main__":

    proxy = "shortline.proxy.rlwy.net:22343"
    print("[*] Starting Selenium browser with TLS proxy at:", proxy)

    driver = create_browser_with_tls_proxy(proxy)

    time.sleep(1000000)
    driver.quit()
