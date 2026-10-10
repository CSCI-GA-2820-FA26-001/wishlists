"""
Test Factory to make fake objects for testing
"""

import factory
from service.models import WishList, Item

class WishListFactory(factory.Factory):
    """Creates fake pets that you don't have to feed"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = WishList

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("name")
    customer_id = factory.Faker("random_int", min=1001, max=9999)
    note = factory.Faker("sentence", nb_words=6, variable_nb_words=True)

    @factory.post_generation
    def items(self, create, extracted, **kwargs):
        """Create a list of items for the wishlist"""
        if not create:
            return

        if extracted:
            # A list of items were passed in, use them
            for item in extracted:
                self.items.append(item)
        

class ItemFactory(factory.Factory):
    """Creates fake items for testing"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Item

    id = factory.Sequence(lambda n: n)
    wishlist_id = factory.Faker("random_int", min=1, max=100)
    product_id = factory.Faker("random_int", min=1001, max=9999)
    note = factory.Faker("sentence", nb_words=6, variable_nb_words=True)
    wishlist = factory.SubFactory(WishListFactory)
