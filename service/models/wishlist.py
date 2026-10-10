"""
WishList Model
"""

from .persistent_base import db, PersistentBase, DataValidationError
from .item import Item

class WishList(db.Model, PersistentBase):
    """
    Class that represents a WishList
    """

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(256), nullable=True)  # optional note field
    items = db.relationship(
        "Item",
        backref="wishlist",
        lazy=True,
        cascade="all, delete-orphan",
    )

    @classmethod
    def find_by_name(cls, name: str):
        """Returns all WishLists with the given name"""
        return cls.query.filter(cls.name == name).all()

    def serialize(self) -> dict:
        """Convert a WishList into a dictionary"""
        wishlist = { 
            "id": self.id,
            "name": self.name,
            "customer_id": self.customer_id,
            "note": self.note,
            "items": [],
        }
        for item in self.items:
            wishlist["items"].append(item.serialize())
        return wishlist

    def deserialize(self, data: dict) -> "WishList":
        """Convert a dictionary into a WishList"""
        try:
            self.name = data["name"]
            self.customer_id = data["customer_id"]
            self.note = data.get("note")  # optional field
            # handle inner list of items
            items = data.get("items", [])
            for item in items:
                new_item = Item()
                new_item.deserialize(item)
                self.items.append(new_item)
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid WishList: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid WishList: body of request contained bad or no data "
                + str(error)
            ) from error
        return self
