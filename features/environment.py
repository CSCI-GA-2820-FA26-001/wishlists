"""Browser hooks adapted from the professor's Fall 2026 lab-flask-bdd."""
# pylint: disable=not-callable  # Selenium resolves these exports at runtime.
import os
from shutil import which
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService


def before_all(context):
    """Expose the same context and environment settings as the course BDD lab."""
    context.base_url = os.getenv("BASE_URL", os.getenv("BDD_BASE_URL", "http://localhost:8080")).rstrip("/")
    context.wait_seconds = int(os.getenv("WAIT_SECONDS", "30"))
    driver = os.getenv("DRIVER", "chrome").lower()
    context.driver = get_firefox() if "firefox" in driver else get_chrome()
    context.add_cleanup(context.driver.quit)
    context.browser = context.driver  # Preserve the existing admin step interface.
    context.driver.implicitly_wait(context.wait_seconds)
    context.driver.set_window_size(1280, 1300)
    context.driver.set_page_load_timeout(context.wait_seconds)
    context.config.setup_logging()


def get_chrome():
    """Create headless Chrome using the image's installed browser and driver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    if os.getenv("CHROME_BINARY"):
        options.binary_location = os.environ["CHROME_BINARY"]
    driver_path = os.getenv("CHROMEDRIVER")
    service = ChromeService(executable_path=driver_path) if driver_path else ChromeService()
    return webdriver.Chrome(service=service, options=options)


def get_firefox():
    """Create the headless Firefox alternative provided by the course image."""
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Read the health endpoint as JSON rather than Firefox's developer viewer.
    options.set_preference("devtools.jsonview.enabled", False)
    service = FirefoxService(executable_path=which("geckodriver"))
    return webdriver.Firefox(service=service, options=options)
