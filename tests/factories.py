"""
Test Factory to make fake objects for testing
"""

import factory
from service.models import WishList


class WishListFactory(factory.Factory):
    """Creates fake pets that you don't have to feed"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = WishList

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("name")
    customer_id = factory.Faker("random_int", min=1001, max=9999)
    note = factory.Faker("sentence", nb_words=6, variable_nb_words=True)

    # Todo: Add your other attributes here...
