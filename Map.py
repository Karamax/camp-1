#  Map and tile classes.
#  These contain only the information about things in game and some gameplay logic, so they don't inherit from
#  any of Kivy classes. MVC and all that.

class MapItem(object):
    """
    Base class from which all items that can be placed on map should inherit
    """
    pass

class GroundTile(MapItem):
    def __init__(self, passable=True, image_source='Tmp_frame.png', **kwargs):
        super(GroundTile, self).__init__(**kwargs)
        self.passable=passable
        self.image_source = image_source
        #  Widget should be defined when a tile is added to the RLMapWidget using TileWidgetFactory
        self.widget = None

class Actor(MapItem):
    def __init__(self, player=False, **kwargs):
        super(Actor, self).__init__(**kwargs)
        #  Set to true if this is a player-controlled actor
        self.player=player
        if self.player:
            #  Last command sent to player-controlled Actor
            self.last_command=None
        #  Here will be data re: map location (in tiles, not pixels)
        #  This is not set by constructor
        self.map = None
        self.location=[]


    def connect_to_map(self, map=None, location=(None, None)):
        """
        Remember that this actor was placed to a given map and a given location
        :param map: RLMap
        :param location: tuple
        :return:
        """
        self.map = map
        #  Cast the type: location attribute was a tuple
        self.location = list(location)

    def pass_command(self, keycode):
        """
        Pass the last key that was pressed. This method is intended to be called before make_turn() for
        a player-controlled Actor, so that the Actor will do whatever player wants instead of making its
        own decisions.
        :param keycode: kivy keycode tuple
        :return:
        """
        if not self.player:
            raise NotImplementedError('Commands to non-player Actors are not implemented')
        self.last_command=keycode

    def make_turn(self):
        """
        Make turn: move, attack or something
        :return:
        """
        if not self.player:
            #  Placeholder action for non-player Actor
            self.location[0] += 1
        else:
            #  Movement for a player actor
            if self.last_command[1] == 'w':
                self.location[1] += 1
            elif self.last_command[1] == 's':
                self.location[1] -= 1
            elif self.last_command[1] == 'a':
                self.location[0] -= 1
            elif self.last_command[1] == 'd':
                self.location[0] += 1
            self.last_command = None


class RLMap(object):
    def __init__(self, size=(10, 10), layers = ['default']):
        self.size=size
        #  Initializing tiles container
        self.tiles ={l: [[None for x in range(size[1])] for y in range(size[0])] for l in layers}
        #  Actors list
        self.actors = []

    #  Actions on map items: addition, removal and so on

    def move_item(self, layer='default', old_location=(0, 0), new_location=(1, 1)):
        """
        Move the map item to a new location. Place None in its old position.
        :param layer: Layer in which the moved object is (str)
        :param old_location: Where to take item from (2-int tuple)
        :param new_location: Where to place the item (2-int tuple)
        :return:
        """
        moved_item=self.get_item(layer=layer, location=old_location)
        # moved_item.widget.pos=(new_location[0]*50, new_location[1]*50)
        self.tiles[layer][new_location[0]][new_location[1]] = moved_item
        self.delete_item(layer=layer, location=old_location)

    def get_item(self, layer='default', location=(0, 0)):
        """
        Return the map item on a given layer and location.
        :param layer:
        :param location:
        :return:
        """
        return self.tiles[layer][location[0]][location[1]]

    def add_item(self, item=None, layer='default', location=(0, 0)):
        """
        Add the map item at the given layer and location.
        :param item:
        :param layer:
        :param location:
        :return:
        """
        self.tiles[layer][location[0]][location[1]] = item
        if type(item) is Actor:
            self.actors.append(item)
            item.connect_to_map(map=self, location=location)

    def has_item(self, layer='default', location=(None, None)):
        """
        Return True if there is anything at the given layer and location.
        :param layer:
        :param location:
        :return:
        """
        if self.tiles[layer][location[0]][location[1]] is not None:
            return True
        else:
            return False

    def delete_item(self, layer='default', location=(None,None)):
        """
        Remove whatever is at the given layer and location.
        :param layer:
        :param location:
        :return:
        """
        self.tile[layer][location[0]][location[1]] = None

    #  Game-related actions

    def process_turn(self, keycode):
        """
        Perform a turn. This procedure is called when player character makes a turn; later I might
        implement a more complex time system.
        :param keycode: kivy keycode tuple
        :return:
        """
        for actor in self.actors:
            if actor.player:
                actor.pass_command(keycode)
            actor.make_turn()