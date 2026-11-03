"""Exercise the real forms and API through a headless browser."""
# pylint: disable=not-callable  # Third-party lazy exports are resolved at runtime.
from uuid import uuid4
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def field(context, element_id):
    """Locate a control by its stable HTML id."""
    return context.browser.find_element(By.ID, element_id)


def submit(context, form_id):
    """Wait for each request to finish, including repeated identical responses."""
    context.browser.find_element(By.CSS_SELECTOR, f"#{form_id} button").click()
    WebDriverWait(context.browser, 10).until(
        lambda browser: browser.find_element(By.ID, "status").text != "Working…"
    )


def create(context, note="BDD sample"):
    """Create unique test data through the UI without deleting existing records."""
    context.wishlist_name = f"BDD {uuid4().hex}"
    context.note = note
    for element_id, value in (
        ("name", context.wishlist_name), ("customer-id", "1001"), ("note", note)
    ):
        field(context, element_id).clear()
        field(context, element_id).send_keys(value)
    submit(context, "create-form")


@given("I am on the wishlist administration page")
def open_admin(context):
    """Visit the actual application."""
    context.browser.get(f"{context.base_url}/admin")
    assert context.browser.title == "Wishlist administration"


@when("I create a new wishlist for customer 1001")
def create_wishlist(context):
    """Submit required fields and a note."""
    create(context)


@then("I see the saved wishlist details")
def saved_details(context):
    """Verify displayed values and retain the generated resource ID."""
    assert field(context, "result").is_displayed()
    assert field(context, "result-name").text == context.wishlist_name
    assert field(context, "result-customer").text == "1001"
    assert field(context, "result-note").text == context.note
    wishlist_id = field(context, "result-id").text
    assert int(wishlist_id) > 0
    if hasattr(context, "wishlist_id"):
        assert wishlist_id == context.wishlist_id
    context.wishlist_id = wishlist_id


@when("I refresh and retrieve the saved wishlist")
def refresh_and_retrieve(context):
    """Reload clears rendered state; retrieval must read the saved resource."""
    context.browser.refresh()
    assert not field(context, "result").is_displayed()
    retrieve(context, context.wishlist_id)


@when("I retrieve wishlist {wishlist_id}")
def retrieve(context, wishlist_id):
    """Retrieve by the resource ID through the form."""
    field(context, "wishlist-id").clear()
    field(context, "wishlist-id").send_keys(wishlist_id)
    submit(context, "retrieve-form")


@when("I submit the same wishlist again")
def duplicate(context):
    """Leave the submitted form values intact to provoke a conflict."""
    submit(context, "create-form")


@then('I see an error containing "{message}"')
def error_message(context, message):
    """Errors must be visible without leaving stale successful results."""
    assert message in field(context, "status").text
    assert not field(context, "result").is_displayed()
    assert context.browser.find_element(By.CSS_SELECTOR, "#retrieve-form button").is_enabled()
    assert context.browser.find_element(By.CSS_SELECTOR, "#create-form button").is_enabled()


@when("I create a wishlist with HTML in its note")
def markup_note(context):
    """An HTML payload should never become a DOM node."""
    create(context, '<img src=x onerror="window.injected=true">')


@then("the note is displayed as text")
def plain_text_note(context):
    """Check rendering as well as the absence of script execution."""
    saved_details(context)
    assert not field(context, "result-note").find_elements(By.TAG_NAME, "img")
    assert context.browser.execute_script("return window.injected") is None
