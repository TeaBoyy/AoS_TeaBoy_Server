"""
Tug of War game mode, where you must progressively capture the enemy CPs in a 
straight line to win.

Maintainer: mat^2
"""

from pyspades.constants import *
from pyspades.server import Territory
import random
import math
from math import pi

from pyspades.loaders import Loader
from pyspades.packet import load_client_packet
from pyspades.bytes import ByteReader, ByteWriter

# TODO:
from pyspades.server import block_action
from commands import add, admin, name
from twisted.internet.task import LoopingCall

from pyspades.common import decode

class VersionResponse(Loader):
    id = 34
    
    client = str()
    version = tuple()
    os_info = str() 

    def read(self, reader):
        magic_no = reader.readByte(True)
        self.client = chr(magic_no)
        self.version = (
            reader.readByte(True),
            reader.readByte(True),
            reader.readByte(True),
        )
        self.os_info = decode(reader.readString())
    
    def write(self, writer):
        writer.writeByte(self.id, True)



        
class HandShakeInit(Loader):
    id = 31

    def read(self, reader):
        pass

    def write(self, writer):
        writer.writeByte(self.id, True)
        writer.writeInt(42, True)

class HandShakeReturn(Loader):
    id = 32

    def read(self, reader):
        self.success = int(reader.readInt(True) == 42)

    def write(self, writer):
        writer.writeByte(self.id, True)


        
class VersionRequest(Loader):
    id = 33

    def read(self, reader):
        pass

    def write(self, writer):
        writer.writeByte(self.id, True)


from pyspades import contained

CONTAINED_LIST = [
    contained.PositionData,
    contained.OrientationData,
    contained.WorldUpdate,
    contained.InputData,
    contained.WeaponInput,
    contained.HitPacket,
    contained.GrenadePacket,
    contained.SetTool,
    contained.SetColor,
    contained.ExistingPlayer,
    contained.ShortPlayerData,
    contained.MoveObject,
    contained.CreatePlayer,
    contained.BlockAction,
    contained.BlockLine,
    contained.StateData,
    contained.KillAction,
    contained.ChatMessage,
    contained.MapStart,
    contained.MapChunk,
    contained.PlayerLeft,
    contained.TerritoryCapture,
    contained.ProgressBar,
    contained.IntelCapture,
    contained.IntelPickup,
    contained.IntelDrop,
    contained.Restock,
    contained.FogColor,
    contained.WeaponReload,
    contained.ChangeTeam,
    contained.ChangeWeapon,
    # TODO: NEW
    HandShakeInit,
    HandShakeReturn,
    VersionRequest,
    VersionResponse
]

CONTAINED_LOADERS = {}

for item in CONTAINED_LIST:
    CONTAINED_LOADERS[item.id] = item

CLIENT_LOADERS = CONTAINED_LOADERS.copy()
for item in (contained.HitPacket,):
    CLIENT_LOADERS[item.id] = item

CP_COUNT = 6
CP_EXTRA_COUNT = CP_COUNT + 2 # PLUS last 'spawn'
ANGLE = 65
START_ANGLE = math.radians(-ANGLE)
END_ANGLE = math.radians(ANGLE)
DELTA_ANGLE = math.radians(30)
FIX_ANGLE = math.radians(4)

HELP = [
    "In Tug of War, you capture your opponents' front CP to advance."
]

class TugTerritory(Territory):
    disabled = True
    
    def add_player(self, player):
        if self.disabled:
            return
        Territory.add_player(self, player)
    
    def enable(self):
        self.disabled = False
    
    def disable(self):
        for player in self.players.copy():
            self.remove_player(player)
        self.disabled = True
        self.progress = float(self.team.id)

def get_index(value):
    if value < 0:
        raise IndexError()
    return value

def random_up_down(value):
    value /= 2
    return random.uniform(-value, value)

def limit_angle(value):
    return min(END_ANGLE, max(START_ANGLE, value))

def limit_dimension(value):
    return min(511, max(0, value))

def get_point(x, y, magnitude, angle):
    return (limit_dimension(x + math.cos(angle) * magnitude),
            limit_dimension(y + math.sin(angle) * magnitude))


@admin
def launch_box(connection, value = None):
    print("Entering command")
    try:
        connection.try_move_box()
    except Exception as ex:
        print("Ex: ", ex)

add(launch_box)

def apply_script(protocol, connection, config):
    class TugConnection(connection):
        def get_spawn_location(self):
            if self.team.spawn_cp is None:
                base = self.team.last_spawn
            else:
                base = self.team.spawn_cp
            return base.get_spawn_location()
            
        def on_spawn(self, pos):
            for line in HELP:
                self.send_chat(line)
            ret = connection.on_spawn(self, pos)

            # TODO:
            #if not "B" in self.name:
            if True:
                self.try_move_box()
            return ret

        def spawn(self, pos = None):
            print("spawn")

            #self.protocol.send_contained(HandShakeInit())
            #self.protocol.send_contained(HandShakeReturn())

            #version_request_packet = VersionRequest()
            #self.protocol.send_contained(version_request_packet)

            if False:
                if "B" in self.name:
                    print("Bot, don't deal with version")
                else:
                    print("Request version")
                    self.protocol.send_contained(VersionRequest())

            return connection.spawn(self, pos)

        
        def test_load_client_packet(self, data):
            return self.load_contained_packet(data, CLIENT_LOADERS)

        def test_load_contained_packet(self, data, table):
            type = data.readByte(True)
            return table[type](data)

        def test_loader_received(self, loader):
            contained = self.load_client_packet(ByteReader(loader.data))
            if contained.id == 34 or contained.id == 33 or contained.id == 32 or contained.id == 31:
                print ("Special contained.id is: ", contained.id)
                if contained.id == VersionResponse.id:
                    print("self.name: ", self.name, ", contained.client: ", contained.client)
            else:
                print("Test ignore")
                return connection.loader_received(self, loader)
            return
            print("TEST loader_received")
            #if self.player_id is not None:
            contained = load_client_packet(ByteReader(loader.data))
            #print("contained.id: ", contained.id)
            
            #if contained.id != VersionResponse.id:
            if contained.id == 34 or contained.id == 33 or contained.id == 32 or contained.id == 31:
                print ("Special contained.id is: ", contained.id)
                return connection.loader_received(self, loader)

            #print("contained.client: ", contained.client)

            # TODO: maybe only return if did nothing?
            return connection.loader_received(self, loader)

        def on_connect(self):
            print("on_connect")

            if False:
                self.protocol.send_contained(HandShakeInit())
                self.protocol.send_contained(HandShakeReturn())

                version_request_packet = VersionRequest()
                self.protocol.send_contained(version_request_packet)

            return connection.on_connect(self)

        # TODO:
        box_loop = None
        box_loop_interval = 0.05 # Seconds
        box_pos = None

        def change_block(self, x, y, z, action):
            block_action.x = x 
            block_action.y = y 
            block_action.z = z 
            block_action.player_id = 32
            block_action.value = action
            return self.protocol.send_contained(block_action, save = True) 

        #def place_block(self, x, y, z, action):
        #    self.change_block(x, y, z, BUILD_BLOCK)

        def iterate_box(self, x, y, z, action):
            box_size = 3
            for dx in range(0, box_size):
                for dy in range(0, box_size):
                    for dz in range(0, box_size):
                        self.change_block(x + dx, y + dy, z + dz, action)

        def destroy_box(self, x, y, z):
            self.iterate_box(x, y, z, DESTROY_BLOCK)

        def create_box(self, x, y, z):
            self.iterate_box(x, y, z, BUILD_BLOCK)

        def box_loop_call(self):
            if self.box_pos != None:
                x, y, z = self.box_pos
                offset = 3*3
                if x <= 0 + offset or x >= 512 - offset or y <= 0 + offset or y >= 512  - offset or z <= 0 + offset or z >=63 - offset:
                    print("Out of bounds, don't spawn box. Stop loop")
                    self.box_loop.stop()
                    self.box_loop = None
                    return


            print("Creating the box")

            if self.box_pos != None:
                self.destroy_box(*self.box_pos)

            if self.box_pos == None:
                player_pos = self.world_object.position.copy()
                self.box_pos = (player_pos.x + 5, player_pos.y + 5, player_pos.z - 5)
            else:
                x, y, z = self.box_pos
                self.box_pos = (x + 1, y, z)

            self.create_box(*self.box_pos)

            x, y, z = self.box_pos

            self.set_location((x, y, self.protocol.map.get_z(x, y)))

        # TOOD:
        def try_move_box(self):
            if self.box_loop != None and self.box_loop.running:
                self.box_loop.stop()
                self.box_pos = None
                print("Stopped loop")

            self.box_loop = LoopingCall(self.box_loop_call)
            self.box_loop.start(self.box_loop_interval)
            print("Started loop")
            
    class TugProtocol(protocol):
        game_mode = TC_MODE
        
        def get_cp_entities(self):
            # generate positions
            
            map = self.map
            blue_cp = []
            green_cp = []

            magnitude = 10
            angle = random.uniform(START_ANGLE, END_ANGLE)
            x, y = (0, random.randrange(64, 512 - 64))
            
            points = []
            
            square_1 = xrange(128)
            square_2 = xrange(512 - 128, 512)
            
            while 1:
                top = int(y) in square_1
                bottom = int(y) in square_2
                if top:
                    angle = limit_angle(angle + FIX_ANGLE)
                elif bottom:
                    angle = limit_angle(angle - FIX_ANGLE)
                else:
                    angle = limit_angle(angle + random_up_down(DELTA_ANGLE))
                magnitude += random_up_down(2)
                magnitude = min(15, max(5, magnitude))
                x2, y2 = get_point(x, y, magnitude, angle)
                if x2 >= 511:
                    break
                x, y = x2, y2
                points.append((int(x), int(y)))
            
            move = 512 / CP_EXTRA_COUNT
            offset = move / 2
            
            for i in xrange(CP_EXTRA_COUNT):
                index = 0
                while 1:
                    p_x, p_y = points[index]
                    index += 1
                    if p_x >= offset:
                        break
                if i < CP_EXTRA_COUNT / 2:
                    blue_cp.append((p_x, p_y))
                else:
                    green_cp.append((p_x, p_y))
                offset += move
            
            # make entities
            
            index = 0
            entities = []
            
            for i, (x, y) in enumerate(blue_cp):
                entity = TugTerritory(index, self, *(x, y, map.get_z(x, y)))
                entity.team = self.blue_team
                if i == 0:
                    self.blue_team.last_spawn = entity
                    entity.id = -1
                else:
                    entities.append(entity)
                    index += 1
            
            self.blue_team.cp = entities[-1]
            self.blue_team.cp.disabled = False
            self.blue_team.spawn_cp = entities[-2]
                
            for i, (x, y) in enumerate(green_cp):
                entity = TugTerritory(index, self, *(x, y, map.get_z(x, y)))
                entity.team = self.green_team
                if i == len(green_cp) - 1:
                    self.green_team.last_spawn = entity
                    entity.id = index
                else:
                    entities.append(entity)
                    index += 1

            self.green_team.cp = entities[-CP_COUNT/2]
            self.green_team.cp.disabled = False
            self.green_team.spawn_cp = entities[-CP_COUNT/2 + 1]
            
            return entities
    
        def on_cp_capture(self, territory):
            team = territory.team
            if team.id:
                move = -1
            else:
                move = 1
            for team in [self.blue_team, self.green_team]:
                try:
                    team.cp = self.entities[get_index(team.cp.id + move)]
                    team.cp.enable()
                except IndexError:
                    pass
                try:
                    team.spawn_cp = self.entities[get_index(
                        team.spawn_cp.id + move)]
                except IndexError:
                    team.spawn_cp = team.last_spawn
            cp = (self.blue_team.cp, self.green_team.cp)
            for entity in self.entities:
                if not entity.disabled and entity not in cp:
                    entity.disable()

    return TugProtocol, TugConnection
