"""REST fixtures for Behave Background steps."""
# pylint: disable=not-callable  # Behave registers its step decorators dynamically.
from http import HTTPStatus

import requests
from behave import given

REQUEST_TIMEOUT = 30


@given("the following wishlists")
def load_wishlists(context):
    """Delete all Wishlists and load new ones through the public REST API, like the lab"""
    url = f"{context.base_url}/api/wishlists"

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


@given('the "{name}" wishlist for customer {customer_id:d} has the following items')
def load_wishlist_items(context, name, customer_id):
    """Add the table's items to an existing wishlist through the REST API."""
    url = f"{context.base_url}/api/wishlists"
    response = requests.get(url, params={"customer_id": customer_id}, timeout=REQUEST_TIMEOUT)
    assert response.status_code == HTTPStatus.OK, f"Could not list wishlists: {response.status_code}"
    matches = [wishlist for wishlist in response.json() if wishlist["name"] == name]
    assert len(matches) == 1, f"Expected one wishlist named {name!r} for customer {customer_id}"

    items_url = f"{url}/{matches[0]['id']}/items"
    for row in context.table:
        product_id = int(row["product_id"])
        payload = {"product_id": product_id, "quantity": int(row["quantity"])}
        response = requests.post(items_url, json=payload, timeout=REQUEST_TIMEOUT)
        assert response.status_code == HTTPStatus.CREATED, f"Could not add product {product_id}: {response.status_code}"
