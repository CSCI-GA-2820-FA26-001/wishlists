"""
Test cases for the WishList Model
"""

import os
import logging
from unittest import TestCase
from unittest.mock import patch
from service.models import WishList, Item, PersistentBase, db, DataValidationError
from wsgi import app
from tests.factories import WishListFactory, ItemFactory


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
        # Rebuild the tables so the schema (incl. unique constraints) matches the models
        db.drop_all()
        db.create_all()

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

    @patch("service.models.db.session.commit")
    def test_add_wishlist_failed(self, exception_mock):
        """It should not create an WishList on database error"""
        exception_mock.side_effect = Exception()
        wishlist = WishListFactory()
        self.assertRaises(DataValidationError, wishlist.create)

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
        self.assertEqual(found_wishlist.items, wishlist.items)

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

    @patch("service.models.db.session.commit")
    def test_update_wishlist_failed(self, exception_mock):
        """It should not update an WishList on database error"""
        exception_mock.side_effect = Exception()
        wishlist = WishListFactory()
        self.assertRaises(DataValidationError, wishlist.update)


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

    @patch("service.models.db.session.commit")
    def test_delete_wishlist_failed(self, exception_mock):
        """It should not delete an WishList on database error"""
        exception_mock.side_effect = Exception()
        wishlist = WishListFactory()
        self.assertRaises(DataValidationError, wishlist.delete)

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

    def test_create_duplicate_wishlist_name_for_customer(self):
        """It should not create two WishLists with the same name for one customer"""
        wishlist = WishListFactory(name="Birthday", customer_id=1001)
        wishlist.create()

        duplicate = WishListFactory(name="Birthday", customer_id=1001)
        self.assertRaises(DataValidationError, duplicate.create)
        self.assertEqual(len(WishList.all()), 1)

    def test_same_wishlist_name_for_different_customers(self):
        """It should allow different customers to use the same WishList name"""
        WishListFactory(name="Birthday", customer_id=1001).create()
        WishListFactory(name="Birthday", customer_id=1002).create()
        self.assertEqual(len(WishList.find_by_name("Birthday")), 2)

    def test_different_wishlist_names_for_same_customer(self):
        """It should allow one customer to have WishLists with different names"""
        WishListFactory(name="Birthday", customer_id=1001).create()
        WishListFactory(name="Holiday", customer_id=1001).create()
        self.assertEqual(len(WishList.all()), 2)

    def test_update_to_duplicate_wishlist_name(self):
        """It should not rename a WishList to a name the customer already uses"""
        WishListFactory(name="Birthday", customer_id=1001).create()
        wishlist = WishListFactory(name="Holiday", customer_id=1001)
        wishlist.create()
        # Load the id now so update() doesn't trigger an autoflush outside its try block
        wishlist_id = wishlist.id

        wishlist.name = "Birthday"
        self.assertRaises(DataValidationError, wishlist.update)

        # The session was rolled back, so the original name is unchanged
        self.assertEqual(WishList.find(wishlist_id).name, "Holiday")

    def test_serialize_wishlist(self):
        """It should serialize a Wishlist into a dictionary"""
        wishlist = WishListFactory()
        item = ItemFactory()

        wishlist.items.append(item)

        data = wishlist.serialize()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["id"], wishlist.id)
        self.assertEqual(data["name"], wishlist.name)
        self.assertEqual(data["customer_id"], wishlist.customer_id)
        self.assertEqual(data["note"], wishlist.note)
        self.assertEqual(len(data["items"]), 1)

        item_data = data["items"][0]
        self.assertEqual(item_data["id"], item.id)
        self.assertEqual(item_data["wishlist_id"], item.wishlist_id)
        self.assertEqual(item_data["product_id"], item.product_id)
        self.assertEqual(item_data["quantity"], item.quantity)
        self.assertEqual(item_data["note"], item.note)

    def test_deserialize_wishlist(self):
        """It should deserialize a dictionary into a Wishlist"""
        wishlist = WishListFactory()
        wishlist.create()

        data = wishlist.serialize()
        new_wishlist = WishList()
        new_wishlist.deserialize(data)

        self.assertEqual(new_wishlist.name, wishlist.name)
        self.assertEqual(new_wishlist.customer_id, wishlist.customer_id)
        self.assertEqual(new_wishlist.note, wishlist.note)

    def test_deserialize_with_key_error(self):
        """It should not Deserialize an wishlist with a KeyError"""
        wishlist = WishList()
        self.assertRaises(DataValidationError, wishlist.deserialize, {})

    def test_deserialize_with_type_error(self):
        """It should not Deserialize an wishlist with a TypeError"""
        wishlist = WishList()
        self.assertRaises(DataValidationError, wishlist.deserialize, [])

    def test_deserialize_ignores_items(self):
        """It should ignore nested items when deserializing a WishList"""
        data = {
            "name": "Birthday",
            "customer_id": 10,
            "items": [
                {
                    "id": 8,
                    "wishlist_id": 5,
                    "product_id": 12,
                    "quantity": 2,
                    "note": "Book",
                }
            ],
        }
        wishlist = WishList().deserialize(data)

        self.assertEqual(wishlist.name, "Birthday")
        self.assertEqual(wishlist.customer_id, 10)
        self.assertEqual(wishlist.items, [])

    def test_deserialize_without_items(self):
        """It should accept older wishlist data without an items field"""
        data = {"id": 5, "name": "Birthday", "customer_id": 10}

        wishlist = WishList().deserialize(data)

        self.assertEqual(wishlist.items, [])

    def test_deserialize_with_attribute_error(self):
        """It should translate attribute errors in input data"""

        class InvalidData:
            def __getitem__(self, key):
                raise AttributeError(key)

        with self.assertRaises(DataValidationError):
            WishList().deserialize(InvalidData())

    def test_persistent_base_initializes_id(self):
        """It should initialize a persistent model without an ID"""
        self.assertIsNone(PersistentBase().id)

    def test_update_without_id(self):
        """It should reject an update without an ID"""
        self.assertRaises(DataValidationError, WishList().update)
