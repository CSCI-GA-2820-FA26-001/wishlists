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

    def deserialize(self, data: dict) -> None:
        """Convert a dictionary into an Item"""
        try:
            self.wishlist_id = data["wishlist_id"]
            self.product_id = data["product_id"]
            quantity = data["quantity"]
            if isinstance(quantity, bool) or not isinstance(quantity, int):
                raise DataValidationError(
                    "Invalid type for integer [quantity]: " + str(type(quantity))
                )
            if quantity < 1:
                raise DataValidationError(
                    "Invalid value for [quantity]: must be at least 1"
                )
            self.quantity = quantity
            self.note = data.get("note")  # optional field
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Item: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Item: body of request contained bad or no data "
                + str(error)
            ) from error
