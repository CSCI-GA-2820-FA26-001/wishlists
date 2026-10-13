"""
Test cases for the Item Model
"""

import os
import logging
from unittest import TestCase
from wsgi import app
from service.models import WishList, Item, db, DataValidationError
from tests.factories import WishListFactory, ItemFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)


class TestItemModel(TestCase):
    """Item Model Test Cases"""

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

    def test_add_wishlist_item(self):
        """It should Create a wishlist with an item and add it to the database"""
        self.assertEqual(WishList.all(), [])

        wishlist = WishListFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.items.append(item)
        wishlist.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(wishlist.id)
        self.assertEqual(len(WishList.all()), 1)

        # Fetch it back and check the item was saved with it
        new_wishlist = WishList.find(wishlist.id)
        self.assertEqual(len(new_wishlist.items), 1)
        self.assertEqual(new_wishlist.items[0].product_id, item.product_id)
        self.assertEqual(new_wishlist.items[0].quantity, item.quantity)
        self.assertEqual(new_wishlist.items[0].note, item.note)
        self.assertEqual(new_wishlist.items[0].wishlist_id, wishlist.id)

        # Add a second item to the same wishlist
        item2 = ItemFactory(wishlist=wishlist)
        wishlist.items.append(item2)
        wishlist.update()

        new_wishlist = WishList.find(wishlist.id)
        self.assertEqual(len(new_wishlist.items), 2)
        self.assertEqual(new_wishlist.items[1].product_id, item2.product_id)

    def test_read_item(self):
        """It should Read an item by its id"""
        wishlist = WishListFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.items.append(item)
        wishlist.create()
        self.assertIsNotNone(item.id)

        found_item = Item.find(item.id)
        self.assertIsNotNone(found_item)
        self.assertEqual(found_item.id, item.id)
        self.assertEqual(found_item.wishlist_id, wishlist.id)
        self.assertEqual(found_item.product_id, item.product_id)
        self.assertEqual(found_item.quantity, item.quantity)
        self.assertEqual(found_item.note, item.note)

    def test_read_item_not_found(self):
        """It should return None when an item is not found"""
        self.assertIsNone(Item.find(0))

    def test_list_wishlist_items(self):
        """It should List all items in a wishlist"""
        wishlist = WishListFactory()
        for item in ItemFactory.create_batch(3, wishlist=wishlist):
            wishlist.items.append(item)
        wishlist.create()

        wishlist = WishList.find(wishlist.id)
        self.assertEqual(len(wishlist.items), 3)
        self.assertEqual(len(Item.all()), 3)

    def test_update_wishlist_item(self):
        """It should Update an item in a wishlist"""
        wishlist = WishListFactory()
        item = ItemFactory(wishlist=wishlist, note="old note")
        wishlist.items.append(item)
        wishlist.create()

        # Fetch it back and change the note
        wishlist = WishList.find(wishlist.id)
        old_item = wishlist.items[0]
        self.assertEqual(old_item.note, "old note")
        old_item.note = "gift wrap please"
        wishlist.update()

        # Fetch it back again and make sure the change was saved
        wishlist = WishList.find(wishlist.id)
        self.assertEqual(len(wishlist.items), 1)
        self.assertEqual(wishlist.items[0].id, old_item.id)
        self.assertEqual(wishlist.items[0].note, "gift wrap please")

    def test_delete_wishlist_item(self):
        """It should Delete an item from a wishlist"""
        wishlist = WishListFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.items.append(item)
        wishlist.create()

        # Fetch it back and delete the item
        wishlist = WishList.find(wishlist.id)
        self.assertEqual(len(wishlist.items), 1)
        item_to_delete = wishlist.items[0]
        item_to_delete.delete()

        # Fetch it back again and make sure the item is gone
        wishlist = WishList.find(wishlist.id)
        self.assertEqual(len(wishlist.items), 0)
        self.assertEqual(len(Item.all()), 0)
        # The wishlist itself should still be there
        self.assertEqual(len(WishList.all()), 1)

    def test_delete_wishlist_deletes_items(self):
        """It should delete all Items when their WishList is deleted"""
        wishlist = WishListFactory()
        wishlist.items.append(ItemFactory(wishlist=wishlist))
        wishlist.items.append(ItemFactory(wishlist=wishlist))
        wishlist.create()
        self.assertEqual(len(Item.all()), 2)

        wishlist.delete()
        self.assertEqual(len(WishList.all()), 0)
        self.assertEqual(len(Item.all()), 0)

    def test_serialize_an_item(self):
        """It should serialize an item"""
        item = ItemFactory()
        serialize_item = item.serialize()
        self.assertEqual(serialize_item["id"], item.id)
        self.assertEqual(serialize_item["wishlist_id"], item.wishlist_id)
        self.assertEqual(serialize_item["product_id"], item.product_id)
        self.assertEqual(serialize_item["quantity"], item.quantity)
        self.assertEqual(serialize_item["note"], item.note)

    def test_deserialize_an_item(self):
        """It should deserialize an item"""
        item = ItemFactory()
        item.create()

        new_item = Item()
        new_item.deserialize(item.serialize())
        self.assertEqual(new_item.wishlist_id, item.wishlist_id)
        self.assertEqual(new_item.product_id, item.product_id)
        self.assertEqual(new_item.quantity, item.quantity)
        self.assertEqual(new_item.note, item.note)

    def test_deserialize_item_without_note(self):
        """It should deserialize an item when the optional note is missing"""
        item = Item()
        item.deserialize({"wishlist_id": 1, "product_id": 1234, "quantity": 1})
        self.assertEqual(item.product_id, 1234)
        self.assertEqual(item.quantity, 1)
        self.assertIsNone(item.note)

    def test_deserialize_item_missing_quantity(self):
        """It should not deserialize an item without a quantity"""
        item = Item()
        self.assertRaises(
            DataValidationError,
            item.deserialize,
            {"wishlist_id": 1, "product_id": 1234},
        )

    def test_deserialize_item_with_quantity(self):
        """It should deserialize an item with a quantity"""
        item = Item()
        item.deserialize({"wishlist_id": 1, "product_id": 1234, "quantity": 3})
        self.assertEqual(item.quantity, 3)

    def test_deserialize_item_bad_quantity_type(self):
        """It should not deserialize an item with a non-integer quantity"""
        for bad in ["3", 2.5, True, None]:
            item = Item()
            self.assertRaises(
                DataValidationError,
                item.deserialize,
                {"wishlist_id": 1, "product_id": 1234, "quantity": bad},
            )

    def test_deserialize_item_bad_quantity_value(self):
        """It should not deserialize an item with a quantity less than 1"""
        for bad in [0, -1]:
            item = Item()
            self.assertRaises(
                DataValidationError,
                item.deserialize,
                {"wishlist_id": 1, "product_id": 1234, "quantity": bad},
            )

    def test_update_item_quantity(self):
        """It should Update the quantity of an item in a wishlist"""
        wishlist = WishListFactory()
        item = ItemFactory(wishlist=wishlist, quantity=1)
        wishlist.items.append(item)
        wishlist.create()

        wishlist = WishList.find(wishlist.id)
        wishlist.items[0].quantity = 5
        wishlist.update()

        wishlist = WishList.find(wishlist.id)
        self.assertEqual(wishlist.items[0].quantity, 5)

    def test_deserialize_item_key_error(self):
        """It should not deserialize an item with missing fields"""
        item = Item()
        self.assertRaises(DataValidationError, item.deserialize, {})

    def test_deserialize_item_type_error(self):
        """It should not deserialize an item from bad data"""
        item = Item()
        self.assertRaises(DataValidationError, item.deserialize, [])

    def test_deserialize_item_attribute_error(self):
        """It should translate attribute errors when deserializing an item"""

        class InvalidData:  # pylint: disable=too-few-public-methods
            """Data that raises AttributeError on access"""

            def __getitem__(self, key):
                raise AttributeError(key)

        item = Item()
        self.assertRaises(DataValidationError, item.deserialize, InvalidData())
