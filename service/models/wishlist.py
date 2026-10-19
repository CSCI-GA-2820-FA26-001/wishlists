"""
WishList Model
"""

from .persistent_base import db, PersistentBase, DataValidationError


class WishList(db.Model, PersistentBase):
    """
    Class that represents a WishList
    """

    # A customer can't have two wishlists with the same name
    __table_args__ = (
        db.UniqueConstraint(
            "customer_id", "name", name="uq_wish_list_customer_id_name"
        ),
    )

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
        """
        Convert a dictionary into a WishList

        Items are ignored here; they are managed through the item endpoints
        """
        try:
            name = data["name"]
            if not isinstance(name, str):
                raise DataValidationError(
                    "Invalid type for string [name]: " + str(type(name))
                )
            if not name:
                raise DataValidationError("Invalid value for [name]: must not be empty")
            customer_id = data["customer_id"]
            if isinstance(customer_id, bool) or not isinstance(customer_id, int):
                raise DataValidationError(
                    "Invalid type for integer [customer_id]: " + str(type(customer_id))
                )
            note = data.get("note")  # optional field
            if note is not None and not isinstance(note, str):
                raise DataValidationError(
                    "Invalid type for string [note]: " + str(type(note))
                )
            self.name = name
            self.customer_id = customer_id
            self.note = note
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
