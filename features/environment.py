"""Browser lifecycle for the isolated BDD environment."""
# pylint: disable=not-callable  # Third-party lazy exports are resolved at runtime.
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


def before_all(context):
    """Use a configurable URL and a locally installed Chromium/Chrome driver."""
    context.base_url = os.getenv("BDD_BASE_URL", "http://app:8080").rstrip("/")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")  # Chromium runs inside the disposable test container.
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    if os.getenv("CHROME_BINARY"):
        options.binary_location = os.environ["CHROME_BINARY"]
    driver_path = os.getenv("CHROMEDRIVER")
    service = Service(executable_path=driver_path) if driver_path else Service()
    context.browser = webdriver.Chrome(service=service, options=options)
    context.browser.set_page_load_timeout(20)
    context.add_cleanup(context.browser.quit)
