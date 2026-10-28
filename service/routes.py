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

"""
WishList Service

This service implements a REST API that allows you to Create, Read, Update
and Delete WishList items
"""

from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.models import WishList, Item, DataValidationError
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Return service information and the wishlist list URL as JSON"""
    # Record requests for the service entry point required by story #8.
    app.logger.info("Request for Wishlist service information")

    # Use the initial service version and generate the resource URL from its existing endpoint.
    response = jsonify(
        name="Wishlist Service",
        version="1.0.0",
        wishlists_url=url_for("list_wishlists"),
    )

    # Log the successful response after constructing the service information.
    app.logger.info("Returning Wishlist service information; 200 OK")
    return response, status.HTTP_200_OK


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

@app.route("/health", methods=["GET"])
def health():
    """Return the service health status."""
    return jsonify(status="OK"), status.HTTP_200_OK


@app.route("/wishlists/<int:wishlist_id>", methods=["DELETE"])
def delete_wishlist(wishlist_id):
    """
    Delete a Wishlist

    This endpoint deletes a Wishlist and its items based on the id.
    It returns 204 No Content whether or not the Wishlist existed.
    """
    app.logger.info("Request to delete Wishlist with id: %s", wishlist_id)

    wishlist = WishList.find(wishlist_id)
    if wishlist:
        wishlist.delete()  # items are removed by the cascade on the relationship
        app.logger.info("Wishlist with id %s deleted", wishlist_id)
    else:
        app.logger.info("Wishlist with id %s not found; nothing to delete", wishlist_id)

    return "", status.HTTP_204_NO_CONTENT


@app.route("/wishlists", methods=["GET"])
def list_wishlists():
    """
    List all Wishlists

    This endpoint returns every Wishlist, with its items, as a JSON array.
    An empty array is returned when there are no Wishlists.
    """
    app.logger.info("Request to list all Wishlists")

    wishlists = WishList.all()
    results = [wishlist.serialize() for wishlist in wishlists]

    app.logger.info("Returning %d Wishlists", len(results))
    return jsonify(results), status.HTTP_200_OK


@app.route("/wishlists/<int:wishlist_id>/items", methods=["POST"])
def create_wishlist_item(wishlist_id):
    """
    Add a product to a Wishlist

    This endpoint creates a new item in the Wishlist identified by wishlist_id
    """
    app.logger.info("Request to add an item to Wishlist with id: %s", wishlist_id)

    wishlist = WishList.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Wishlist with id '{wishlist_id}' was not found.",
        )

    data = request.get_json()
    if not isinstance(data, dict):
        raise DataValidationError("Invalid Item: request body must be a JSON object")

    data["wishlist_id"] = wishlist_id
    data.setdefault("quantity", 1)

    item = Item()
    item.deserialize(data)
    if isinstance(item.product_id, bool) or not isinstance(item.product_id, int):
        raise DataValidationError("Invalid Item: product_id must be an integer")
    item.create()

    app.logger.info("Item with id %s added to Wishlist %s", item.id, wishlist_id)
    return jsonify(item.serialize()), status.HTTP_201_CREATED


@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["GET"])
def get_wishlist_item(wishlist_id, item_id):
    """
    Retrieve a product in a Wishlist

    This endpoint returns the item identified by item_id in the Wishlist identified by wishlist_id
    """
    app.logger.info(
        "Request to retrieve Item with id: %s from Wishlist with id: %s",
        item_id,
        wishlist_id,
    )

    wishlist = WishList.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Wishlist with id '{wishlist_id}' was not found.",
        )

    item = Item.find(item_id)
    if not item or item.wishlist_id != wishlist_id:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Item with id '{item_id}' was not found in Wishlist '{wishlist_id}'.",
        )

    app.logger.info("Returning Item with id %s from Wishlist %s", item_id, wishlist_id)
    return jsonify(item.serialize()), status.HTTP_200_OK


@app.route("/wishlists", methods=["POST"])
def create_wishlist():
    """Creates a Wishlist"""
    app.logger.info("Request to create a Wishlist")
    wishlist = WishList()
    wishlist.deserialize(request.get_json())
    existing = WishList.query.filter_by(
        customer_id=wishlist.customer_id,
        name=wishlist.name,
    ).first()
    if existing:
        abort(
            status.HTTP_409_CONFLICT,
            description="Wishlist already exists for this customer",
        )
    wishlist.create()
    app.logger.info("Wishlist with id %s created", wishlist.id)
    location_url = url_for("get_wishlist", wishlist_id=wishlist.id, _external=True)
    return (
        jsonify(wishlist.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


# Update one item identified within its wishlist, matching the story #14 URL structure.
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["PUT"])
def update_wishlist_item(wishlist_id, item_id):
    """Update an existing wishlist item and return its JSON"""
    # Log both IDs to identify the requested resource during debugging.
    app.logger.info("Request to update item %s in wishlist %s", item_id, wishlist_id)

    # Require the parent to exist and prevent updates to an item from another wishlist.
    if WishList.find(wishlist_id) is None:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Wishlist with id '{wishlist_id}' was not found",
        )
    item = Item.find(item_id)
    if item is None or item.wishlist_id != wishlist_id:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Item with id '{item_id}' was not found in Wishlist '{wishlist_id}'",
        )

    # Require a JSON object before passing its fields to the existing model validation.
    data = request.get_json()
    if not isinstance(data, dict):
        raise DataValidationError("Item data must be a JSON object")

    # Reject implicit database conversions; a product ID must be a JSON integer, not a boolean.
    product_id = data.get("product_id")
    if isinstance(product_id, bool) or not isinstance(product_id, int):
        raise DataValidationError("product_id is required and must be an integer")

    # Match the existing nullable String(256) column before changing the persisted item.
    note = data.get("note")
    if note is not None and (not isinstance(note, str) or len(note) > 256):
        raise DataValidationError("note must be null or a string of at most 256 characters")

    # Validate on an unsaved object so rejected input does not partially alter the stored item.
    candidate = Item()
    candidate.deserialize({**data, "wishlist_id": wishlist_id})

    # Copy only editable fields, preserving the item's ID and its wishlist association.
    item.product_id = candidate.product_id
    item.quantity = candidate.quantity
    item.note = candidate.note
    item.update()

    # Log success only after the database update has completed.
    app.logger.info("Item %s in wishlist %s updated; returning 200 OK", item_id, wishlist_id)

    # Return the updated item itself, rather than the entire wishlist, as required by #15.
    return jsonify(item.serialize()), status.HTTP_200_OK


# Delete one Item record within its wishlist, preserving the parent wishlist.
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["DELETE"])
def delete_wishlist_item(wishlist_id, item_id):
    """Delete an item from a wishlist and return an empty 204 response"""
    # Record the requested parent and item IDs for debugging.
    app.logger.info("Request to delete item %s from wishlist %s", item_id, wishlist_id)

    # Match both IDs so an item belonging to another wishlist cannot be deleted.
    item = Item.query.filter_by(id=item_id, wishlist_id=wishlist_id).first()
    if item is not None:
        item.delete()
        # Log success only after the existing model method commits the deletion.
        app.logger.info("Item %s deleted from wishlist %s; returning 204 No Content", item_id, wishlist_id)
    else:
        # An absent item under this URL requires no deletion, including an absent parent.
        app.logger.info("Item %s not found in wishlist %s; returning 204 No Content", item_id, wishlist_id)

    # Story #3 returns no response body whether or not the item was present.
    return "", status.HTTP_204_NO_CONTENT


@app.route("/wishlists/<int:wishlist_id>", methods=["PUT"])
def update_wishlist(wishlist_id):
    """Updates a Wishlist"""
    app.logger.info("Request to update Wishlist with id %s", wishlist_id)
    wishlist = WishList.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Wishlist with id '{wishlist_id}' was not found",
        )
    data = request.get_json()
    # Validate on a detached copy so a rejected request leaves the record untouched
    updated = WishList().deserialize(data)
    if updated.customer_id != wishlist.customer_id:
        abort(
            status.HTTP_400_BAD_REQUEST,
            description="customer_id of a Wishlist cannot be changed",
        )
    existing = WishList.query.filter(
        WishList.id != wishlist_id,
        WishList.customer_id == updated.customer_id,
        WishList.name == updated.name,
    ).first()
    if existing:
        abort(
            status.HTTP_409_CONFLICT,
            description="Wishlist already exists for this customer",
        )
    wishlist.deserialize(data)
    wishlist.update()
    app.logger.info("Wishlist with id %s updated", wishlist_id)
    return jsonify(wishlist.serialize()), status.HTTP_200_OK


@app.route("/wishlists/<int:wishlist_id>", methods=["GET"])
def get_wishlist(wishlist_id):
    """
    Retrieve a single Wishlist

    This endpoint will return a Wishlist, including its items, based on its id
    """
    app.logger.info("Request to retrieve Wishlist with id: %s", wishlist_id)

    wishlist = WishList.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Wishlist with id '{wishlist_id}' was not found.",
        )

    app.logger.info("Returning Wishlist: %s", wishlist.name)
    return jsonify(wishlist.serialize()), status.HTTP_200_OK


######################################################################
#  I T E M   E N D P O I N T S
######################################################################


@app.route("/wishlists/<int:wishlist_id>/items", methods=["GET"])
def list_wishlist_items(wishlist_id):
    """Returns all of the Items in a Wishlist"""
    app.logger.info("Request for Items in Wishlist with id: %s", wishlist_id)

    wishlist = WishList.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Wishlist with id '{wishlist_id}' was not found.",
        )

    items = sorted(wishlist.items, key=lambda item: item.id)
    results = [item.serialize() for item in items]
    app.logger.info("Returning %d items", len(results))
    return jsonify(results), status.HTTP_200_OK
