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

    def test_update_wishlist_item(self):
        """It should update one item and return its JSON while preserving the wishlist"""
        # Create records through the models so this test does not depend on POST endpoints. BY_HYC
        wishlist = WishList()
        wishlist.name = "Update item test"
        wishlist.customer_id = 1001
        wishlist.create()
        item = Item()
        item.wishlist_id = wishlist.id
        item.product_id = 1001
        item.quantity = 1
        item.note = "Original note"
        item.create()
        wishlist_id, item_id = wishlist.id, item.id

        # Supply editable fields; the URL identifies the existing item and its parent. BY_HYC
        payload = {"product_id": 1002, "quantity": 2, "note": "Updated note"}
        response = self.client.put(
            f"/wishlists/{wishlist_id}/items/{item_id}", json=payload
        )

        # Return the updated item itself, including its unchanged identity and parent. BY_HYC
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.is_json)
        expected = {"id": item_id, "wishlist_id": wishlist_id, **payload}
        self.assertEqual(response.get_json(), expected)

        # Read fresh database state to verify persistence and preservation of the wishlist. BY_HYC
        db.session.remove()
        saved_item = Item.find(item_id)
        self.assertIsNotNone(saved_item)
        self.assertEqual(saved_item.serialize(), expected)
        saved_wishlist = WishList.find(wishlist_id)
        self.assertIsNotNone(saved_wishlist)
        self.assertEqual(saved_wishlist.name, "Update item test")
        self.assertEqual(saved_wishlist.customer_id, 1001)

    def _create_item_for_update(self, name="Item update validation"):
        """Prepare persisted records for the story #15 tests. BY_HYC"""
        # Use explicit attributes to avoid ORM constructor inference issues in Pylint. BY_HYC
        wishlist = WishList()
        wishlist.name = name
        wishlist.customer_id = 1001
        wishlist.create()
        item = Item()
        item.wishlist_id = wishlist.id
        item.product_id = 1001
        item.quantity = 1
        item.note = "Keep original note"
        item.create()
        return wishlist.id, item.id

    def test_update_wishlist_item_not_found(self):
        """It should return JSON 404 for a missing wishlist or item"""
        # Only one parent and item exist, so the next IDs are absent. BY_HYC
        wishlist_id, item_id = self._create_item_for_update()
        original = Item.find(item_id).serialize()
        paths = [
            f"/wishlists/{wishlist_id + 1}/items/{item_id}",
            f"/wishlists/{wishlist_id}/items/{item_id + 1}",
        ]
        for path in paths:
            with self.subTest(path=path):
                # A missing resource must produce the existing structured JSON error. BY_HYC
                response = self.client.put(path, json={"product_id": 1002, "quantity": 2})
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
                self.assertTrue(response.is_json)
                self.assertEqual(response.get_json()["status"], status.HTTP_404_NOT_FOUND)
                self.assertIn("message", response.get_json())

        # Failed lookups must leave the existing records intact. BY_HYC
        db.session.remove()
        self.assertEqual(Item.find(item_id).serialize(), original)
        self.assertIsNotNone(WishList.find(wishlist_id))

    def test_update_item_from_another_wishlist(self):
        """It should reject an item that belongs to another wishlist"""
        # Prepare two separate wishlists and preserve both items for comparison. BY_HYC
        wishlist_id, item_id = self._create_item_for_update("First wishlist")
        other_wishlist_id, other_item_id = self._create_item_for_update("Second wishlist")
        original = Item.find(item_id).serialize()
        other_original = Item.find(other_item_id).serialize()

        # An existing item is still not found under the wrong parent URL. BY_HYC
        response = self.client.put(
            f"/wishlists/{wishlist_id}/items/{other_item_id}",
            json={"product_id": 1002, "quantity": 2},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.is_json)
        self.assertIn("message", response.get_json())

        # Check fresh database state to ensure neither item was modified or moved. BY_HYC
        db.session.remove()
        self.assertEqual(Item.find(item_id).serialize(), original)
        self.assertEqual(Item.find(other_item_id).serialize(), other_original)
        self.assertIsNotNone(WishList.find(wishlist_id))
        self.assertIsNotNone(WishList.find(other_wishlist_id))

    def test_update_wishlist_item_invalid_data(self):
        """It should return JSON 400 for invalid fields without changing stored data"""
        # Exercise required fields, integer types, positive quantity, and the note schema. BY_HYC
        invalid_payloads = [
            {},
            {"product_id": 1002},
            {"quantity": 2},
            {"product_id": None, "quantity": 2},
            {"product_id": "1002", "quantity": 2},
            {"product_id": True, "quantity": 2},
            {"product_id": 1002.5, "quantity": 2},
            {"product_id": 1002, "quantity": 0},
            {"product_id": 1002, "quantity": -1},
            {"product_id": 1002, "quantity": True},
            {"product_id": 1002, "quantity": "2"},
            {"product_id": 1002, "quantity": 1.5},
            {"product_id": 1002, "quantity": None},
            {"product_id": 1002, "quantity": 2, "note": 123},
            {"product_id": 1002, "quantity": 2, "note": "x" * 257},
            [],
            "invalid object",
        ]
        for case_number, payload in enumerate(invalid_payloads):
            with self.subTest(payload=payload):
                # Give each case independent records so one failed update cannot contaminate later cases. BY_HYC
                db.session.remove()
                wishlist_id, item_id = self._create_item_for_update(f"Invalid input case {case_number}")
                original = Item.find(item_id).serialize()
                response = self.client.put(
                    f"/wishlists/{wishlist_id}/items/{item_id}", json=payload
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertTrue(response.is_json)
                self.assertEqual(response.get_json()["status"], status.HTTP_400_BAD_REQUEST)
                self.assertIn("message", response.get_json())

                # Invalid input must not leave partial changes in memory or in the database. BY_HYC
                self.assertEqual(Item.find(item_id).serialize(), original)
                db.session.remove()
                self.assertEqual(Item.find(item_id).serialize(), original)
                self.assertIsNotNone(WishList.find(wishlist_id))
