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

    def test_read_wishlist(self):
        """It should read a wishlist from the database"""
        wishlist = WishListFactory()
        wishlist.create()

        found_wishlist = WishList.find(wishlist.id)
        self.assertIsNotNone(found_wishlist)
        self.assertEqual(found_wishlist.id, wishlist.id)
        self.assertEqual(found_wishlist.name, wishlist.name)
        self.assertEqual(found_wishlist.customer_id, wishlist.customer_id)
        self.assertEqual(found_wishlist.note, wishlist.note)

    def test_update_wishlist(self):
        """It should update a wishlist in the database"""
        name = "21st Birthday Wishlist"
     
        wishlist = WishListFactory(name=name)
        wishlist.create()

        self.assertEqual(wishlist.name, name)

        # Fetch it back and update it
        wishlist = WishList.find(wishlist.id)
        wishlist.name = "Updated Wishlist Name"
        wishlist.update()   

        # Fetch it back again and assert the name was updated
        updated_wishlist = WishList.find(wishlist.id)
        self.assertEqual(updated_wishlist.name, "Updated Wishlist Name")

    def test_delete_wishlist(self):
        """It should delete a wishlist from the database"""
        wishlists = WishList.all()
        self.assertEqual(wishlists, [])

        # Create a wishlist and add it to the database
        wishlist = WishListFactory()
        wishlist.create()
        self.assertIsNotNone(wishlist.id)

        wishlists = WishList.all()
        self.assertEqual(len(wishlists), 1)

        # Delete the wishlist and assert that it was removed
        wishlist = wishlists[0]
        wishlist.delete()
        wishlists = WishList.all()
        self.assertEqual(len(wishlists), 0)

    def test_list_all_wishlists(self):
        """It should List all WishLists in the database"""
        wishlists = WishList.all()
        self.assertEqual(wishlists, [])
        for wishlist in WishListFactory.create_batch(5):
            wishlist.create()
        # Assert that there are not 5 wishlists in the database
        wishlists = WishList.all()
        self.assertEqual(len(wishlists), 5)

    def test_find_by_name(self):
        """It should Find a Wishlist by name"""
        wishlist = WishListFactory()
        wishlist.create()

        # Fetch it back by name
        same_wishlist = WishList.find_by_name(wishlist.name)[0]
        self.assertEqual(same_wishlist.id, wishlist.id)
        self.assertEqual(same_wishlist.name, wishlist.name)

    def test_serialize_wishlist(self):
        """It should serialize a Wishlist into a dictionary"""
        wishlist = WishListFactory()
        wishlist.create()

        data = wishlist.serialize()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["id"], wishlist.id)
        self.assertEqual(data["name"], wishlist.name)
        self.assertEqual(data["customer_id"], wishlist.customer_id)
        self.assertEqual(data["note"], wishlist.note)




