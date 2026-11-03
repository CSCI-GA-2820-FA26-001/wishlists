"""Route tests for product-specific Item queries within a Wishlist."""

import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Item, WishList
from tests.factories import WishListFactory, ItemFactory

# pylint: disable=duplicate-code

BASE_URL = "/wishlists"


class TestItemQueryService(TestCase):
    """Verify product filtering and query validation through the API."""

    @classmethod
    def setUpClass(cls):
        """Configure the application and retain a context for these tests."""
        cls.app_context = app.app_context()
        cls.app_context.push()
        app.config.update(TESTING=True, DEBUG=False)
        app.logger.setLevel(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        """Release this test class's database session and application context."""
        db.session.remove()
        cls.app_context.pop()

    def setUp(self):
        """Start each case with an empty test database."""
        self.client = app.test_client()
        for model in (Item, WishList):
            db.session.query(model).delete()
        db.session.commit()

    def tearDown(self):
        """Release the session after each test."""
        db.session.remove()

    def _create_wishlist(self, *product_ids):
        """Create a Wishlist holding one Item for each given product_id."""
        wishlist = WishListFactory()
        wishlist.create()
        for product_id in product_ids:
            ItemFactory(wishlist=wishlist, wishlist_id=wishlist.id, product_id=product_id).create()
        return wishlist

    def test_list_items_by_product_id(self):
        """It should return only the Items for the selected product in that Wishlist"""
        wishlist = self._create_wishlist(123, 456, 123)
        self._create_wishlist(123)

        response = self.client.get(f"{BASE_URL}/{wishlist.id}/items", query_string={"product_id": 123})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content_type, "application/json")
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual([item["id"] for item in data], sorted(item["id"] for item in data))
        for item in data:
            self.assertEqual(item["wishlist_id"], wishlist.id)
            self.assertEqual(item["product_id"], 123)

    def test_list_items_by_product_id_in_other_wishlist(self):
        """It should return an empty JSON list when the product is only in another Wishlist"""
        wishlist = self._create_wishlist(456)
        self._create_wishlist(123)

        response = self.client.get(f"{BASE_URL}/{wishlist.id}/items", query_string={"product_id": 123})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.get_json(), [])
        self.assertEqual(len(Item.all()), 2)

    def test_list_items_without_product_filter(self):
        """It should still return every Item in the Wishlist without a filter"""
        wishlist = self._create_wishlist(123, 456, 789)

        response = self.client.get(f"{BASE_URL}/{wishlist.id}/items")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(sorted(item["product_id"] for item in data), [123, 456, 789])

    def test_list_items_with_invalid_product_id(self):
        """It should reject invalid product filters with a JSON error"""
        wishlist = self._create_wishlist(123)

        for product_id in ("", "abc", "1.5", "123,456", "true"):
            with self.subTest(product_id=product_id):
                response = self.client.get(
                    f"{BASE_URL}/{wishlist.id}/items", query_string={"product_id": product_id}
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.content_type, "application/json")
                data = response.get_json()
                self.assertEqual(data["status"], status.HTTP_400_BAD_REQUEST)
                self.assertEqual(data["error"], "Bad Request")
                self.assertIn("product_id", data["message"])

    def test_list_items_with_multiple_product_ids(self):
        """It should reject repeated product filters with a JSON error"""
        wishlist = self._create_wishlist(123, 456)

        response = self.client.get(
            f"{BASE_URL}/{wishlist.id}/items",
            query_string=[("product_id", "123"), ("product_id", "456")],
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content_type, "application/json")
        self.assertIn("product_id", response.get_json()["message"])

    def test_list_items_by_product_id_wishlist_not_found(self):
        """It should return 404 Not Found when the Wishlist does not exist"""
        response = self.client.get(f"{BASE_URL}/0/items", query_string={"product_id": 123})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.content_type, "application/json")
        self.assertIn("Wishlist with id '0' was not found", response.get_json()["message"])
