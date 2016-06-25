"""
Item classes for the stuff that may be put in the inventories
"""

class Item(object):
    """
    Base class for the inventory item
    """
    def __init__(self, name='Item', owner=None):
        self.name = name
        #  Owner is an inventory component, not an actor
        self.owner = owner

    def use(self):
        """
        This method uses the item. It should be overloaded in child classes.
        :return:
        """
        raise NotImplementedError('use should be overloaded in Item\'s child')


class PotionTypeItem(Item):
    """
    Single-use items that affect whoever uses them.
    When creating object, it should be supplied with the effect parameter, which
    should be a function accepting actor as a single parameter.
    """
    def __init__(self, effect=lambda a: None, **kwargs):
        super(PotionTypeItem, self).__init__(**kwargs)
        self.effect = effect

    def use(self):
        self.effect(self.owner)