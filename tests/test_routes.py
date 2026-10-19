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
TestWishList API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Item, WishList
from tests.factories import WishListFactory, ItemFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/wishlists"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Item).delete()  # clean up dependent items first
        db.session.query(WishList).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
    def test_create_wishlist(self):
        """It should Create a new Wishlist"""
        payload = {
            "name": "Birthday",
            "customer_id": 1001,
        }
        response = self.client.post("/wishlists", json=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.get_json()
        self.assertEqual(data["name"], "Birthday")
        self.assertEqual(data["customer_id"], 1001)
        self.assertIsNotNone(data["id"])
        self.assertEqual(len(WishList.all()), 1)

    def test_create_duplicate_wishlist(self):
        """It should return Conflict when a customer reuses a Wishlist name"""
        payload = {
            "name": "Birthday",
            "customer_id": 1001,
        }
        response = self.client.post("/wishlists", json=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post("/wishlists", json=payload)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertIn("message", data)
        self.assertEqual(len(WishList.all()), 1)

    def test_create_same_wishlist_name_different_customer(self):
        """It should allow different customers to use the same Wishlist name"""
        first = {
            "name": "Birthday",
            "customer_id": 1001,
        }
        second = {
            "name": "Birthday",
            "customer_id": 1002,
        }
        response = self.client.post("/wishlists", json=first)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post("/wishlists", json=second)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(WishList.all()), 2)

    def test_create_wishlist_missing_required_data(self):
        """It should reject a Wishlist with missing required data"""
        invalid_payloads = [
            {"customer_id": 1001},
            {"name": "Birthday"},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/wishlists", json=payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(WishList.all()), 0)

    def test_create_wishlist_requires_json(self):
        """It should reject a Wishlist request that is not JSON"""
        response = self.client.post(
            "/wishlists",
            data="name=Birthday&customer_id=1001",
            content_type="text/plain",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

        
    def test_get_wishlist(self):
        """It should Read a single Wishlist"""
        wishlist = WishListFactory()
        wishlist.create()
        response = self.client.get(f"/wishlists/{wishlist.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content_type, "application/json")
        data = response.get_json()
        self.assertEqual(data["id"], wishlist.id)
        self.assertEqual(data["name"], wishlist.name)
        self.assertEqual(data["customer_id"], wishlist.customer_id)
        self.assertEqual(data["note"], wishlist.note)
        self.assertEqual(data["items"], [])

    def test_get_wishlist_with_items(self):
        """It should Read a Wishlist along with its items"""
        wishlist = WishListFactory()
        wishlist.create()
        item = ItemFactory(wishlist=wishlist, wishlist_id=wishlist.id)
        item.create()
        response = self.client.get(f"/wishlists/{wishlist.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["id"], item.id)
        self.assertEqual(data["items"][0]["product_id"], item.product_id)
        self.assertEqual(data["items"][0]["wishlist_id"], wishlist.id)

    def _create_wishlist(self):
        """Helper: save a Wishlist to the database and return it"""
        wishlist = WishListFactory()
        wishlist.create()
        return wishlist

    def test_add_item_to_wishlist(self):
        """It should add a product to an existing Wishlist"""
        wishlist = self._create_wishlist()
        payload = {"product_id": 2001, "quantity": 2, "note": "Size M"}
        response = self.client.post(f"/wishlists/{wishlist.id}/items", json=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.content_type, "application/json")
        data = response.get_json()
        self.assertIsNotNone(data["id"])
        self.assertEqual(data["wishlist_id"], wishlist.id)
        self.assertEqual(data["product_id"], 2001)
        self.assertEqual(data["quantity"], 2)
        self.assertEqual(data["note"], "Size M")

        # the product is now saved in the wishlist
        saved = WishList.find(wishlist.id)
        self.assertEqual(len(saved.items), 1)
        self.assertEqual(saved.items[0].product_id, 2001)

    def test_add_item_default_quantity(self):
        """It should default quantity to 1 when it is not given"""
        wishlist = self._create_wishlist()
        response = self.client.post(
            f"/wishlists/{wishlist.id}/items", json={"product_id": 2001}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.get_json()
        self.assertEqual(data["quantity"], 1)
        self.assertIsNone(data["note"])

    def test_add_item_ignores_wishlist_id_in_body(self):
        """It should use the Wishlist id from the URL, not the body"""
        wishlist = self._create_wishlist()
        payload = {"product_id": 2001, "quantity": 1, "wishlist_id": 999999}
        response = self.client.post(f"/wishlists/{wishlist.id}/items", json=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.get_json()["wishlist_id"], wishlist.id)

    def test_add_multiple_items_to_wishlist(self):
        """It should add several products to the same Wishlist"""
        wishlist = self._create_wishlist()
        for product_id in (2001, 2002, 2003):
            response = self.client.post(
                f"/wishlists/{wishlist.id}/items", json={"product_id": product_id}
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(WishList.find(wishlist.id).items), 3)

    def test_add_item_wishlist_not_found(self):
        """It should return 404 Not Found when the Wishlist does not exist"""
        response = self.client.post("/wishlists/0/items", json={"product_id": 2001})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.content_type, "application/json")
        data = response.get_json()
        self.assertEqual(data["error"], "Not Found")
        self.assertIn("was not found", data["message"])
        self.assertEqual(len(Item.all()), 0)

    def test_get_wishlist_not_found(self):
        """It should return 404 Not Found when the Wishlist does not exist"""
        response = self.client.get("/wishlists/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.content_type, "application/json")
        data = response.get_json()
        self.assertEqual(data["error"], "Not Found")
        self.assertIn("was not found", data["message"])
        self.assertEqual(len(Item.all()), 0)

    def test_add_item_invalid_data(self):
        """It should return 400 Bad Request for invalid item data"""
        wishlist = self._create_wishlist()
        invalid_payloads = [
            {},                                      # missing product_id
            {"quantity": 2},                         # missing product_id
            {"product_id": "abc"},                   # product_id not an integer
            {"product_id": True},                    # product_id is a boolean
            {"product_id": 2001, "quantity": 0},     # quantity below 1
            {"product_id": 2001, "quantity": "2"},   # quantity not an integer
            [{"product_id": 2001}],                  # body is not an object
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(
                    f"/wishlists/{wishlist.id}/items", json=payload
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(Item.all()), 0)

    def test_list_wishlists_empty(self):
        """It should return an empty list when there are no WishLists"""
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.content_type, "application/json")
        self.assertEqual(resp.get_json(), [])

    def test_list_wishlists(self):
        """It should List all WishLists"""
        birthday = WishListFactory(name="Birthday")
        birthday.create()
        holiday = WishListFactory(name="Holiday")
        holiday.create()

        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.content_type, "application/json")
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

        # each wishlist is returned in full and matches what was saved
        by_id = {wishlist["id"]: wishlist for wishlist in data}
        for expected in (birthday, holiday):
            self.assertIn(expected.id, by_id)
            returned = by_id[expected.id]
            self.assertEqual(returned["name"], expected.name)
            self.assertEqual(returned["customer_id"], expected.customer_id)
            self.assertEqual(returned["note"], expected.note)
            self.assertEqual(returned["items"], [])

    def test_list_wishlists_includes_items(self):
        """It should include each WishList's items in the list"""
        wishlist = WishListFactory(name="Birthday")
        wishlist.create()
        item = ItemFactory(wishlist=wishlist, wishlist_id=wishlist.id)
        item.create()

        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(len(data[0]["items"]), 1)
        self.assertEqual(data[0]["items"][0]["id"], item.id)
        self.assertEqual(data[0]["items"][0]["product_id"], item.product_id)
    def test_add_item_requires_json(self):
        """It should return 415 when the request is not JSON"""
        wishlist = self._create_wishlist()
        response = self.client.post(
            f"/wishlists/{wishlist.id}/items",
            data="product_id=2001",
            content_type="text/plain",
        )
        self.assertEqual(
            response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )
