"""Steps for the browser setup smoke scenario."""
# pylint: disable=not-callable  # Behave registers its step decorators dynamically.
from pathlib import Path
from behave import then, when


@when("I open the local BDD test page")
def open_test_page(context):
    """Open the HTML fixture in the configured browser."""
    page = Path(__file__).resolve().parents[1] / "fixtures" / "setup.html"
    context.driver.get(page.as_uri())


@then('the browser title is "{expected_title}"')
def check_page_title(context, expected_title):
    """Check the title returned by Selenium."""
    actual_title = context.driver.title
    assert actual_title == expected_title, f"Expected {expected_title!r}, got {actual_title!r}"
