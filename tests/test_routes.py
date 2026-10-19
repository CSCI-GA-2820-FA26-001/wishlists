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

# Payloads with every required field present but one field of the wrong type
INVALID_TYPE_PAYLOADS = [
    {"name": 123, "customer_id": 1001},
    {"name": [], "customer_id": 1001},
    {"name": "", "customer_id": 1001},
    {"name": "Holiday", "customer_id": "1001"},
    {"name": "Holiday", "customer_id": 1.5},
    {"name": "Holiday", "customer_id": True},
    {"name": "Holiday", "customer_id": 1001, "note": 123},
]


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

    def test_create_wishlist_bad_data_types(self):
        """It should reject a Wishlist with fields of the wrong type"""
        for payload in INVALID_TYPE_PAYLOADS:
            with self.subTest(payload=payload):
                response = self.client.post("/wishlists", json=payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                data = response.get_json()
                self.assertIsNotNone(data)
                self.assertIn("message", data)
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

    def test_update_wishlist(self):
        """It should Update an existing Wishlist"""
        wishlist = WishListFactory(name="Birthday", customer_id=1001, note="old")
        wishlist.create()
        wishlist_id = wishlist.id

        payload = {"name": "Holiday", "customer_id": 1001, "note": "new"}
        response = self.client.put(f"/wishlists/{wishlist_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["id"], wishlist_id)
        self.assertEqual(data["name"], "Holiday")
        self.assertEqual(data["customer_id"], 1001)
        self.assertEqual(data["note"], "new")
        self.assertEqual(
            WishList.query.filter_by(id=wishlist_id, name="Holiday").count(), 1
        )

    def test_update_wishlist_not_found(self):
        """It should return Not Found when updating a missing Wishlist"""
        payload = {"name": "Holiday", "customer_id": 1001}
        response = self.client.put("/wishlists/0", json=payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertIn("message", data)

    def test_update_wishlist_missing_required_data(self):
        """It should reject a Wishlist update with missing required data"""
        wishlist = WishListFactory(name="Birthday", customer_id=1001)
        wishlist.create()
        wishlist_id = wishlist.id

        invalid_payloads = [
            {"customer_id": 1001},
            {"name": "Holiday"},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.put(f"/wishlists/{wishlist_id}", json=payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                data = response.get_json()
                self.assertIsNotNone(data)
                self.assertIn("message", data)
        self.assertEqual(
            WishList.query.filter_by(id=wishlist_id, name="Birthday").count(), 1
        )

    def test_update_wishlist_bad_data_types(self):
        """It should reject a Wishlist update with fields of the wrong type"""
        wishlist = WishListFactory(name="Birthday", customer_id=1001, note="old")
        wishlist.create()
        wishlist_id = wishlist.id

        for payload in INVALID_TYPE_PAYLOADS:
            with self.subTest(payload=payload):
                response = self.client.put(f"/wishlists/{wishlist_id}", json=payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                data = response.get_json()
                self.assertIsNotNone(data)
                self.assertIn("message", data)
        self.assertEqual(
            WishList.query.filter_by(
                id=wishlist_id, name="Birthday", customer_id=1001, note="old"
            ).count(),
            1,
        )

    def test_update_wishlist_customer_id_change(self):
        """It should not allow a Wishlist update to change the customer_id"""
        wishlist = WishListFactory(name="Birthday", customer_id=1001, note="old")
        wishlist.create()
        wishlist_id = wishlist.id

        payload = {"name": "Holiday", "customer_id": 1002, "note": "new"}
        response = self.client.put(f"/wishlists/{wishlist_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertIn("message", data)
        self.assertEqual(
            WishList.query.filter_by(
                id=wishlist_id, name="Birthday", customer_id=1001, note="old"
            ).count(),
            1,
        )

    def test_update_wishlist_requires_json(self):
        """It should reject a Wishlist update that is not JSON"""
        wishlist = WishListFactory(name="Birthday", customer_id=1001)
        wishlist.create()
        response = self.client.put(
            f"/wishlists/{wishlist.id}",
            data="name=Holiday&customer_id=1001",
            content_type="text/plain",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    def test_update_wishlist_to_duplicate_name(self):
        """It should return Conflict when renaming to a name the customer already uses"""
        WishListFactory(name="Birthday", customer_id=1001).create()
        wishlist = WishListFactory(name="Holiday", customer_id=1001)
        wishlist.create()
        wishlist_id = wishlist.id

        payload = {"name": "Birthday", "customer_id": 1001}
        response = self.client.put(f"/wishlists/{wishlist_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertIn("message", data)
        self.assertEqual(
            WishList.query.filter_by(id=wishlist_id, name="Holiday").count(), 1
        )

    def test_update_wishlist_same_name(self):
        """It should allow a Wishlist to be saved with its current name"""
        wishlist = WishListFactory(name="Birthday", customer_id=1001, note="old")
        wishlist.create()
        wishlist_id = wishlist.id

        payload = {"name": "Birthday", "customer_id": 1001, "note": "new"}
        response = self.client.put(f"/wishlists/{wishlist_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], "Birthday")
        self.assertEqual(data["note"], "new")

    def test_update_wishlist_does_not_duplicate_items(self):
        """It should not duplicate existing Items when the update includes items"""
        wishlist = WishListFactory(name="Birthday", customer_id=1001)
        ItemFactory(wishlist=wishlist)
        wishlist.create()
        wishlist_id = wishlist.id

        payload = wishlist.serialize()
        payload["name"] = "Holiday"
        response = self.client.put(f"/wishlists/{wishlist_id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], "Holiday")
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(len(Item.all()), 1)
