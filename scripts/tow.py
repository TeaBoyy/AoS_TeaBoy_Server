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
from twisted.internet.task import LoopingCall

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

    def update_rate(self):
        rate = 0
        for player in self.players:
            if player.team.id:
                rate += 1
            else:
                rate -= 1
        progress = self.progress
        if ((progress == 1.0 and (rate > 0 or rate == 0)) or 
           (progress == 0.0 and (rate < 0 or rate == 0))):
            return

        # Modification - more than N players cannot speed up capturing
        rate = max(-4, min(rate, 4))

        self.rate = rate
        
        self.rate_value = rate * TC_CAPTURE_RATE

        # TODO: also reduce UI progress bar speed on client (add pauses to slow it down)
        # Modification - reduce capture speed
        rate_multiplier = 4
        self.rate_value /= rate_multiplier
        
        if self.finish_call is not None:
            self.finish_call.cancel()
            self.finish_call = None
        if rate != 0:
            self.start = reactor.seconds()
            rate_value = self.rate_value
            if rate_value < 0:
                self.capturing_team = self.protocol.blue_team
                end_time = progress / -rate_value
            else:
                self.capturing_team = self.protocol.green_team
                end_time = (1.0 - progress) / rate_value
            if self.capturing_team is not self.team:
                self.finish_call = reactor.callLater(end_time, self.finish)

        self.send_progress()
        
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

        def my_get_spawn_location(self, base):
            radius = 24

            x1 = max(0, base.x - radius)
            y1 = max(0, base.y - radius)
            x2 = min(512, base.x + radius)
            y2 = min(512, base.y + radius)
            return self.protocol.get_random_location(True, (x1, y1, x2, y2))

        def get_spawn_location(self):
            if self.team.spawn_cp is None:
                base = self.team.last_spawn
            else:
                base = self.team.spawn_cp
            location = self.my_get_spawn_location(base)
            spawn_point_offset = 48 + 16
            x, y, z = location
            # Shift by half the distance to equalize distance for both teams
            tents_distance_hardcode = 32 / 2
            attacker_offset = self.protocol.attacker_favor * tents_distance_hardcode
            if attacker_offset < 0:
                attacker_offset = -attacker_offset if self.team == self.protocol.blue_team else attacker_offset
            elif attacker_offset > 0:
                attacker_offset = attacker_offset if self.team != self.protocol.blue_team else -attacker_offset

            spawn_point_offset -= attacker_offset

            if self.team != self.protocol.blue_team:
                spawn_point_offset = -spawn_point_offset

            if self.protocol.round_just_started:
                spawn_point_offset = 0

            x -= spawn_point_offset
            y -= spawn_point_offset

            z = self.protocol.map.get_z(x, y)

            location = (x, y, z)
                
            return location
            
        def on_spawn(self, pos):
            for line in HELP:
                self.send_chat(line)
            return connection.on_spawn(self, pos)
            
    class TugProtocol(protocol):
        game_mode = TC_MODE

        progress_reporter_loop = None
        progress_reporter_loop_interval_seconds = 2.0

        def progress_reporter_check(self):
            attacker_favor = 0

            for tent in self.entities:
                if tent.disabled:
                    continue

                progress = tent.get_progress()
                team = tent.team

                attacker_favor += (progress > 0.5)*(1) if team == self.blue_team else (progress < 0.5)*(-1)
            self.attacker_favor = attacker_favor

            if self.attacker_favor != 0:
                print("self.attacker_favor: ", self.attacker_favor)

        round_just_started = False
        round_just_started_timeout = 10

        attacker_favor = 0
        def on_map_change(self, map):
            protocol.on_map_change(self, map)
            self.setup_round_just_started()
            self.progress_reporter_loop = LoopingCall(self.progress_reporter_check)
            self.progress_reporter_loop.start(self.progress_reporter_loop_interval_seconds)

        def setup_round_just_started(self):
            self.round_just_started = True

            if len(self.connections) <= 0:
                reactor.callLater(1.0, self.setup_round_just_started)
                print("[setup_round_just_started] Wait for more players to join")
                return
           
            reactor.callLater(self.round_just_started_timeout, self.reset_round_just_started)

        def reset_round_just_started(self):
            self.round_just_started = False
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
            # generate positions
            
            map = self.map
            blue_cp = []
            green_cp = []

            offset_point = -32
            points = self.generate_spawn_points(512, CP_EXTRA_COUNT, 32, int(offset_point))

            entities = []
            for i in range(len(points)):    
                if i < CP_EXTRA_COUNT / 2:
                    blue_cp.append(points[i])
                else:
                    green_cp.append(points[i])
            
            magnitude = 10
            angle = random.uniform(START_ANGLE, END_ANGLE)
            x, y = (0, random.randrange(64, 512 - 64))
            
            points = []
            
            square_1 = xrange(128)
            square_2 = xrange(512 - 128, 512)
            
            index = 0

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
