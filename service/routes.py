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
# Reuse the existing Item model for the story #3 deletion endpoint. BY_HYC
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


# Delete one Item record within its wishlist, preserving the parent wishlist. BY_HYC
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["DELETE"])
def delete_wishlist_item(wishlist_id, item_id):
    """Delete an item from a wishlist and return an empty 204 response"""
    # Record the requested parent and item IDs for debugging. BY_HYC
    app.logger.info("Request to delete item %s from wishlist %s", item_id, wishlist_id)

    # Match both IDs so an item belonging to another wishlist cannot be deleted. BY_HYC
    item = Item.query.filter_by(id=item_id, wishlist_id=wishlist_id).first()
    if item is not None:
        item.delete()
        # Log success only after the existing model method commits the deletion. BY_HYC
        app.logger.info("Item %s deleted from wishlist %s; returning 204 No Content", item_id, wishlist_id)
    else:
        # An absent item under this URL requires no deletion, including an absent parent. BY_HYC
        app.logger.info("Item %s not found in wishlist %s; returning 204 No Content", item_id, wishlist_id)

    # Story #3 returns no response body whether or not the item was present. BY_HYC
    return "", status.HTTP_204_NO_CONTENT
