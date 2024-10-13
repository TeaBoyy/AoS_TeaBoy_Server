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

from twisted.internet import reactor

# TODO:
#CP_COUNT = 6
CP_COUNT = 6
#CP_COUNT = 7

CP_EXTRA_COUNT = CP_COUNT + 2 # PLUS last 'spawn'

#ANGLE = 65
ANGLE = 0

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
            # TODO: spams every second
            # TODO: can actually use update_rate, and just keep proxy list of players, use it but assign to real player list for base class only when enabled
            # TODO: yet better to leave this logic alone, and proly just store last pair of tent&time on connection/player and check against it
            # TODO: this way no need to test and no need to worry, and less changes to the original
            #print("DISABLED")
            return

        # TODO: do something to not start with 0.5 progress
        #if self.team == None:
        #    self.progress = float(player.team.other.id)

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

def apply_script(protocol, connection, config):
    class TugConnection(connection):
        def get_spawn_location(self):
            if self.team.spawn_cp is None:
                base = self.team.last_spawn
            else:
                base = self.team.spawn_cp
            # TODO:
            location = base.get_spawn_location()

            #random_offset = random.choice((-64, -32, 0, 32, 64))
            #random_offset = random.choice((-64, 0, 64))
            #random_offset = random.choice((-96, -64, -32, 0, 32, 64, 96))

            offsets = [0, -32, 32, -64, 64, -96, 96]

            random_offset = None

            if self.team == self.protocol.blue_team:
                random_offset = offsets[self.protocol.spawn_location_counter_blue]

                if self.protocol.spawn_location_counter_blue >= len(offsets) - 1:
                    self.protocol.spawn_location_counter_blue = 0
                else:  
                    self.protocol.spawn_location_counter_blue += 1
            else:
                random_offset = offsets[self.protocol.spawn_location_counter_green]

                if self.protocol.spawn_location_counter_green >= len(offsets) - 1:
                    self.protocol.spawn_location_counter_green = 0
                else:  
                    self.protocol.spawn_location_counter_green += 1

            x, y, _ = location
            y += random_offset

            location = (x, y, self.protocol.map.get_z(x, y))
            return location
            
        def on_spawn(self, pos):
            for line in HELP:
                self.send_chat(line)
            return connection.on_spawn(self, pos)
            
    class TugProtocol(protocol):
        game_mode = TC_MODE

        on_cp_finalize_call = None

        # TODO:
        spawn_location_counter_blue = 0
        spawn_location_counter_green = 0

        def generate_spawn_points(self, world_size, N, M, K):
            points = []
            center = world_size // 2
            step = int((world_size - 2 * M) / (N - 1))  # Calculate the step based on the world size and number of points

            # Generate points along the diagonal with the offset K
            for i in range(N):
                x = M + i * step + (i - N // 2) * K  # Apply custom offset K relative to the center
                y = x  # For diagonal, x == y

                # Ensure points stay within bounds
                if 0 <= x < world_size and 0 <= y < world_size:
                    points.append((x, y))

            return points
        
        def get_cp_entities(self):
            # TODO:
            """
            points = self.generate_spawn_points(512, CP_EXTRA_COUNT, 32, 0)

            entities = []

            for i in range(len(points)):
                if i < CP_EXTRA_COUNT / 2:
                    x, y = points[i]
                    entity = TugTerritory(i, self, *(x, y, map.get_z(x, y)))
                    entity.team = self.green_team
                    entities.append(entity)

            return entities
            """

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
            
            # TODO:
            # while 1:
            while False:
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

            # TODO:
            # TODO: test neutral one
            points = self.generate_spawn_points(512, CP_EXTRA_COUNT, 32, 0)
            print("len(points): ", len(points))
            for x, y in points:
                print("x: ", x, ", y: ", y)
            
            move = 512 / CP_EXTRA_COUNT
            offset = move / 2
            
            # TODO: 
            #neutral_cp = []

            for i in xrange(len(points)):
                #index = 0
                #while 1:
                #    p_x, p_y = points[index]
                #    index += 1
                #    if p_x >= offset:
                #        break
                p_x, p_y = points[i]

                # TODO:
                p_y = 256

                if i < CP_EXTRA_COUNT / 2:
                    blue_cp.append((p_x, p_y))
                    print("Blue point added - x: ", p_x, ", y: ", p_y)
                #elif i > CP_EXTRA_COUNT / 2:
                else:
                    green_cp.append((p_x, p_y))
                    print("Green point added - x: ", p_x, ", y: ", p_y)
                #else:
                #    print("Neutral one")
                #    neutral_cp.append((p_x, p_y))
                #offset += move
            
            # make entities
            
            index = 0
            entities = []
            
            for i, (x, y) in enumerate(blue_cp):
                entity = TugTerritory(index, self, *(x, y, map.get_z(x, y)))
                entity.team = self.blue_team
                if i == 0:
                    self.blue_team.last_spawn = entity
                    entity.id = -1
                    print("Blue last spawn set")
                else:
                    entities.append(entity)
                    index += 1
            
            self.blue_team.cp = entities[-1]
            self.blue_team.cp.disabled = False
            #self.blue_team.cp.disabled = True

            # TODO:
            #self.blue_team.spawn_cp = entities[-2]
            self.blue_team.spawn_cp = entities[-3]
                
            for i, (x, y) in enumerate(green_cp):
                entity = TugTerritory(index, self, *(x, y, map.get_z(x, y)))
                entity.team = self.green_team
                if i == len(green_cp) - 1:
                    self.green_team.last_spawn = entity
                    entity.id = index
                    print("Green last spawn set")
                else:
                    entities.append(entity)
                    index += 1

            self.green_team.cp = entities[-CP_COUNT/2]
            self.green_team.cp.disabled = False
            #self.green_team.cp.disabled = True

            # TODO:
            #self.green_team.spawn_cp = entities[-CP_COUNT/2 + 1]
            self.green_team.spawn_cp = entities[-CP_COUNT/2 + 2]

            """
            # TODO:
            for i, (x, y) in enumerate(neutral_cp):
                entity = TugTerritory(index, self, *(x, y, map.get_z(x, y)))
                entity.team = None

                #entity.disabled = False
                entity.disabled = True

                #entity.progress = 0.5
                entities.append(entity)

                #entities[len(blue_cp) - 1].disabled = False
                entities[len(blue_cp) - 1].disabled = True

                #entities[len(blue_cp) - 1].progress = 0.5
                index += 1
            """
            
            return entities
    
        def on_cp_capture(self, territory):
            # TODO: try and send like its now neutral, not blue/green, with test delay to see if works
            #territory.team = None
            #territory.update()

            #return

            # TODO:
            return self.on_cp_finalize(territory)

            if self.on_cp_finalize_call != None:
                self.on_cp_finalize(territory, False)
                print("Defending team took the tent back! Back to normal!")
                return

            # TODO: read from config
            cooldown = 60

            print("Attacker team took the tent! They need to hold for ", cooldown, " seconds before they can advance further!")

            # Temporary disable all the tents except for the one needs to be secured by the attackers
            for entity in self.entities:
                if not entity.disabled and entity is not territory:
                    entity.disable()

            self.on_cp_finalize_call = reactor.callLater(cooldown, self.on_cp_finalize, territory)

        # TODO: probably when trying to cap disabled tents, let know what's going on
        # TODO: announce how much left every few seconds
        # TODO: and ideally print openspades/betterspades text on actual screen
        def on_cp_finalize(self, territory, is_secured = True):
            print("Attacker team secured the tent! Now they can advance further!")

            self.reset_cp_finalize_call()

            # Original tow code
            team = territory.team
            if team.id:
                # TODO:
                move = -1
                #move = -2
            else:
                # TODO:
                move = 1
                #move = 2

            if not is_secured:
                move = 0

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

        def reset_cp_finalize_call(self):
            print("self.reset_cp_finalize_call()")
            if self.on_cp_finalize_call != None:
                if self.on_cp_finalize_call.active():
                    self.on_cp_finalize_call.cancel()
                self.on_cp_finalize_call = None

        def on_map_change(self, map):
            print("on_map_change")
            self.reset_cp_finalize_call()
            protocol.on_map_change(self, map)
            
        def reset_tc(self):
            print("reset_tc")
            self.reset_cp_finalize_call()
            protocol.reset_tc(self)

    return TugProtocol, TugConnection
