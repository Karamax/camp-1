"""
Various factories, generating functions and other things.
Creates both Widgets and MapItems
"""

from kivy.uix.image import Image
from kivy.uix.widget import Widget

#  Importing my own stuff
from Map import RLMap
from MapItem import GroundTile, MapItem
from Actor import Actor
from Constructions import Construction, FighterConstruction, Spawner, Trap, ShooterConstruction
from Components import *
from Controller import PlayerController, MeleeAIController, FighterSpawnController,\
    ShooterSpawnController, RangedAIController
from Items import PotionTypeItem, Item, FighterTargetedEffect, TileTargetedEffect

#  Other imports
from random import choice, random


class ActorWidget(Widget):
    """
    The actor widget that contains an actor image
    """
    def __init__(self, source='PC.png', **kwargs):
        super(ActorWidget, self).__init__(**kwargs)
        self.img = Image(source=source, size=(32, 32), allow_stretch=True)
        self.add_widget(self.img)
        self.bind(pos=self.update_img)
        self.bind(size=self.update_img)
        # self.last_move_animated = True
        #  Flag that controls whether this widget is to be animated

    # def update_size(self, a, b):
    #     self.img.size=self.size

    def update_img(self, a, b):
        self.img.pos = self.pos
        self.img.size = self.size

    # def update_texture(self, size, pos):
    #     self.rect.size = self.size
    #     self.rect.pos = self.pos

class TileWidget(Widget):
    """
    The tile widget that currently contains only an image.
    """
    def __init__(self, source='PC.png', **kwargs):
        super(TileWidget, self).__init__(**kwargs)
        self.img = Image(source=source, size=(32, 32))
        self.add_widget(self.img)
        self.bind(pos=self.update_img)

    def update_img(self, a, b):
        self.img.pos = self.pos

    def update_texture(self, size, pos):
        self.rect.size = self.size
        self.rect.pos = self.pos

class ItemWidget(Widget):
    """
    Widget for an item. Used both for item on the ground and item in the inventory
    """
    def __init__(self, source='Bottle.png', **kwargs):
        super(ItemWidget, self).__init__(**kwargs)
        self.img = Image(source=source, size=(32, 32))
        self.add_widget(self.img)
        self.bind(pos=self.update_img)

    def update_img(self, a, b):
        self.img.pos = self.pos

class ConstructionWidget(Widget):
    """
    Widget for a construction
    """
    def __init__(self, source='DownStairs.png', **kwargs):
        super(ConstructionWidget, self).__init__(**kwargs)
        self.img = Image(source=source, size=(32, 32))
        self.add_widget(self.img)
        self.bind(pos=self.update_img)

    def update_img(self, a, b):
        self.img.pos = self.pos


class TileWidgetFactory(object):
    def __init__(self):
        # The dictionary that implements dispatching correct methods for any MapItem class
        self.type_methods = {GroundTile: self.create_tile_widget,
                             Actor: self.create_actor_widget,
                             Item: self.create_item_widget,
                             Construction: self.create_construction_widget}
        self.passable_tiles = ('Tile_passable.png', )

    def create_widget(self, item):
        """
        Create a MapItem widget.
        Calls the correct method of self depending on what the class of MapItem is
        :param item:
        :return:
        """
        assert isinstance(item, MapItem)
        for t in self.type_methods.keys():
            if isinstance(item, t):
                return self.type_methods[t](item)

    def create_tile_widget(self, tile):
        #  There is no true randomness now, because the tiles are simple white bg.
        #  When aesthetics get implemented, some floors, underground piping, etc. will be added
        s = choice(self.passable_tiles) if tile.passable else 'Tile_impassable.png'
        tile.widget = TileWidget(source=s, size=(32, 32),
                                 size_hint=(None, None))
        return tile.widget

    def create_actor_widget(self, actor):
        s = actor.image_source
        widget = ActorWidget(source=s, size=(32, 32),
                             size_hint=(None, None))
        actor.widget = widget
        return widget

    def create_item_widget(self, item):
        s = item.image_source
        item.widget = ItemWidget(source=s, size=(32, 32),
                                 size_hint=(None, None))
        return item.widget

    def create_construction_widget(self, constr):
        constr.widget = ConstructionWidget(source=constr.image_source, size=(32, 32),
                                           size_hint=(None, None))
        return constr.widget


class MapItemDepot():
    """
    A class that contains definitions of every item that can be placed on map during map generation.
    Every make_* method returns the instance of object in question.
    """

    def __init__(self):
        self.item_methods = [self.make_landmine,
                             self.make_bottle,
                             self.make_flag,
                             self.make_shooter_flag,
                             self.make_rocket,
                             self.make_ammo]
        self.glyph_methods = {'#': self.make_wall,
                              'S': self.make_spawner,
                              '^': self.make_mine,
                              'f': self.make_fighter,
                              'r': self.make_shooter,
                              '_': self.make_hole,
                              '@': self.make_pc,
                              'z': self.make_thug,
                              'g': self.make_gunner,
                              'R': self.make_rocket,
                              'L': self.make_landmine,
                              'B': self.make_bottle,
                              'F': self.make_flag,
                              '.': self.make_passable_tile,
                              '~': self.make_impassable_tile}

    #  Simple single-item methods
    @staticmethod
    def make_passable_tile():
        """
        A simple passable tile
        :return:
        """
        return GroundTile(passable=True, air_passable=True)

    @staticmethod
    def make_impassable_tile():
        """
        Impassable water tile
        :return:
        """
        return GroundTile(passable=False, air_passable=True)

    def make_pc(self):
        """
        Player character
        :return:
        """
        return Actor(image_source='PC.png',
                     controller=PlayerController(),
                     fighter=FighterComponent(max_hp=10),
                     inventory=InventoryComponent(volume=10, initial_items=self.get_all_items()),
                     faction=FactionComponent(faction='pc', enemies=['npc']),
                     descriptor=DescriptorComponent(name='PC', description='Player character'),
                     breath=BreathComponent())

    @staticmethod
    def make_wall():
        """
        Impassable wall
        :return:
        """
        return Construction(image_source='Tree.png', passable=False,
                            descriptor=DescriptorComponent(name='Tree'))

    @staticmethod
    def make_spawner():
        """
        Thug spawner
        :return:
        """
        return Spawner(image_source='DownStairs.png', spawn_frequency=3,
                       spawn_factory=ActorFactory(faction=FactionComponent(faction='npc',
                                                                           enemies=['pc'])),
                       faction=FactionComponent(faction='npc', enemies=['pc']),
                       descriptor=DescriptorComponent(name='A dark hole in the ground'),
                       fighter=FighterComponent(max_hp=10, defenses=[0,0]))

    @staticmethod
    def make_mine():
        """
        Landmine (the construction)
        :return:
        """
        return Trap(effect=TileTargetedEffect(effect_type='explode', effect_value=5),
                    image_source='Mined.png')

    @staticmethod
    def make_hole():
        """
        Explosion-produced hole
        :return:
        """
        return Construction(image_source='Hole.png', passable=False)

    @staticmethod
    def make_fighter():
        """
        Headless dude
        :return:
        """
        return FighterConstruction(image_source='MeleeTower.png', passable=False,
                                   fighter=FighterComponent(ammo=0, max_ammo=0),
                                   faction=FactionComponent(faction='pc', enemies=['npc']),
                                   descriptor=DescriptorComponent(name='Melee tower',
                                                                  description='This simple mechanism drops its heavy axe onto anything it considers an enemy.'),
                                   controller=FighterSpawnController())

    @staticmethod
    def make_shooter():
        """
        Shooty headless dude
        :return:
        """
        return ShooterConstruction(image_source='Shooter.png', passable=False,
                                   fighter=FighterComponent(ammo=10, max_ammo=10),
                                   faction=FactionComponent(faction='pc', enemies=['npc']),
                                   descriptor=DescriptorComponent(name='Shooter',
                                                                  description='This construction shoots your enemies. Swinging at their weak points with a hefty barrel also works surprisingly well.'),
                                   controller=ShooterSpawnController())

    def make_thug(self):
        """
        A regular thug
        :return:
        """
        return Actor(image_source='Chassis.png',
                     controller=MeleeAIController(),
                     fighter=FighterComponent(max_hp=3, ammo=0, max_ammo=0),
                     descriptor=DescriptorComponent(name='An empty chassis',
                                                    description='The chassis on which weapons or tools could be installed.'),
                     inventory=InventoryComponent(volume=1,
                                                  initial_items=[self.make_random_item()]),
                     faction=FactionComponent(faction='npc', enemies=['pc']))

    def make_gunner(self):
        """
        A thug that gets three shots but only 1 HP
        :return:
        """
        return Actor(image_source='GunnerChassis.png',
                     controller=RangedAIController(),
                     fighter=FighterComponent(max_hp=1, ammo=3, max_ammo=3),
                     descriptor=DescriptorComponent(name='Gunner',
                                                    description='A short-range gunner assembly.'),
                     inventory=InventoryComponent(volume=1,
                                                  initial_items=[self.make_random_item()]),
                     faction=FactionComponent(faction='npc', enemies=['pc']))

    @staticmethod
    def make_rocket():
        """
        Rocket
        :return:
        """
        return PotionTypeItem(descriptor=DescriptorComponent(name='Rocket',
                                                             description='Can and should be [F]ired at enemies'),
                              image_source='Rocket.png',
                              effect=TileTargetedEffect(effect_type='explode', effect_value=5,
                                                        require_targeting=True),
                              event_type='rocket_shot')

    def make_landmine(self):
        """
        Landmine (item)
        :return:
        """
        return PotionTypeItem(descriptor=DescriptorComponent(name='Landmine',
                                                             description='Places a landmine under the player'),
                              image_source='Landmine.png',
                              effect=TileTargetedEffect(effect_type='spawn_construction',
                                                        effect_value=self.make_mine()))
    @staticmethod
    def make_bottle():
        """
        Bottle
        :return:
        """
        return PotionTypeItem(descriptor=DescriptorComponent(name='Bottle',
                                                             description='Heals for 2 or 3 HP'),
                              image_source='Bottle.png',
                              effect=FighterTargetedEffect(effect_type='heal',
                                                           effect_value=[2, 3]))

    @staticmethod
    def make_ammo():
        """
        Restores 5 bullets
        :return:
        """
        return PotionTypeItem(descriptor=DescriptorComponent(name='Ammo',
                                                             description='Reloads bullets'),
                              effect=FighterTargetedEffect(effect_type='restore_ammo',
                                                           effect_value=5),
                              image_source='Ammo.png')

    def make_flag(self):
        """
        Spawning flag
        :return:
        """
        return PotionTypeItem(descriptor=DescriptorComponent(name='Spawning flag',
                                                             description='Builds a melee tower under the player'),
                              image_source='Flag.png',
                              effect=TileTargetedEffect(effect_type='spawn_construction',
                                                        effect_value=self.make_fighter()))

    def make_shooter_flag(self):
        """
        Shooter spawning flag
        :return:
        """
        return PotionTypeItem(descriptor=DescriptorComponent(name='Shooter flag',
                                                             description='Builds a shooter tower under the player'),
                              image_source='ShooterFlag.png',
                              effect=TileTargetedEffect(effect_type='spawn_construction',
                                                        effect_value=self.make_shooter()))

    #  Following methods generate items according to some rule

    def make_random_item(self):
        """
        Create a random item
        :return:
        """
        method = choice(self.item_methods)
        i = method()
        return i

    def get_all_items(self):
        """
        Return the list of all inventory items supported by this object
        :return:
        """
        r = []
        for method in self.item_methods:
            r.append(method())
        return r

    def get_item_by_glyph(self, glyph):
        """
        Return the item encoded by the glyph
        :param glyph:
        :return:
        """
        method = self.glyph_methods[glyph]
        item = method()
        return item


class MapLoader():
    """
    The map file interface. It takes a filehandle and returns a complete map. Everything it needs to do so is not
    the caller's problem.
    """
    def __init__(self):
        #  A dict of tag-to-function mappings. Values should be callables that accept string and return
        #  an object of a required type
        self.tag_converters = {'height': int,
                               'width': int,
                               'aesthetic': str,
                               'map_id': str,
                               'neighbour_south': str,
                               'neighbour_west': str,
                               'neighbour_east': str,
                               'neighbour_north': str,
                               'on_entrance': str}
        self.depot = MapItemDepot()
        self.layers = {'#': 'constructions',
                       '@': 'actors',
                       'S': 'constructions',
                       '^': 'constructions',
                       'f': 'constructions',
                       'r': 'constructions',
                       '_': 'constructions',
                       'z': 'actors',
                       'g': 'actors',
                       'R': 'items',
                       'L': 'items',
                       'B': 'items',
                       'F': 'items',
                       '.': 'bg',
                       '~': 'bg'}
        #  All the maps loaded from file will be stored here
        self.maps = {}

    def parse_tag_line(self, line):
        """
        Parse a tag line
        Convert the value to the required type (as per tag_types) and return (key, value) pair
        :param line:
        :return:
        """
        line = line.lstrip('/')
        a = line.split()
        if len(a) == 2:
            try:
                r = a[0], self.tag_converters[a[0]](a[1])
            except KeyError:
                raise ValueError('Unknown tag {0} in the map file'.format(a[0]))
        else:
            #  Tag values can contain spaces
            try:
                r = a[0], self.tag_converters[a[0]](' '.join(a[1:]))
            except KeyError:
                raise ValueError('Unknown tag {0} in the map file'.format(a[0]))
        return r

    def read_map_file(self, file):
        """
        Read a file that contains maps.
        :param handle: str
        :return:
        """
        tags = {}
        map_lines = []
        for line in open(file):
            if line[0] == '/':
                l = self.parse_tag_line(line)
                tags.update({l[0]: l[1]})
            elif line == '\n':
                #  Empty line means that one map ended and the next will maybe begin from the next line
                #  Anyway, time to compile the map
                map = RLMap(size=(tags['width'], tags['height']), layers=['bg', 'constructions', 'items', 'actors'])
                for y in range(0, tags['height']):
                    for x in range(0, tags['width']):
                        map.add_item(self.depot.make_passable_tile(),
                                     layer='bg', location=(x, tags['height']-1-y))
                        i = map_lines[y][x]
                        if i == '.':
                            #  Nothing to place here
                            continue
                        item = self.depot.get_item_by_glyph(i)
                        map.add_item(item=item,
                                     layer=self.layers[i],
                                     location=(x, tags['height']-1-y))
                #  Neighbouring map IDs
                for tag in [x for x in tags.keys() if 'neighbour_' in x]:
                    direction = tag.split('_')[1]
                    map.neighbour_maps[direction] = tags[tag]
                if 'on_entrance' in tags.keys():
                    map.entrance_message = tags['on_entrance']
                self.maps[tags['map_id']] = map
                print('Loaded map: {0}'.format(tags['map_id']))
                tags = {}
                map_lines = []
            else:
                map_lines.append(line)

    def get_map_by_id(self, map_id):
        """
        Return a map with a given ID.
        This method assumes that map-loading was done before it was called and that there is, in fact,
        such a map in the file
        :param map_id:
        :return:
        """
        return self.maps[map_id]

class ActorFactory(object):
    """
    Factory that produces Actors of a given faction
    """
    def __init__(self, faction):
        assert isinstance(faction, FactionComponent)
        self.faction = faction
        self.depot = MapItemDepot()

    def create_thug(self):
        """
        Creates a simple melee combatant. It has default FighterComponent
        and all the other components are (temporarily?) hardcoded
        :return:
        """
        if random() < 0.3:
            return self.depot.make_gunner()
        else:
            return self.depot.make_thug()
