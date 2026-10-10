"""
WishList Model
"""

from .persistent_base import db, PersistentBase


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

    

