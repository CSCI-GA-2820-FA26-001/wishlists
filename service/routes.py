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

# Delete a wishlist by its integer ID for story #11. BY_HYC
@app.route("/wishlists/<int:wishlist_id>", methods=["DELETE"])
def delete_wishlist(wishlist_id):
    """Delete a wishlist and return 204 No Content"""
    # Log the requested ID so deletion requests can be traced during debugging. BY_HYC
    app.logger.info("Request to delete wishlist with id: %s", wishlist_id)

    # Reuse the model's delete method, including its existing cascade behavior. BY_HYC
    wishlist = WishList.find(wishlist_id)
    if wishlist is not None:
        wishlist.delete()
        # Log success only after the database deletion has completed. BY_HYC
        app.logger.info("Wishlist %s deleted; returning 204 No Content", wishlist_id)
    else:
        # Record the missing-resource outcome, which also returns 204 under story #11. BY_HYC
        app.logger.info("Wishlist %s not found; returning 204 No Content", wishlist_id)

    # Return an empty 204 response even when the wishlist does not exist, as required by #11. BY_HYC
    return "", status.HTTP_204_NO_CONTENT


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
