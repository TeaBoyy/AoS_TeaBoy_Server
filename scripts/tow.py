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

def apply_script(protocol, connection, config):
    class TugConnection(connection):
        def get_spawn_location(self):
            if self.team.spawn_cp is None:
                base = self.team.last_spawn
            else:
                base = self.team.spawn_cp
            return base.get_spawn_location()
            
        # TODO: reset on game end and stuff
        last_spawn_time = None
        cooldown_time = None
        times_spawned = 0
        def on_spawn(self, pos):
            for line in HELP:
                self.send_chat(line)

            current_time = reactor.seconds()

            alive_cooldown = 75
            if self.last_spawn_time != None and current_time > self.last_spawn_time and current_time - self.last_spawn_time > alive_cooldown:
                #self.times_spawned = 0
                print("[HEY] It's been " + str(alive_cooldown) + "s of alive, drop by 1s")
                if self.times_spawned >= 1:
                    self.times_spawned -= 1

            if self.cooldown_time != None and current_time > self.cooldown_time and self.cooldown_time - self.cooldown_time > 60 * 5:
                # Try drop after 5 mins regardless of how long player lived last time
                self.cooldown_time = current_time
                print("[HEY] It's been 5mins in total, drop by 1s")
                if self.times_spawned >= 1:
                    self.times_spawned -= 1

            if self.times_spawned == 0:
                self.cooldown_time = current_time

            self.last_spawn_time = current_time



            final_respawn_time = int(min(5 + self.times_spawned * 1.5, 16))
            random_offset = random.randrange(-3, 3)
            if random_offset < 0 and final_respawn_time < random_offset * -1:
                random_offset = 0

            final_respawn_time += random_offset

            self.respawn_time = final_respawn_time + random.randrange(-2, 2)
            print("my respawn_time -> ", self.respawn_time)

            self.times_spawned += 1

            if self.times_spawned > 16 / 1.5:
                self.times_spawned = 16 / 1.5
            
            return connection.on_spawn(self, pos)

        # TODO: ok so config 10s resapwn + no waves works not too bad. But now seems like its getting empties faster.
        # TODO: likely need own wave system, to just over time decrease reinforcements. After taking objective, reset spawn timer for team that lost it i guess?
        # TODO: goal is to make it challanging but eventually possible to clear and take tent.
        # TODO: really, just waves after waves should decrease amount of incoming reinforncements, it's like reducing 9vs9 to 3vs3 or so

        # TODO: ok i guess bug with leaked capturers exists still. Maybe my home bases stuff. Maybe not. Clearly blue got it and surround it, but smh invisble green took it for a bit

        # TODO:
        #def on_kill(self, killer, type, grenade):
        #    self.respawn_time = 15 # TODO: maybe if just bots take longer to respawn, it would be better
        #    # TODO: at 30s respawn seems like its much calmer with 18 bots
        #    return connection.on_kill(self, killer, type, grenade)
            
    # TOOD: in general looks like coold idea. Diagonal pattern, TOW, balanced respawn time, Rifle only, maybe mines.
    # TODO: encourages to build fortifications and mines to protect agains other team, yet trying to push themselves

    class TugProtocol(protocol):
        game_mode = TC_MODE
        # TODO: careful on edge of maps can be stuff floaiting in sky. UPD - for green on cowang it still can spawn on that square, so shrink somehow
        # TODO: maybe like decrease distance for last points? Accelerating? Idk
        def get_cp_entities(self):
            # generate positions
            
            map = self.map
            blue_cp = []
            green_cp = []

            magnitude = 10
            #angle = random.uniform(START_ANGLE, END_ANGLE)
            angle = START_ANGLE

            #x, y = (0, random.randrange(64, 512 - 64))
            x, y = (0, 128)
            
            points = []


            # TODO: maybe just generate 6 positions in a line, just shift y for each to get diagonal
            
            # TODO: this is pretty good diagonal. But might add some X to have them further apart. Or reduce amount of tents
            #x, y = (32, 32)
            #for i in range(CP_EXTRA_COUNT):
            #    points.append((int(x), int(y)))
            #    x += 64
            #    y += 64
            #    print("added")

            # TODO: interesting but too far now
            #x, y = (32, 32)
            #for i in range(CP_EXTRA_COUNT):
            #    points.append((int(x), int(y)))
            #    x += 96
            #    y += 96
            #    print("added")


            # TODO:
            #extra_offset = -4
            #x, y = (32 - extra_offset * 2, 32 - extra_offset * 2)

            # TODO: hardcode matches 46 from start, and 46 at end
            x, y = (46, 46)

            for i in range(CP_EXTRA_COUNT):
                points.append((int(x), int(y)))
                print("added point: x -> ", x, ", y -> ", y)
                x += 60 
                y += 60
                
            square_1 = xrange(128)
            square_2 = xrange(512 - 128, 512)
            
            # TODO:
            while False:
                top = int(y) in square_1
                bottom = int(y) in square_2
                if top:
                    angle = limit_angle(angle + FIX_ANGLE)
                elif bottom:
                    angle = limit_angle(angle - FIX_ANGLE)
                else:
                    #diff = random_up_down(DELTA_ANGLE)
                    diff = DELTA_ANGLE
                    angle = limit_angle(angle + diff)

                #magnitude += random_up_down(2)
                magnitude += 2

                magnitude = min(15, max(5, magnitude))
                x2, y2 = get_point(x, y, magnitude, angle)
                if x2 >= 511:
                    break
                x, y = x2, y2
                points.append((int(x), int(y)))
            
            #move = 512 / CP_EXTRA_COUNT
            #offset = move / 2
            
            for i in xrange(CP_EXTRA_COUNT):
                
                #index = 0
                #while 1:
                #    print("index: " + str(index))
                #    p_x, p_y = points[index]
                #    index += 1
                #    if p_x >= offset:
                #        break
                p_x, p_y = points[i]
                if i < CP_EXTRA_COUNT / 2:
                    blue_cp.append((p_x, p_y))
                    print("tent spawn - blue")
                else:
                    green_cp.append((p_x, p_y))
                    print("tent spawn - green")
                #offset += move
                #index += 1
            
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
                    # TODO:
                    #if i % 2 == 0:
                    #    continue
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
                    # TODO:
                    #if i % 2 == 0:
                    #    continue

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
