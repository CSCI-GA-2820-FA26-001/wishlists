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
    """Root URL response"""
    return (
        "Reminder: return some useful information in json format about the service here",
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


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
