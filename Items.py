"""
Item and Effect classes and their subclasses.
"""

from random import random, choice

from Actor import GameEvent
from Constructions import Construction
from MapItem import MapItem


class Effect(object):
    """
    Root effect class. Sets the following parameters:
    effect_type: str. The description of effect that should be processed by one of the subclasses. For example,
    'explode' or 'spawn_construction'.
    effect_value: The value of effect. Its type depends on effect_type: it can be Construction object for
    'spawn_construction' or int list for damage or healing
    require_targeting: bool. If set to true, GameWidget sets targeting game state before actually using this item;
     otherwise it is used immediately on PC or tile under PC. Defaults to False
    """
    def __init__(self, effect_type, effect_value, require_targeting=False):
        self.effect_type = effect_type
        self.effect_value = effect_value
        self.require_targeting = require_targeting


class FighterTargetedEffect(Effect):
    """
    Effect that affects the FighterComponent of an Actor
    """
    def __init__(self, **kwargs):
        super(FighterTargetedEffect, self).__init__(**kwargs)

    def affect(self, actor):
        if self.effect_type == 'heal':
            actor.fighter.hp += choice(self.effect_value)
            return True
        if self.effect_type == 'restore_ammo':
            actor.fighter.ammo += self.effect_value
            return True


class TileTargetedEffect(Effect):
    """
    Effect that affects map tile
    """
    def __init__(self, **kwargs):
        super(TileTargetedEffect, self).__init__(**kwargs)

    def affect(self, map, location):
        if self.effect_type == 'spawn_construction':
            #  Spawn something in construction layer unless there already is something
            if not map.get_item(location=location, layer='constructions'):
                map.add_item(item=self.effect_value, location=location, layer='constructions')
                map.game_events.append(GameEvent(event_type='construction_spawned',
                                                 actor=self.effect_value,
                                                 location=location))
                return True
            else:
                return False
        elif self.effect_type == 'explode':
            #  Blow up, dealing effect_value damage to all fighters on this and neighbouring tiles and
            #  destroying items with 50% chance. Spawn an impassable hole where explosion occured
            map.game_events.append(GameEvent(event_type='exploded', location=location))
            destroyed_items = False
            for tile in map.get_neighbour_coordinates(location=location, return_query=True):
                for victim in map.get_column(tile):
                    if hasattr(victim, 'fighter') and victim.fighter:
                        if isinstance(victim, Construction) and tile == location:
                            #  Deal over-the-top damage to constructions on ground zero
                            #  This means that, barring incredible defense, explosion under a costruction should
                            #  kill it outright
                            victim.fighter.get_damaged(victim.fighter.max_hp*2)
                        victim.fighter.get_damaged(self.effect_value)
                for victim in map.get_column(tile):
                    #  Items are checked in a separate cycle because items could've been dropped by killed enemies
                    if isinstance(victim, Item) and (random() > 0.5 or tile == location):
                        map.delete_item(layer='items', location=tile)
                        map.game_events.append(GameEvent(event_type='was_destroyed',
                                                         actor=victim, location=tile))
                        destroyed_items = True
            hole = Construction(image_source='Hole.png',
                                passable=False, air_passable=True)
            map.add_item(item=hole, location=location, layer='constructions')
            map.game_events.append(GameEvent(event_type='construction_spawned', actor=hole,
                                             location=location))
            if destroyed_items:
                map.extend_log('Some items were destroyed')
            return True


class Item(MapItem):
    """
    Base class for the inventory item. Inherits from MapItem to allow placing items on map.
    """
    def __init__(self, name='Item', image_source='Bottle.png', owner=None, descriptor=None,
                 event_type=None, **kwargs):
        super(Item, self).__init__(**kwargs)
        #  Owner is an inventory component, not an actor
        self.owner = owner
        self.descriptor = descriptor
        if self.descriptor:
            self.descriptor.actor = self
        self.image_source = image_source
        #  event_type currently is used only by TileTargeted items used with Target
        self.event_type = event_type

    @property
    def name(self):
        return self.descriptor.name

    @name.setter
    def name(self, value):
        self.descriptor.name = value

    def use(self):
        """
        This method uses the item. It should be overridden in child classes.
        The override should return True upon successfully using an item
        :return:
        """
        raise NotImplementedError('use should be overloaded in Item\'s child')


class PotionTypeItem(Item):
    """
    Single-use items that affect whoever uses them and vanishes.
    When creating object, it should be supplied with the Effect class instance that
    can affect Actor class.
    """
    def __init__(self, effect=lambda a: None, **kwargs):
        super(PotionTypeItem, self).__init__(**kwargs)
        self.effect = effect

    def use(self, target=None):
        """
        Spend this item: apply effect, remove it from inventory and send a message to game log
        Returns True if using item was possible (not necessary successful!)
        :param target: type depends on Effect class and may be Actor, location or whatever else subclass supports
        :return:
        """
        self.owner.actor.map.extend_log('{0} used {1}'.format(self.owner.actor.descriptor.name,
                                                              self.name))
        if isinstance(self.effect, FighterTargetedEffect):
            if not target:
                r = self.effect.affect(self.owner.actor)
            else:
                r = self.effect.affect(target)
        elif isinstance(self.effect, TileTargetedEffect):
            if not target:
                if not self.effect.require_targeting:
                    r = self.effect.affect(self.owner.actor.map, self.owner.actor.location)
                else:
                    self.owner.actor.map.extend_log('Better not to blow yourself up. Use [F]ire command.')
                    r = False
            else:
                if self.event_type:
                    self.owner.actor.map.game_events.append(GameEvent(event_type=self.event_type,
                                                                      actor=self.owner.actor,
                                                                      location=target))
                r = self.effect.affect(self.owner.actor.map, target)
        #  Log usage and return result
        if r:
            self.owner.remove(self)
            return True
        else:
            return False

