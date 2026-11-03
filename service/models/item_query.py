"""Query input model for listing the Items in a WishList."""

from .persistent_base import DataValidationError
from .item import Item


class ItemQuery:
    """Deserialize and execute optional Item filters."""

    def __init__(self):
        self.product_id = None

    def deserialize(self, data):
        """Validate query values without changing the stored Item model."""
        self.product_id = None
        product_ids = data.get("product_id", [])
        if len(product_ids) > 1:
            raise DataValidationError("Only one product_id filter is supported")
        if product_ids:
            try:
                self.product_id = int(product_ids[0])
            except ValueError as error:
                raise DataValidationError("product_id must be an integer") from error
        return self

    def find(self, wishlist):
        """Return all Items in the WishList or only those for the selected product."""
        if self.product_id is None:
            return sorted(wishlist.items, key=lambda item: item.id)
        return Item.find_by_product_id(wishlist.id, self.product_id)
