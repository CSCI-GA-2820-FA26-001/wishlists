"""
WishList Model
"""

from .persistent_base import db, PersistentBase, DataValidationError


class WishList(db.Model, PersistentBase):
    """
    Class that represents a WishList
    """

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(256), nullable=True)  # optional note field

    @classmethod
    def find_by_name(cls, name: str):
        """Returns all WishLists with the given name"""
        return cls.query.filter(cls.name == name).all()

    def serialize(self) -> dict:
        """Convert a WishList into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "customer_id": self.customer_id,
            "note": self.note,
        }

    def deserialize(self, data: dict) -> "WishList":
        """Convert a dictionary into a WishList"""
        try:
            self.id = data["id"]
            self.name = data["name"]
            self.customer_id = data["customer_id"]
            self.note = data.get("note")  # optional field
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
