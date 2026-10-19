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
from service.models import WishList, DataValidationError
# Use the existing Item model for the story #15 update endpoint. BY_HYC
from service.models import Item
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        "Reminder: return some useful information in json format about the service here",
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

@app.route("/wishlists", methods=["POST"])
def create_wishlist():
    """Creates a Wishlist"""
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
    return jsonify(wishlist.serialize()), status.HTTP_201_CREATED


# Update one item identified within its wishlist, matching the story #14 URL structure. BY_HYC
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["PUT"])
def update_wishlist_item(wishlist_id, item_id):
    """Update an existing wishlist item and return its JSON"""
    # Log both IDs to identify the requested resource during debugging. BY_HYC
    app.logger.info("Request to update item %s in wishlist %s", item_id, wishlist_id)

    # Require the parent to exist and prevent updates to an item from another wishlist. BY_HYC
    if WishList.find(wishlist_id) is None:
        abort(status.HTTP_404_NOT_FOUND, description="Wishlist not found")
    item = Item.find(item_id)
    if item is None or item.wishlist_id != wishlist_id:
        abort(status.HTTP_404_NOT_FOUND, description="Item not found in this wishlist")

    # Require a JSON object before passing its fields to the existing model validation. BY_HYC
    data = request.get_json()
    if not isinstance(data, dict):
        raise DataValidationError("Item data must be a JSON object")

    # Reject implicit database conversions; a product ID must be a JSON integer, not a boolean. BY_HYC
    product_id = data.get("product_id")
    if isinstance(product_id, bool) or not isinstance(product_id, int):
        raise DataValidationError("product_id is required and must be an integer")

    # Match the existing nullable String(256) column before changing the persisted item. BY_HYC
    note = data.get("note")
    if note is not None and (not isinstance(note, str) or len(note) > 256):
        raise DataValidationError("note must be null or a string of at most 256 characters")

    # Validate on an unsaved object so rejected input does not partially alter the stored item. BY_HYC
    candidate = Item()
    candidate.deserialize({**data, "wishlist_id": wishlist_id})

    # Copy only editable fields, preserving the item's ID and its wishlist association. BY_HYC
    item.product_id = candidate.product_id
    item.quantity = candidate.quantity
    item.note = candidate.note
    item.update()

    # Return the updated item itself, rather than the entire wishlist, as required by #15. BY_HYC
    return jsonify(item.serialize()), status.HTTP_200_OK
