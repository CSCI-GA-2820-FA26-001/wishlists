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

######################################################################
# LIST ALL WISHLISTS
######################################################################
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
