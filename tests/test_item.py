import os
import logging
from unittest import TestCase
from wsgi import app
from service.models import WishList, Item, db, DataValidationError
from tests.factories import WishListFactory, ItemFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)

class TestWishListModel(TestCase):
    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Item).delete()  # clean up the last tests
        db.session.query(WishList).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    # Test cases for Item Model
    def test_add_wishlist_item(self):
        "It should Create a wishlist with an item and add it to the database"
        wishlists = WishList.all()
        self.assertEqual(wishlists, [])

        wishlist = WishListFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.items.append(item)
        wishlist.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(wishlist.id)
        wishlists = WishList.all()
        self.assertEqual(len(wishlists), 1)

    def test_update_wishlist_item(self):
        "It should update a item from wishlist"
        self.test_add_wishlist_item()

        # Fetch it back and update it
        wishlist = WishList.all()[0]
        self.assertEqual(len(wishlist.items), 1)

        new_item = ItemFactory(wishlist=wishlist)
        wishlist.items.append(new_item)
        wishlist.update()

        self.assertEqual(len(wishlist.items), 2)


        

    