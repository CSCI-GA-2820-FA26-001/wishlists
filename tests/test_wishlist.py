"""
Test cases for the WishList Model
"""

import os
import logging
from unittest import TestCase
from service.models import WishList, db
from wsgi import app
from tests.factories import WishListFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)


class TestWishListModel(TestCase):
    """Wishlist Model Test Cases"""

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
        db.session.query(WishList).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    # TEST CASES FOR WishList MODEL
    def test_create_wishlist(self):
        """It should create a wishlist and assert its attributes"""
        fake_wishlist = WishListFactory()

        wishlist = WishList(
            id=fake_wishlist.id,
            name=fake_wishlist.name,
            customer_id=fake_wishlist.customer_id,
            note=fake_wishlist.note
        )
        self.assertIsNotNone(wishlist)
        self.assertEqual(wishlist.id, fake_wishlist.id)
        self.assertEqual(wishlist.name, fake_wishlist.name)
        self.assertEqual(wishlist.customer_id, fake_wishlist.customer_id)
        self.assertEqual(wishlist.note, fake_wishlist.note)

    def test_add_wishlist_to_db(self):
        """It should add a wishlist to the database and retrieve it"""
        wishlists = WishList.all()
        self.assertEqual(wishlists, [])

        wishlist = WishListFactory()
        wishlist.create()
        # Assert that it was assigned an id and can be found in the database
        self.assertIsNotNone(wishlist.id)
        wishlists = WishList.all()
        self.assertEqual(len(wishlists), 1)



    
    
