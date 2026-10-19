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

    def test_delete_wishlist_item(self):
        """It should delete one item while preserving its wishlist and another item"""
        # Prepare persisted records directly so this test does not depend on POST endpoints. BY_HYC
        wishlist = WishList()
        wishlist.name = "Delete item test"
        wishlist.customer_id = 1001
        wishlist.create()
        item = Item()
        item.wishlist_id = wishlist.id
        item.product_id = 1001
        item.quantity = 1
        item.create()

        # Keep a second item in the same wishlist to detect deletion beyond the requested item. BY_HYC
        other_item = Item()
        other_item.wishlist_id = wishlist.id
        other_item.product_id = 1002
        other_item.quantity = 2
        other_item.create()
        wishlist_id, item_id = wishlist.id, item.id
        other_item_id = other_item.id
        other_original = other_item.serialize()

        # Address the Item record ID in the URL, rather than its product_id. BY_HYC
        response = self.client.delete(f"/wishlists/{wishlist_id}/items/{item_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

        # Read fresh database state to prove only the requested item was deleted. BY_HYC
        db.session.remove()
        self.assertIsNone(Item.find(item_id))
        saved_wishlist = WishList.find(wishlist_id)
        self.assertIsNotNone(saved_wishlist)
        self.assertEqual(saved_wishlist.name, "Delete item test")
        self.assertEqual(saved_wishlist.customer_id, 1001)
        saved_item = Item.find(other_item_id)
        self.assertIsNotNone(saved_item)
        self.assertEqual(saved_item.serialize(), other_original)

    def _create_item_for_deletion(self, name="Item deletion test"):
        """Prepare persisted records for the story #3 tests. BY_HYC"""
        # Set attributes explicitly and avoid depending on POST endpoints. BY_HYC
        wishlist = WishList()
        wishlist.name = name
        wishlist.customer_id = 1001
        wishlist.create()
        item = Item()
        item.wishlist_id = wishlist.id
        item.product_id = 1001
        item.quantity = 1
        item.note = "Preserve unless targeted"
        item.create()
        return wishlist.id, item.id

    def test_delete_wishlist_item_not_found(self):
        """It should return empty 204 for a missing item or wishlist"""
        # Setup clears the tables; only the records created here exist. BY_HYC
        wishlist_id, item_id = self._create_item_for_deletion()
        original = Item.find(item_id).serialize()
        paths = [
            f"/wishlists/{wishlist_id}/items/{item_id + 1}",
            f"/wishlists/{wishlist_id + 1}/items/{item_id}",
        ]
        for path in paths:
            with self.subTest(path=path):
                # Treat an absent parent as no item at this URL, returning an empty 204. BY_HYC
                response = self.client.delete(path)
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
                self.assertEqual(response.data, b"")

                # A request for missing resources must preserve the existing records. BY_HYC
                db.session.remove()
                saved_item = Item.find(item_id)
                self.assertIsNotNone(saved_item)
                self.assertEqual(saved_item.serialize(), original)
                self.assertIsNotNone(WishList.find(wishlist_id))

    def test_delete_wishlist_item_twice(self):
        """It should return empty 204 on repeated deletion and retain the wishlist"""
        # Repeat the same request to verify the missing-item behavior after a real deletion. BY_HYC
        wishlist_id, item_id = self._create_item_for_deletion()
        for attempt in range(2):
            with self.subTest(attempt=attempt):
                response = self.client.delete(f"/wishlists/{wishlist_id}/items/{item_id}")
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
                self.assertEqual(response.data, b"")

                # The item stays absent while its parent survives both requests. BY_HYC
                db.session.remove()
                self.assertIsNone(Item.find(item_id))
                self.assertIsNotNone(WishList.find(wishlist_id))

    def test_delete_wishlist_item_wrong_wishlist(self):
        """It should preserve an item when the URL specifies a different wishlist"""
        # Both wishlists contain the same product but have distinct Item record IDs. BY_HYC
        wishlist_id, item_id = self._create_item_for_deletion("First wishlist")
        other_wishlist_id, other_item_id = self._create_item_for_deletion("Second wishlist")
        original = Item.find(item_id).serialize()
        other_original = Item.find(other_item_id).serialize()

        # Combine one parent's ID with the other parent's item ID; neither item should be deleted. BY_HYC
        response = self.client.delete(f"/wishlists/{wishlist_id}/items/{other_item_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

        # Check persisted records to verify isolation between wishlists. BY_HYC
        db.session.remove()
        saved_item = Item.find(item_id)
        saved_other_item = Item.find(other_item_id)
        self.assertIsNotNone(saved_item)
        self.assertIsNotNone(saved_other_item)
        self.assertEqual(saved_item.serialize(), original)
        self.assertEqual(saved_other_item.serialize(), other_original)
        self.assertIsNotNone(WishList.find(wishlist_id))
        self.assertIsNotNone(WishList.find(other_wishlist_id))
