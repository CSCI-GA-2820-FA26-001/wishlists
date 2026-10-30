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
        """It should return service information and a usable wishlist list URL"""
        # Keep the existing status check and verify the JSON response required by story #8.
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertIsInstance(data, dict)

        # Define the service metadata contract using the initial service version.
        self.assertEqual(data.get("name"), "Wishlist Service")
        self.assertEqual(data.get("version"), "1.0.0")
        self.assertEqual(data.get("wishlists_url"), BASE_URL)

        # Follow the advertised link to confirm it reaches the existing list endpoint.
        listing = self.client.get(data["wishlists_url"])
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertTrue(listing.is_json)
        self.assertIsInstance(listing.get_json(), list)

    def test_health(self):
        """It should return the service health status as JSON"""
        response = self.client.get("/health")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.get_json(), {"status": "OK"})

    ######################################################################
    #  D E L E T E   A   W I S H L I S T
    ######################################################################

    def test_delete_wishlist(self):
        """It should Delete an existing Wishlist"""
        wishlist = WishListFactory()
        wishlist.create()
        wishlist_id = wishlist.id

        response = self.client.delete(f"/wishlists/{wishlist_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

        # the wishlist is actually gone from the database
        self.assertIsNone(WishList.find(wishlist_id))

    def test_delete_wishlist_not_found(self):
        """It should return 204 No Content when the Wishlist does not exist"""
        response = self.client.delete("/wishlists/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

    def test_delete_wishlist_with_items(self):
        """It should Delete a Wishlist's items and leave other Wishlists alone"""
        wishlist = WishListFactory(name="Delete target")
        wishlist.create()
        other_wishlist = WishListFactory(name="Keep target")
        other_wishlist.create()

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

        response = self.client.delete(f"/wishlists/{wishlist_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

        # read fresh from the database instead of the session cache
        db.session.remove()
        self.assertIsNone(WishList.find(wishlist_id))
        self.assertIsNone(Item.find(item_id))
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

        # Check that the Location header points to the new Wishlist
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_wishlist = response.get_json()
        self.assertEqual(new_wishlist["id"], data["id"])
        self.assertEqual(new_wishlist["name"], data["name"])

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

    def test_delete_wishlist_item(self):
        """It should delete one item while preserving its wishlist and another item"""
        # Prepare persisted records directly so this test does not depend on POST endpoints.
        wishlist = WishListFactory(name="Delete item test", customer_id=1001)
        wishlist.create()
        item = ItemFactory(
            wishlist=wishlist, wishlist_id=wishlist.id, product_id=1001, quantity=1
        )
        item.create()

        # Keep a second item in the same wishlist to detect deletion beyond the requested item.
        other_item = ItemFactory(
            wishlist=wishlist, wishlist_id=wishlist.id, product_id=1002, quantity=2
        )
        other_item.create()
        wishlist_id, item_id = wishlist.id, item.id
        other_item_id = other_item.id
        other_original = other_item.serialize()

        # Address the Item record ID in the URL, rather than its product_id.
        response = self.client.delete(f"/wishlists/{wishlist_id}/items/{item_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

        # Read fresh database state to prove only the requested item was deleted.
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
        """Prepare persisted records for the story #3 tests."""
        # Bind factory items to the persisted wishlist without using POST endpoints.
        wishlist = WishListFactory(name=name, customer_id=1001)
        wishlist.create()
        item = ItemFactory(
            wishlist=wishlist,
            wishlist_id=wishlist.id,
            product_id=1001,
            quantity=1,
            note="Preserve unless targeted",
        )
        item.create()
        return wishlist.id, item.id

    def test_delete_wishlist_item_not_found(self):
        """It should return empty 204 for a missing item or wishlist"""
        # Setup clears the tables; only the records created here exist.
        wishlist_id, item_id = self._create_item_for_deletion()
        original = Item.find(item_id).serialize()
        paths = [
            f"/wishlists/{wishlist_id}/items/{item_id + 1}",
            f"/wishlists/{wishlist_id + 1}/items/{item_id}",
        ]
        for path in paths:
            with self.subTest(path=path):
                # Treat an absent parent as no item at this URL, returning an empty 204.
                response = self.client.delete(path)
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
                self.assertEqual(response.data, b"")

                # A request for missing resources must preserve the existing records.
                db.session.remove()
                saved_item = Item.find(item_id)
                self.assertIsNotNone(saved_item)
                self.assertEqual(saved_item.serialize(), original)
                self.assertIsNotNone(WishList.find(wishlist_id))

    def test_delete_wishlist_item_twice(self):
        """It should return empty 204 on repeated deletion and retain the wishlist"""
        # Repeat the same request to verify the missing-item behavior after a real deletion.
        wishlist_id, item_id = self._create_item_for_deletion()
        for attempt in range(2):
            with self.subTest(attempt=attempt):
                response = self.client.delete(f"/wishlists/{wishlist_id}/items/{item_id}")
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
                self.assertEqual(response.data, b"")

                # The item stays absent while its parent survives both requests.
                db.session.remove()
                self.assertIsNone(Item.find(item_id))
                self.assertIsNotNone(WishList.find(wishlist_id))

    def test_delete_wishlist_item_wrong_wishlist(self):
        """It should preserve an item when the URL specifies a different wishlist"""
        # Both wishlists contain the same product but have distinct Item record IDs.
        wishlist_id, item_id = self._create_item_for_deletion("First wishlist")
        other_wishlist_id, other_item_id = self._create_item_for_deletion("Second wishlist")
        original = Item.find(item_id).serialize()
        other_original = Item.find(other_item_id).serialize()

        # Combine one parent's ID with the other parent's item ID; neither item should be deleted.
        response = self.client.delete(f"/wishlists/{wishlist_id}/items/{other_item_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

        # Check persisted records to verify isolation between wishlists.
        db.session.remove()
        saved_item = Item.find(item_id)
        saved_other_item = Item.find(other_item_id)
        self.assertIsNotNone(saved_item)
        self.assertIsNotNone(saved_other_item)
        self.assertEqual(saved_item.serialize(), original)
        self.assertEqual(saved_other_item.serialize(), other_original)
        self.assertIsNotNone(WishList.find(wishlist_id))
        self.assertIsNotNone(WishList.find(other_wishlist_id))

    def test_update_wishlist_item(self):
        """It should update one item and return its JSON while preserving the wishlist"""
        # Create records through the models so this test does not depend on POST endpoints.
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

        # Supply editable fields; the URL identifies the existing item and its parent.
        payload = {"product_id": 1002, "quantity": 2, "note": "Updated note"}
        response = self.client.put(
            f"/wishlists/{wishlist_id}/items/{item_id}", json=payload
        )

        # Return the updated item itself, including its unchanged identity and parent.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.is_json)
        expected = {"id": item_id, "wishlist_id": wishlist_id, **payload}
        self.assertEqual(response.get_json(), expected)

        # Read fresh database state to verify persistence and preservation of the wishlist.
        db.session.remove()
        saved_item = Item.find(item_id)
        self.assertIsNotNone(saved_item)
        self.assertEqual(saved_item.serialize(), expected)
        saved_wishlist = WishList.find(wishlist_id)
        self.assertIsNotNone(saved_wishlist)
        self.assertEqual(saved_wishlist.name, "Update item test")
        self.assertEqual(saved_wishlist.customer_id, 1001)

    def _create_item_for_update(self, name="Item update validation"):
        """Prepare persisted records for the story #15 tests."""
        # Use explicit attributes to avoid ORM constructor inference issues in Pylint.
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
        # Only one parent and item exist, so the next IDs are absent.
        wishlist_id, item_id = self._create_item_for_update()
        original = Item.find(item_id).serialize()
        cases = [
            (
                f"/wishlists/{wishlist_id + 1}/items/{item_id}",
                f"Wishlist with id '{wishlist_id + 1}' was not found",
            ),
            (
                f"/wishlists/{wishlist_id}/items/{item_id + 1}",
                f"Item with id '{item_id + 1}' was not found in Wishlist '{wishlist_id}'",
            ),
        ]
        for path, expected_message in cases:
            with self.subTest(path=path):
                # A missing resource must produce the existing structured JSON error.
                response = self.client.put(path, json={"product_id": 1002, "quantity": 2})
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
                self.assertTrue(response.is_json)
                self.assertEqual(response.get_json()["status"], status.HTTP_404_NOT_FOUND)
                self.assertEqual(
                    response.get_json()["message"], f"404 Not Found: {expected_message}"
                )

        # Failed lookups must leave the existing records intact.
        db.session.remove()
        self.assertEqual(Item.find(item_id).serialize(), original)
        self.assertIsNotNone(WishList.find(wishlist_id))

    def test_update_item_from_another_wishlist(self):
        """It should reject an item that belongs to another wishlist"""
        # Prepare two separate wishlists and preserve both items for comparison.
        wishlist_id, item_id = self._create_item_for_update("First wishlist")
        other_wishlist_id, other_item_id = self._create_item_for_update("Second wishlist")
        original = Item.find(item_id).serialize()
        other_original = Item.find(other_item_id).serialize()

        # An existing item is still not found under the wrong parent URL.
        response = self.client.put(
            f"/wishlists/{wishlist_id}/items/{other_item_id}",
            json={"product_id": 1002, "quantity": 2},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.is_json)
        self.assertEqual(
            response.get_json()["message"],
            "404 Not Found: "
            f"Item with id '{other_item_id}' was not found in Wishlist '{wishlist_id}'",
        )

        # Check fresh database state to ensure neither item was modified or moved.
        db.session.remove()
        self.assertEqual(Item.find(item_id).serialize(), original)
        self.assertEqual(Item.find(other_item_id).serialize(), other_original)
        self.assertIsNotNone(WishList.find(wishlist_id))
        self.assertIsNotNone(WishList.find(other_wishlist_id))

    def test_update_wishlist_item_invalid_data(self):
        """It should return JSON 400 for invalid fields without changing stored data"""
        # Exercise required fields, integer types, positive quantity, and the note schema.
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
                # Give each case independent records so one failed update cannot contaminate later cases.
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

                # Invalid input must not leave partial changes in memory or in the database.
                self.assertEqual(Item.find(item_id).serialize(), original)
                db.session.remove()
                self.assertEqual(Item.find(item_id).serialize(), original)
                self.assertIsNotNone(WishList.find(wishlist_id))

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

    ######################################################################
    #  I T E M   T E S T   C A S E S
    ######################################################################

    def test_list_wishlist_items(self):
        """It should List all Items in a Wishlist"""
        wishlist = WishListFactory()
        for item in ItemFactory.create_batch(2, wishlist=wishlist):
            wishlist.items.append(item)
        wishlist.create()
        expected_ids = sorted(item.id for item in wishlist.items)

        response = self.client.get(f"/wishlists/{wishlist.id}/items")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual([item["id"] for item in data], expected_ids)
        for item in data:
            self.assertEqual(item["wishlist_id"], wishlist.id)

    def test_list_wishlist_items_ordered_by_id(self):
        """It should List Items in id order even after one is updated"""
        wishlist = WishListFactory()
        for item in ItemFactory.create_batch(3, wishlist=wishlist):
            wishlist.items.append(item)
        wishlist.create()
        expected_ids = sorted(item.id for item in wishlist.items)

        # Updating a row can change the order Postgres returns rows in
        first_item = Item.find(expected_ids[0])
        first_item.note = "updated note"
        first_item.update()

        response = self.client.get(f"/wishlists/{wishlist.id}/items")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.get_json()], expected_ids)

    def test_list_wishlist_items_only_from_that_wishlist(self):
        """It should only List the Items that belong to the given Wishlist"""
        wishlist = WishListFactory()
        wishlist.items.append(ItemFactory(wishlist=wishlist))
        wishlist.create()
        other = WishListFactory()
        other.items.append(ItemFactory(wishlist=other))
        other.create()

        response = self.client.get(f"/wishlists/{wishlist.id}/items")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["wishlist_id"], wishlist.id)

    def test_list_wishlist_items_empty(self):
        """It should return an empty list when a Wishlist has no Items"""
        wishlist = WishListFactory()
        wishlist.create()

        response = self.client.get(f"/wishlists/{wishlist.id}/items")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_list_wishlist_items_wishlist_not_found(self):
        """It should return 404 Not Found when the Wishlist does not exist"""
        response = self.client.get("/wishlists/0/items")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.content_type, "application/json")
        data = response.get_json()
        self.assertEqual(data["error"], "Not Found")
        self.assertIn("Wishlist with id '0' was not found", data["message"])

    def test_get_wishlist_item(self):
        """It should Read a product in a Wishlist"""
        wishlist = self._create_wishlist()
        item = ItemFactory(wishlist=wishlist, wishlist_id=wishlist.id)
        item.create()

        response = self.client.get(f"/wishlists/{wishlist.id}/items/{item.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content_type, "application/json")
        data = response.get_json()
        self.assertEqual(data["id"], item.id)
        self.assertEqual(data["wishlist_id"], wishlist.id)
        self.assertEqual(data["product_id"], item.product_id)
        self.assertEqual(data["quantity"], item.quantity)
        self.assertEqual(data["note"], item.note)

    def test_get_wishlist_item_wishlist_not_found(self):
        """It should return 404 Not Found when the Wishlist does not exist"""
        response = self.client.get("/wishlists/0/items/1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.content_type, "application/json")
        data = response.get_json()
        self.assertEqual(data["error"], "Not Found")
        self.assertIn("Wishlist", data["message"])
        self.assertIn("was not found", data["message"])

    def test_get_wishlist_item_not_found(self):
        """It should return 404 Not Found when the Item does not exist"""
        wishlist = self._create_wishlist()
        response = self.client.get(f"/wishlists/{wishlist.id}/items/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.content_type, "application/json")
        data = response.get_json()
        self.assertEqual(data["error"], "Not Found")
        self.assertIn("Item", data["message"])
        self.assertIn("was not found", data["message"])

    def test_get_wishlist_item_in_other_wishlist(self):
        """It should return 404 Not Found when the Item belongs to another Wishlist"""
        wishlist = self._create_wishlist()
        other_wishlist = self._create_wishlist()
        item = ItemFactory(wishlist=other_wishlist, wishlist_id=other_wishlist.id)
        item.create()

        response = self.client.get(f"/wishlists/{wishlist.id}/items/{item.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertEqual(data["error"], "Not Found")
        self.assertIn("Item", data["message"])
