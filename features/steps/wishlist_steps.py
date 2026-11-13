"""REST fixtures for Behave Background steps."""
# pylint: disable=not-callable  # Behave registers its step decorators dynamically.
from http import HTTPStatus

import requests
from behave import given

REQUEST_TIMEOUT = 30


def delete_fixture(url):
    """Remove the specific wishlist created by the fixture."""
    response = requests.delete(url, timeout=REQUEST_TIMEOUT)
    assert response.status_code == HTTPStatus.NO_CONTENT, f"Fixture cleanup failed: {response.status_code}"


@given("the following wishlists")
def load_wishlists(context):
    """Create the scenario's wishlist data through the public REST API."""
    url = f"{context.base_url}/wishlists"
    for row in context.table:
        payload = {"name": row["name"], "customer_id": int(row["customer_id"]), "note": row.get("note") or None}
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        assert response.status_code == HTTPStatus.CREATED, f"Could not create {row['name']!r}: {response.status_code}"
        context.add_cleanup(delete_fixture, f"{url}/{response.json()['id']}")
