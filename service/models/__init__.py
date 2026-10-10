"""
Models for Wishlist

All of the models are stored in this package.
"""

from .persistent_base import db, PersistentBase, DataValidationError
from .wishlist import WishList
from .item import Item
