"""REST fixtures for Behave Background steps."""
# pylint: disable=not-callable  # Behave registers its step decorators dynamically.
from http import HTTPStatus

import requests
from behave import given

REQUEST_TIMEOUT = 30


@given("the following wishlists")
def load_wishlists(context):
    """Delete all Wishlists and load new ones through the public REST API, like the lab"""
    url = f"{context.base_url}/wishlists"

    # Get a list of all the wishlists and delete them one by one
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    assert response.status_code == HTTPStatus.OK, f"Could not list wishlists: {response.status_code}"
    for wishlist in response.json():
        response = requests.delete(f"{url}/{wishlist['id']}", timeout=REQUEST_TIMEOUT)
        assert response.status_code == HTTPStatus.NO_CONTENT, f"Could not delete wishlist: {response.status_code}"

    # Load the database with the wishlists from the Background table
    for row in context.table:
        payload = {"name": row["name"], "customer_id": int(row["customer_id"]), "note": row.get("note") or None}
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        assert response.status_code == HTTPStatus.CREATED, f"Could not create {row['name']!r}: {response.status_code}"
