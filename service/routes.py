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

    # Sort by id so the order is stable (the database doesn't guarantee one)
    items = sorted(wishlist.items, key=lambda item: item.id)
    results = [item.serialize() for item in items]
    app.logger.info("Returning %d items", len(results))
    return jsonify(results), status.HTTP_200_OK
