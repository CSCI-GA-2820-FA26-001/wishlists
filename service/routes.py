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
and Delete WishLists and the Items in them.

The REST API is served by Flask-RESTX under the /api prefix. The Admin UI (/)
and the health check (/health) stay as plain Flask routes.
"""

from flask import jsonify, request, abort
from flask import current_app as app  # Import Flask application
from flask_restx import Api, Resource, fields, reqparse
from service.models import WishList, Item, WishListQuery, ItemQuery
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Serve the single-page admin UI"""
    app.logger.info("Request for the Wishlist admin UI")
    return app.send_static_file("index.html")


######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/health", methods=["GET"])
def health():
    """Return the service health status."""
    return jsonify(status="OK"), status.HTTP_200_OK


######################################################################
# Configure the Flask-RESTX API
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Wishlist REST API Service",
    description="This is the Wishlist service for managing customer wishlists and the products saved in them.",
    default="wishlists",
    default_label="Wishlist operations",
    doc="/apidocs",  # default would be "/"
    prefix="/api",
)


######################################################################
# Swagger models
######################################################################
item_create_model = api.model(
    "ItemCreate",
    {
        "product_id": fields.Integer(required=True, description="The product to save"),
        "quantity": fields.Integer(required=False, description="How many to save; defaults to 1 when adding an item"),
        "note": fields.String(required=False, description="An optional note of up to 256 characters"),
    },
)

item_model = api.inherit(
    "ItemModel",
    item_create_model,
    {
        "id": fields.Integer(readonly=True, description="The unique id assigned internally by the service"),
        "wishlist_id": fields.Integer(readonly=True, description="The id of the Wishlist this item belongs to"),
    },
)

wishlist_create_model = api.model(
    "WishlistCreate",
    {
        "name": fields.String(required=True, description="The name of the Wishlist"),
        "customer_id": fields.Integer(required=True, description="The id of the customer who owns the Wishlist"),
        "note": fields.String(required=False, description="An optional note of up to 256 characters"),
    },
)

wishlist_model = api.inherit(
    "WishlistModel",
    wishlist_create_model,
    {
        "id": fields.Integer(readonly=True, description="The unique id assigned internally by the service"),
        "items": fields.List(fields.Nested(item_model), readonly=True, description="The products saved in the Wishlist"),
    },
)

# Query string arguments, used for the Swagger docs (WishListQuery and ItemQuery validate them)
wishlist_args = reqparse.RequestParser()
wishlist_args.add_argument(
    "customer_id", type=int, location="args", required=False, help="List the Wishlists of this customer"
)

item_args = reqparse.RequestParser()
item_args.add_argument("product_id", type=int, location="args", required=False, help="List the Items for this product")


######################################################################
#  H E L P E R   F U N C T I O N S
######################################################################
def find_wishlist_or_404(wishlist_id: int) -> WishList:
    """Return the Wishlist with the given id, or abort with 404 Not Found"""
    wishlist = WishList.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Wishlist with id '{wishlist_id}' was not found",
        )
    return wishlist


def find_item_or_404(wishlist_id: int, item_id: int) -> Item:
    """Return the Item in the given Wishlist, or abort with 404 Not Found"""
    item = Item.find(item_id)
    if not item or item.wishlist_id != wishlist_id:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Item with id '{item_id}' was not found in Wishlist '{wishlist_id}'",
        )
    return item


######################################################################
#  PATH: /wishlists/{wishlist_id}
######################################################################
@api.route("/wishlists/<int:wishlist_id>")
@api.param("wishlist_id", "The Wishlist identifier")
class WishlistResource(Resource):
    """
    WishlistResource class

    Allows the manipulation of a single Wishlist
    GET /wishlists/{id} - Returns a Wishlist with the id
    PUT /wishlists/{id} - Updates a Wishlist with the id
    DELETE /wishlists/{id} - Deletes a Wishlist with the id
    """

    # ------------------------------------------------------------------
    # RETRIEVE A WISHLIST
    # ------------------------------------------------------------------
    @api.doc("get_wishlist")
    @api.marshal_with(wishlist_model)
    def get(self, wishlist_id):
        """
        Retrieve a single Wishlist

        This endpoint will return a Wishlist, including its items, based on its id
        """
        app.logger.info("Request to retrieve Wishlist with id: %s", wishlist_id)
        wishlist = find_wishlist_or_404(wishlist_id)
        app.logger.info("Returning Wishlist: %s", wishlist.name)
        return wishlist.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # UPDATE AN EXISTING WISHLIST
    # ------------------------------------------------------------------
    @api.doc("update_wishlist")
    @api.expect(wishlist_create_model)
    @api.marshal_with(wishlist_model)
    def put(self, wishlist_id):
        """
        Update a Wishlist

        This endpoint will update the name and note of a Wishlist
        """
        app.logger.info("Request to update Wishlist with id %s", wishlist_id)
        wishlist = find_wishlist_or_404(wishlist_id)
        # Validate on a detached copy (with the current owner) so a rejected
        # request leaves the stored record untouched
        updated = WishList(customer_id=wishlist.customer_id).deserialize(request.get_json())
        existing = WishList.find_by_customer_and_name(updated.customer_id, updated.name)
        if existing and existing.id != wishlist_id:
            abort(
                status.HTTP_409_CONFLICT,
                description="Wishlist already exists for this customer",
            )
        wishlist.name = updated.name
        wishlist.note = updated.note
        wishlist.update()
        app.logger.info("Wishlist with id %s updated", wishlist_id)
        return wishlist.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE A WISHLIST
    # ------------------------------------------------------------------
    @api.doc("delete_wishlist")
    @api.response(204, "Wishlist deleted")
    def delete(self, wishlist_id):
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


######################################################################
#  PATH: /wishlists
######################################################################
@api.route("/wishlists", strict_slashes=False)
class WishlistCollection(Resource):
    """Handles all interactions with collections of Wishlists"""

    # ------------------------------------------------------------------
    # LIST ALL WISHLISTS
    # ------------------------------------------------------------------
    @api.doc("list_wishlists")
    @api.expect(wishlist_args)
    @api.marshal_list_with(wishlist_model)
    def get(self):
        """
        List Wishlists, optionally filtered by customer_id

        This endpoint returns matching Wishlists, with their items, as a JSON array.
        Without a filter, all Wishlists are returned. An empty array is returned
        when no Wishlists match.
        """
        app.logger.info("Request to list Wishlists")
        query = WishListQuery().deserialize(request.args.to_dict(flat=False))
        results = [wishlist.serialize() for wishlist in query.find()]
        app.logger.info("Returning %d Wishlists", len(results))
        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # ADD A NEW WISHLIST
    # ------------------------------------------------------------------
    @api.doc("create_wishlist")
    @api.expect(wishlist_create_model)
    @api.marshal_with(wishlist_model, code=201)
    def post(self):
        """
        Create a Wishlist

        This endpoint will create a Wishlist based on the data in the body that is posted
        """
        app.logger.info("Request to create a Wishlist")
        wishlist = WishList()
        wishlist.deserialize(request.get_json())
        if WishList.find_by_customer_and_name(wishlist.customer_id, wishlist.name):
            abort(
                status.HTTP_409_CONFLICT,
                description="Wishlist already exists for this customer",
            )
        wishlist.create()
        app.logger.info("Wishlist with id %s created", wishlist.id)
        location_url = api.url_for(WishlistResource, wishlist_id=wishlist.id, _external=True)
        return wishlist.serialize(), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
#  PATH: /wishlists/{wishlist_id}/clear
######################################################################
@api.route("/wishlists/<int:wishlist_id>/clear")
@api.param("wishlist_id", "The Wishlist identifier")
class ClearResource(Resource):
    """Clear action on a Wishlist"""

    @api.doc("clear_wishlist")
    @api.marshal_with(wishlist_model)
    def put(self, wishlist_id):
        """Clear all items while keeping the Wishlist"""
        app.logger.info("Request to clear Wishlist with id %s", wishlist_id)
        wishlist = find_wishlist_or_404(wishlist_id)
        wishlist.clear_items()
        app.logger.info("Wishlist with id %s cleared", wishlist_id)
        return wishlist.serialize(), status.HTTP_200_OK


######################################################################
#  PATH: /wishlists/{wishlist_id}/items/{item_id}
######################################################################
@api.route("/wishlists/<int:wishlist_id>/items/<int:item_id>")
@api.param("wishlist_id", "The Wishlist identifier")
@api.param("item_id", "The Item identifier")
class ItemResource(Resource):
    """
    ItemResource class

    Allows the manipulation of a single Item in a Wishlist
    GET /wishlists/{id}/items/{item_id} - Returns the Item
    PUT /wishlists/{id}/items/{item_id} - Updates the Item
    DELETE /wishlists/{id}/items/{item_id} - Deletes the Item
    """

    # ------------------------------------------------------------------
    # RETRIEVE AN ITEM FROM A WISHLIST
    # ------------------------------------------------------------------
    @api.doc("get_wishlist_item")
    @api.marshal_with(item_model)
    def get(self, wishlist_id, item_id):
        """
        Retrieve a product in a Wishlist

        This endpoint returns the item identified by item_id in the Wishlist identified by wishlist_id
        """
        app.logger.info("Request to retrieve Item with id: %s from Wishlist with id: %s", item_id, wishlist_id)
        find_wishlist_or_404(wishlist_id)
        item = find_item_or_404(wishlist_id, item_id)
        app.logger.info("Returning Item with id %s from Wishlist %s", item_id, wishlist_id)
        return item.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # UPDATE AN ITEM IN A WISHLIST
    # ------------------------------------------------------------------
    @api.doc("update_wishlist_item")
    @api.expect(item_create_model)
    @api.marshal_with(item_model)
    def put(self, wishlist_id, item_id):
        """Update an existing wishlist item and return its JSON"""
        app.logger.info("Request to update item %s in wishlist %s", item_id, wishlist_id)

        # Require the parent to exist and prevent updates to an item from another wishlist.
        find_wishlist_or_404(wishlist_id)
        item = find_item_or_404(wishlist_id, item_id)

        # Validate on an unsaved object so rejected input does not partially alter the stored item.
        candidate = Item().deserialize(request.get_json())

        # Copy only editable fields, preserving the item's ID and its wishlist association.
        item.product_id = candidate.product_id
        item.quantity = candidate.quantity
        item.note = candidate.note
        item.update()

        app.logger.info("Item %s in wishlist %s updated; returning 200 OK", item_id, wishlist_id)
        return item.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE AN ITEM FROM A WISHLIST
    # ------------------------------------------------------------------
    @api.doc("delete_wishlist_item")
    @api.response(204, "Item deleted")
    def delete(self, wishlist_id, item_id):
        """Delete an item from a wishlist and return an empty 204 response"""
        app.logger.info("Request to delete item %s from wishlist %s", item_id, wishlist_id)

        # Match both IDs so an item belonging to another wishlist cannot be deleted.
        item = Item.query.filter_by(id=item_id, wishlist_id=wishlist_id).first()
        if item is not None:
            item.delete()
            app.logger.info("Item %s deleted from wishlist %s; returning 204 No Content", item_id, wishlist_id)
        else:
            # An absent item under this URL requires no deletion, including an absent parent.
            app.logger.info("Item %s not found in wishlist %s; returning 204 No Content", item_id, wishlist_id)
        return "", status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /wishlists/{wishlist_id}/items
######################################################################
@api.route("/wishlists/<int:wishlist_id>/items", strict_slashes=False)
@api.param("wishlist_id", "The Wishlist identifier")
class ItemCollection(Resource):
    """Handles all interactions with the collection of Items in a Wishlist"""

    # ------------------------------------------------------------------
    # LIST ALL ITEMS IN A WISHLIST
    # ------------------------------------------------------------------
    @api.doc("list_wishlist_items")
    @api.expect(item_args)
    @api.marshal_list_with(item_model)
    def get(self, wishlist_id):
        """Returns the Items in a Wishlist, optionally filtered by product_id"""
        app.logger.info("Request for Items in Wishlist with id: %s", wishlist_id)
        wishlist = find_wishlist_or_404(wishlist_id)
        query = ItemQuery().deserialize(request.args.to_dict(flat=False))
        results = [item.serialize() for item in query.find(wishlist)]
        app.logger.info("Returning %d items", len(results))
        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # ADD AN ITEM TO A WISHLIST
    # ------------------------------------------------------------------
    @api.doc("create_wishlist_item")
    @api.expect(item_create_model)
    @api.marshal_with(item_model, code=201)
    def post(self, wishlist_id):
        """
        Add a product to a Wishlist

        This endpoint creates a new item in the Wishlist identified by wishlist_id
        """
        app.logger.info("Request to add an item to Wishlist with id: %s", wishlist_id)
        find_wishlist_or_404(wishlist_id)

        item = Item()
        item.deserialize(request.get_json(), default_quantity=1)
        item.wishlist_id = wishlist_id  # the URL decides the Wishlist, not the body
        item.create()

        app.logger.info("Item with id %s added to Wishlist %s", item.id, wishlist_id)
        return item.serialize(), status.HTTP_201_CREATED
