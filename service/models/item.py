"""
Item Model
"""

from .persistent_base import db, PersistentBase, DataValidationError


class Item(db.Model, PersistentBase):
    """
    Class that represents an Item
    """

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    wishlist_id = db.Column(
        db.Integer, db.ForeignKey("wish_list.id", ondelete="CASCADE"), nullable=False
    )
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    note = db.Column(db.String(256), nullable=True)  # optional note field

    def serialize(self) -> dict:
        """Convert an Item into a dictionary"""
        return {
            "id": self.id,
            "wishlist_id": self.wishlist_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "note": self.note,
        }

    def deserialize(self, data: dict, default_quantity: int | None = None) -> "Item":
        """
        Convert a dictionary into an Item

        Args:
            data: the item fields; wishlist_id is optional because the
                route usually supplies it from the URL
            default_quantity: quantity to use when none is given
                (None means quantity is required)
        """
        try:
            product_id = data["product_id"]
            if isinstance(product_id, bool) or not isinstance(product_id, int):
                raise DataValidationError(
                    "Invalid Item: product_id must be an integer"
                )
            if "quantity" not in data and default_quantity is not None:
                quantity = default_quantity
            else:
                quantity = data["quantity"]
            if isinstance(quantity, bool) or not isinstance(quantity, int):
                raise DataValidationError(
                    "Invalid type for integer [quantity]: " + str(type(quantity))
                )
            if quantity < 1:
                raise DataValidationError(
                    "Invalid value for [quantity]: must be at least 1"
                )
            note = data.get("note")  # optional field
            if note is not None and (not isinstance(note, str) or len(note) > 256):
                raise DataValidationError(
                    "Invalid Item: note must be null or a string of at most 256 characters"
                )
            self.wishlist_id = data.get("wishlist_id", self.wishlist_id)
            self.product_id = product_id
            self.quantity = quantity
            self.note = note
        except AttributeError as error:
            raise DataValidationError("Invalid Item attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Item: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Item: body of request contained bad or no data "
                + str(error)
            ) from error
        return self
