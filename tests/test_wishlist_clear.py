"""Tests for the wishlist clear action."""

import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Item, WishList
from tests.factories import WishListFactory, ItemFactory

BASE_URL = "/wishlists"


class TestWishlistClearService(TestCase):
    """Verify the clear action through the API and persisted database state."""

    @classmethod
    def setUpClass(cls):
        """Configure the application once for these tests."""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.logger.setLevel(logging.CRITICAL)
        cls.app_context = app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        """Close the database session after these tests."""
        db.session.remove()
        cls.app_context.pop()

    def setUp(self):
        """Create a client and remove data from the previous test."""
        self.client = app.test_client()
        db.session.query(Item).delete()
        db.session.query(WishList).delete()
        db.session.commit()

    def tearDown(self):
        """Remove the session after each test."""
        db.session.remove()

    def test_clear_wishlist(self):
        """It should clear only the requested wishlist and return its JSON"""
        wishlist = WishListFactory(items=ItemFactory.create_batch(2))
        wishlist.create()
        other = WishListFactory(items=[ItemFactory()])
        other.create()
        wishlist_id, other_id = wishlist.id, other.id
        expected = wishlist.serialize()
        expected["items"] = []
        other_data = other.serialize()

        response = self.client.put(f"{BASE_URL}/{wishlist_id}/clear")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.get_json(), expected)
        db.session.remove()
        self.assertEqual(WishList.find(wishlist_id).serialize(), expected)
        self.assertEqual(Item.query.filter_by(wishlist_id=wishlist_id).count(), 0)
        self.assertEqual(WishList.find(other_id).serialize(), other_data)

    def test_clear_empty_wishlist(self):
        """It should return 200 when an empty wishlist is cleared repeatedly"""
        wishlist = WishListFactory()
        wishlist.create()
        wishlist_id = wishlist.id
        expected = wishlist.serialize()

        for _ in range(2):
            response = self.client.put(f"{BASE_URL}/{wishlist_id}/clear")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.is_json)
            self.assertEqual(response.get_json(), expected)
            db.session.remove()
            self.assertEqual(WishList.find(wishlist_id).serialize(), expected)

    def test_clear_wishlist_not_found(self):
        """It should return a JSON 404 for the same nonexistent wishlist ID"""
        wishlist_id = 99
        self.assertIsNone(WishList.find(wishlist_id))

        response = self.client.put(f"{BASE_URL}/{wishlist_id}/clear")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data["error"], "Not Found")
        self.assertIn(str(wishlist_id), data["message"])
