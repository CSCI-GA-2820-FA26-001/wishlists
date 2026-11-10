"""Read-only checks for the browser test environment."""
# pylint: disable=not-callable  # Behave registers its step decorators dynamically.
import json
from behave import then, when
from selenium.webdriver.common.by import By


@when("I open the service health endpoint")
def open_health(context):
    """Navigate through the browser, without creating application data."""
    context.driver.get(f"{context.base_url}/health")


@then("the browser displays a healthy service")
def health_response(context):
    """Check the actual service response rendered by the browser."""
    response = context.driver.find_element(By.TAG_NAME, "body").text
    assert json.loads(response) == {"status": "OK"}
