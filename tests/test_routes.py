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
# Use the factory to prepare test data independently of the POST endpoint. BY_HYC
from tests.factories import WishListFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


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

    def test_delete_wishlist(self):
        """It should delete an existing wishlist"""
        # Save a wishlist through the model so the test does not require a POST route. BY_HYC
        wishlist = WishListFactory()
        wishlist.create()
        wishlist_id = wishlist.id

        # Send a DELETE request for the wishlist created by this test. BY_HYC
        response = self.client.delete(f"/wishlists/{wishlist_id}")

        # Verify the endpoint returns 204 No Content with an empty response body. BY_HYC
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

        # Verify the wishlist was removed from the database, not only acknowledged. BY_HYC
        self.assertIsNone(WishList.find(wishlist_id))

    def test_delete_wishlist_not_found(self):
        """It should return empty 204 when the wishlist does not exist"""
        # The setup clears all wishlists, so this ID is guaranteed to be absent. BY_HYC
        self.assertIsNone(WishList.find(1))
        response = self.client.delete("/wishlists/1")

        # Story #11 requires the same empty 204 response for a missing wishlist. BY_HYC
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

    def test_delete_wishlist_with_items(self):
        """It should delete associated items and preserve another wishlist"""
        # Give each wishlist a distinct name to avoid the existing uniqueness constraint. BY_HYC
        wishlist = WishListFactory(name="Delete target")
        wishlist.create()
        other_wishlist = WishListFactory(name="Keep target")
        other_wishlist.create()

        # Persist one item per wishlist to check both cascade deletion and isolation. BY_HYC
        # Assign attributes explicitly so Pylint can check construction without ORM-generated keywords. BY_HYC
        item = Item()
        item.wishlist_id = wishlist.id
        item.product_id = 1001
        item.quantity = 1
        item.create()
        other_item = Item()
        other_item.wishlist_id = other_wishlist.id
        other_item.product_id = 1002
        other_item.quantity = 1
        other_item.create()
        wishlist_id, item_id = wishlist.id, item.id
        other_wishlist_id, other_item_id = other_wishlist.id, other_item.id

        # Delete only the selected wishlist through the HTTP endpoint. BY_HYC
        response = self.client.delete(f"/wishlists/{wishlist_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

        # Clear cached objects so these checks read the committed database state. BY_HYC
        db.session.remove()
        self.assertIsNone(WishList.find(wishlist_id))
        self.assertIsNone(Item.find(item_id))

        # Deleting one wishlist must leave the other wishlist and its item intact. BY_HYC
        self.assertIsNotNone(WishList.find(other_wishlist_id))
        self.assertIsNotNone(Item.find(other_item_id))

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
