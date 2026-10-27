"""Query input model for listing WishLists."""

from .persistent_base import DataValidationError
from .wishlist import WishList


class WishListQuery:
    """Deserialize and execute optional Wishlist filters."""

    def __init__(self):
        self.customer_id = None

    def deserialize(self, data):
        """Validate query values without changing the stored Wishlist model."""
        self.customer_id = None
        customer_ids = data.get("customer_id", [])
        if len(customer_ids) > 1:
            raise DataValidationError("Only one customer_id filter is supported")
        if customer_ids:
            try:
                self.customer_id = int(customer_ids[0])
            except ValueError as error:
                raise DataValidationError("customer_id must be an integer") from error
        return self

    def find(self):
        """Return all WishLists or only those belonging to the selected customer."""
        if self.customer_id is None:
            return WishList.all()
        return WishList.find_by_customer_id(self.customer_id)
