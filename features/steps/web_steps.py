######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""Shared Selenium steps adapted from the course lab for the Wishlist Admin UI."""
# pylint: disable=not-callable  # Behave registers its step decorators dynamically.
from behave import then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

ID_PREFIX = "wishlist_"


def field_id(name):
    """Convert a UI field name to its HTML ID."""
    return ID_PREFIX + name.lower().replace(" ", "_")


@when('I visit the "Home Page"')
def visit_home_page(context):
    """Open the running application in the browser."""
    context.driver.get(context.base_url)


@then('I should see "{message}" in the title')
def check_page_title(context, message):
    """Check the current document's title."""
    assert message in context.driver.title, f"Expected {message!r} in {context.driver.title!r}"


@then('I should not see "{text_string}"')
def check_text_absent(context, text_string):
    """Check that the page body omits the text."""
    assert text_string not in context.driver.find_element(By.TAG_NAME, "body").text


@when('I set the "{element_name}" to "{text_string}"')
@when('I change "{element_name}" to "{text_string}"')
def set_field(context, element_name, text_string):
    """Replace a field's value with the given text."""
    element = context.driver.find_element(By.ID, field_id(element_name))
    element.clear()
    element.send_keys(text_string)


@then('the "{element_name}" field should be empty')
def check_field_empty(context, element_name):
    """Check that a form field has been cleared."""
    assert context.driver.find_element(By.ID, field_id(element_name)).get_attribute("value") == ""


@when('I copy the "{element_name}" field')
def copy_field(context, element_name):
    """Save a field's value for another step in the scenario."""
    element = context.driver.find_element(By.ID, field_id(element_name))
    context.clipboard = element.get_attribute("value")


@when('I paste the "{element_name}" field')
def paste_field(context, element_name):
    """Enter the copied value in the given field."""
    set_field(context, element_name, context.clipboard)


@when('I press the "{button}" button')
def press_button(context, button):
    """Click a button by its name, including multiword names."""
    button_id = button.lower().replace(" ", "_") + "-btn"
    context.driver.find_element(By.ID, button_id).click()


@then('I should see the message "{message}"')
def check_message(context, message):
    """Wait for the status message after a browser action."""
    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element((By.ID, "flash_message"), message)
    )


@then('I should see "{name}" in the results')
def check_result(context, name):
    """Wait for the expected text in the search results."""
    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element((By.ID, "search_results"), name)
    )


@then('I should not see "{name}" in the results')
def check_result_absent(context, name):
    """Check that the displayed results omit the specified text."""
    assert name not in context.driver.find_element(By.ID, "search_results").text


@then('I should see "{text_string}" in the "{element_name}" field')
def check_field_value(context, text_string, element_name):
    """Wait for the form to display the expected value."""
    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element_value((By.ID, field_id(element_name)), text_string)
    )
