"""Route tests for customer-specific Wishlist queries."""

import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Item, WishList
from tests.factories import WishListFactory, ItemFactory

BASE_URL = "/wishlists"


class TestWishListQueryService(TestCase):
    """Verify customer filtering and query validation through the API."""

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

    def test_list_wishlists_without_customer_filter(self):
        """It should still return WishLists from different customers without a filter"""
        birthday = WishListFactory(name="Birthday", customer_id=1001)
        birthday.create()
        holiday = WishListFactory(name="Holiday", customer_id=1002)
        holiday.create()

        response = self.client.get(BASE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content_type, "application/json")
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual({wishlist["id"] for wishlist in data}, {birthday.id, holiday.id})

    def test_list_wishlists_by_customer_id(self):
        """It should return only the selected customer's WishLists and their items"""
        birthday = WishListFactory(name="Birthday", customer_id=1001)
        birthday.create()
        holiday = WishListFactory(name="Holiday", customer_id=1001)
        holiday.create()
        other_wishlist = WishListFactory(name="Birthday", customer_id=1002)
        other_wishlist.create()
        ItemFactory(wishlist=birthday, wishlist_id=birthday.id).create()
        ItemFactory(wishlist=other_wishlist, wishlist_id=other_wishlist.id).create()

        response = self.client.get(BASE_URL, query_string={"customer_id": 1001})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content_type, "application/json")
        data = response.get_json()
        self.assertIsInstance(data, list)
        by_id = {wishlist["id"]: wishlist for wishlist in data}
        self.assertEqual(set(by_id), {birthday.id, holiday.id})
        for expected in (birthday, holiday):
            self.assertEqual(by_id[expected.id], expected.serialize())
        self.assertEqual(len(WishList.all()), 3)
        self.assertEqual(len(Item.all()), 2)

    def test_list_wishlists_by_customer_id_not_found(self):
        """It should return an empty JSON list when a customer has no WishLists"""
        WishListFactory(customer_id=1002).create()

        response = self.client.get(BASE_URL, query_string={"customer_id": 1001})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.get_json(), [])
        self.assertEqual(len(WishList.all()), 1)

    def test_list_wishlists_with_invalid_customer_id(self):
        """It should reject invalid customer filters with a JSON error"""
        WishListFactory(customer_id=1001).create()
        WishListFactory(customer_id=1002).create()

        for customer_id in ("", "abc", "1.5", "1001,1002", "true"):
            with self.subTest(customer_id=customer_id):
                response = self.client.get(BASE_URL, query_string={"customer_id": customer_id})

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.content_type, "application/json")
                data = response.get_json()
                self.assertEqual(data["status"], status.HTTP_400_BAD_REQUEST)
                self.assertEqual(data["error"], "Bad Request")
                self.assertIn("customer_id", data["message"])
                self.assertEqual(len(WishList.all()), 2)

    def test_list_wishlists_with_multiple_customer_ids(self):
        """It should reject repeated customer filters with a JSON error"""
        WishListFactory(customer_id=1001).create()
        WishListFactory(customer_id=1002).create()

        for customer_ids in (("1001", "1002"), ("1001", "1001")):
            with self.subTest(customer_ids=customer_ids):
                response = self.client.get(
                    BASE_URL,
                    query_string=[("customer_id", customer_id) for customer_id in customer_ids],
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.content_type, "application/json")
                data = response.get_json()
                self.assertEqual(data["status"], status.HTTP_400_BAD_REQUEST)
                self.assertEqual(data["error"], "Bad Request")
                self.assertIn("customer_id", data["message"])
                self.assertEqual(len(WishList.all()), 2)
