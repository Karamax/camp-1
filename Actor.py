"""
Actor classes.
"""

from Controller import Controller, PlayerController, AIController
from MapItem import MapItem

class FighterComponent(object):
    """
    The component that provides the actor with combat capabilities
    """
    def __init__(self, hp=5, damage=3):
        self.hp = hp
        self.damage = damage

class Actor(MapItem):
    def __init__(self, player=False, name='Unnamed actor',
                 controller=None, fighter=None, **kwargs):
        #  Actors should be impassable by default. The 'passable' should be in kwargs to be passed to
        #  superclass constructor, so a simple default value in signature won't work here
        if 'passable' not in kwargs.keys():
            kwargs.update({'passable': False})
        super(Actor, self).__init__(**kwargs)
        #  Set to true if this is a player-controlled actor
        self.player = player
        self.attach_controller(controller)
        self.fighter = fighter
        self.name = name
        #  Here will be data that not set by constructor: it is only defined when map factory
        # places the actor on the map
        self.map = None
        self.location = []

    def connect_to_map(self, map=None, layer=None, location=(None, None)):
        """
        Remember that this actor was placed to a given map and a given location
        :param map: RLMap
        :param location: tuple
        :return:
        """
        self.map = map
        self.layer = layer
        #  Cast the type: location attribute was a tuple
        self.location = list(location)

    def attach_controller(self, controller):
        """
        Attach a controller to the Actor
        :param controller: Controller
        :return:
        """
        assert isinstance(controller, Controller)
        self.controller = controller
        self.controller.actor = self

    def pass_command(self, keycode):
        """
        Pass the last key that was pressed. This method is intended to be called before make_turn() for
        a player-controlled Actor, so that the Actor will do whatever player wants instead of making its
        own decisions.
        :param keycode: kivy keycode tuple
        :return:
        """
        try:
            self.controller.take_keycode(keycode)
        except AttributeError:
            raise NotImplementedError('Commands to non-player Actors are not implemented')

    def make_turn(self):
        """
        Make turn: move, attack or something. If an actor has player=True, it respects self.last_command.
        Otherwise this method makes the decision and calls the appropriate method to perform it.
        Returns True if this actor has managed to do something
        :return: bool
        """
        #  Prevent dead actors from making turns. If I'm correct, they act just because GC doesn't get to them
        #  quickly enough to prevent that. If, on the other hand, I've missed an Actor reference somewhere,
        #  this is a potential memory leak
        if self.fighter and self.fighter.hp <= 0:
            return False
        return self.controller.call_actor_method()
        # if self.player:
        #     return self.controller.call_actor_method()
        # else:
        #     return self.controller.call_actor_method()

    def move(self, location=(None, None)):
        """
        Move self to a location. Returns True after a successful movement
        and False if it turns out to be impossible. Movement is considered successful if
        collision occured even if the actor didn't actually move.
        :param location: tuple
        :return: bool
        """
        # Passability should be detected before collision. In general these two concepts are unrelated
        # but collision may change passability. In that case actor should enter the tile only on the next
        # turn, having wasted current one on cleaning the obstacle or killing enemy
        passability = self.map.entrance_possible(location)
        # Check if collision has occured
        collision_occured = False
        try:
            for item in self.map.get_column(location):
                if type(item) is Actor:
                    #  No need to collide with tiles or something
                    if item.collide(self):
                        collision_occured = True
        except IndexError:
            #  Attempts to collide with something outside map boundaries are silently ignored
            pass
        moved = False
        if passability:
            self.map.move_item(layer=self.layer,
                               old_location=self.location,
                               new_location=location)
            self.location = location
            moved = True
            self.widget.last_move_animated = False
        return moved or collision_occured

    def pause(self):
        """
        Spend one turn doing nothing. Return True if it was possible, False otherwise
        :return:
        """
        return True

    def collide(self, other):
        """ Collision callback: get bumped into by some other actor.
        :param other: Actor
        :return:
        """
        if self.fighter and other.fighter:
            self.fighter.hp -= other.fighter.damage
            self.map.game_log.append('{1} hit {0} for {2} damage'.format(self.name,
                                                                                other.name,
                                                                                self.fighter.damage))
            if self.fighter.hp <= 0:
                self.map.game_log.append('{} was killed'.format(self.name))
                self.map.delete_item(layer='actors', location=self.location)
            return True
        else:
            #  Teleporting non-fighter Actors instead of fighting
            if self.map.entrance_possible((1, 1)):
                self.map.game_log.append('{0} successfully teleported by {1}'.format(self.name,
                                                                                       other.name))
                #  Cannot just return True here because the item needs to be actually moved
                return self.move(location=(1, 1))
            else:
                #  Collision did happen, but teleportation turned out to be impossible
                self.map.game_log.append('{1} attempted to teleport {0}, but failed'.format(self.name,
                                                                                              other.name))
                return True