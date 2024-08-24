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

# TODO:
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

            return self.my_get_spawn_location(base.x, base.y)
            #return base.get_spawn_location()
            
        def my_get_spawn_location(self, x, y):

            # TODO:
            offset = 20
            if self.team == self.protocol.green_team:
                offset_x = offset
                offset_y = offset
            else:
                offset_x = -offset
                offset_y = -offset

            # TODO:
            x += offset_x
            y += offset_y

            # TODO: this is not bad. X is same, but reduce Y so that don't spawn closer than needed.
            # TODO: tho stuck at 2nd tent so idk
            my_radius = 28
            x1 = max(0, x - my_radius)
            y1 = max(0, y - my_radius)
            x2 = min(512, x + my_radius)
            y2 = min(512, y + my_radius)
            
            return self.protocol.get_random_location(True, (x1, y1, x2, y2))

        # TODO: read more https://foxhole.fandom.com/wiki/Respawning

        # TODO: note - classicgen with big hills and 2vs20s respawn time dominating team capped at least 2 tents (2nd too fast, so maybe reduce reset timer from 60s to idk 30s)

        # TODO: issue - only watching for total kills diff, so like even if it stays 15 vs 10 kills, it's still 5 kills, so we keep thinking one side made +5 kills
        # TODO: but it's still playable. Tho if u push too hard, then alone won't be able to easily to shift scales back, making 40kills for example is hard with 14s respawn time
        # TODO: can try and test on 16vs16 for fun but need correponding respawn time for this, which is like twice, so 24-30s will have to be
        def on_kill(self, killer, type, grenade):
            # Every 10 kills for team increase own team respawn time by 2s, decrease other team respawn time by 2

            # TODO: at first just adding/removing didnt seem to work, but over time blue (weaker) reached 10s vs 2s spawn time
            # TODO: so, maybe no need to check for leading team first?
            # TODO: also, should maybe reset at some point? Like, if diff is big, and players leave, like, might not be possible to balance the kills anymore
            # TODO: just it must be possible to push diff back and start bleeding the other team respawn time

            # TODO: in general POC kinda works, green overkills blue so blue respawn time gets to max (12s), though maybe kinda fast.
            # TODO: so far not sure if or how long it takes for green to capture tent. Ok with 12s not much but with 14s faster, maybe up to 7mins?

            # TODO: kills_per_update should control how fast shift happens, how much kills needed to progress

            # TODO: maybe better grow by 1 second, but faster?
            diff_respawn_time = 2

            #max_respawn_time = 14
            #max_respawn_time = 20
            #max_respawn_time = 18
            max_respawn_time = int(16)

            #kills_per_update = 5

            player_count = len(self.protocol.players)

            # The higher, the longer balance shift takes
            kills_per_update_multipler = 1.0
            kills_diff_margine_multipler = 1.0

            stalemate_cooldown_seconds_multiplier = 1.0

            kills_per_update = int((0.3 * player_count) * kills_per_update_multipler)

            if killer != None and killer != self:

                # TODO: margin must be different based on amount of players, 5diff for 2-4 players is too much, while for 20 players not really
                kills_diff_margin = int(0.3 * player_count * kills_diff_margine_multipler)

                # TODO: check if neither is leading too
                kills_diff = self.protocol.green_team.kills - self.protocol.blue_team.kills

                if kills_diff > -kills_diff_margin and kills_diff < kills_diff_margin:
                    print("Neither is leading; green kills -> ", self.protocol.green_team.kills , "; blue kills -> ", self.protocol.blue_team.kills)

                    # TODO: move on some other action/update or start a loop that doesn't rely on on_kill
                    current_time = reactor.seconds() 

                    # TODO: probably must be as high as entire domination time
                    stalemate_cooldown_seconds = int(0.45 * 5.0 * player_count * stalemate_cooldown_seconds_multiplier)

                    if self.protocol.last_stalemate_cooldown_time == None:
                        self.protocol.last_stalemate_cooldown_time = current_time

                    if current_time - self.protocol.last_stalemate_cooldown_time > stalemate_cooldown_seconds:
                        print("Cooldown. Passed ", current_time - self.protocol.last_stalemate_cooldown_time, " seconds, reducing both teams respawn time by ", diff_respawn_time)
                        self.protocol.last_stalemate_cooldown_time = current_time
                        if self.protocol.green_respawn_time > diff_respawn_time:
                            if self.protocol.green_respawn_time - diff_respawn_time >= 2:
                                self.protocol.green_respawn_time -= diff_respawn_time
                                print("Reduced green spawn time by: ", diff_respawn_time, ", it's now: ", self.protocol.green_respawn_time)
                        if self.protocol.blue_respawn_time > diff_respawn_time:
                            if self.protocol.blue_respawn_time - diff_respawn_time >= 2:
                                self.protocol.blue_respawn_time -= diff_respawn_time
                                print("Reduced blue spawn time by: ", diff_respawn_time, ", it's now: ", self.protocol.blue_respawn_time)

                    # TODO: then restore back not leading team's respawn time somehow over time
                    return connection.on_kill(self, killer, type, grenade)
                else:
                    self.protocol.last_stalemate_cooldown_time = None

                green_is_leading = (self.protocol.green_team.kills - self.protocol.blue_team.kills - kills_diff_margin) >= 0

                print("Is green leading -> ", green_is_leading, "; green kills -> ", self.protocol.green_team.kills , "; blue kills -> ", self.protocol.blue_team.kills)

                if green_is_leading and killer.team == self.protocol.green_team:
                    kills = self.protocol.green_team.kills
                    if kills != 0 and kills % kills_per_update == 0:

                        if self.protocol.green_respawn_time > diff_respawn_time:
                            if self.protocol.green_respawn_time - diff_respawn_time >= 2:
                                self.protocol.green_respawn_time -= diff_respawn_time
                                print("Reduced green spawn time by: ", diff_respawn_time, ", it's now: ", self.protocol.green_respawn_time)

                        if self.protocol.blue_respawn_time + diff_respawn_time > max_respawn_time:
                            self.protocol.blue_respawn_time = max_respawn_time
                            print("Blue spawn time reached maximum: ", max_respawn_time)
                        else:
                            self.protocol.blue_respawn_time += diff_respawn_time
                            print("Increased blue spawn time by: ", diff_respawn_time, ", it's now: ", self.protocol.blue_respawn_time)

                        print("Green: +%d kills", kills_per_update)

                if not green_is_leading and killer.team == self.protocol.blue_team:
                    kills = self.protocol.blue_team.kills
                    if kills != 0 and kills % kills_per_update == 0:

                        if self.protocol.blue_respawn_time > diff_respawn_time:
                            if self.protocol.blue_respawn_time - diff_respawn_time >= 2:
                                self.protocol.blue_respawn_time -= diff_respawn_time
                                print("Reduced blue spawn time by: ", diff_respawn_time, ", it's now: ", self.protocol.blue_respawn_time)

                        if self.protocol.green_respawn_time + diff_respawn_time > max_respawn_time:
                            self.protocol.green_respawn_time = max_respawn_time
                            print("Green spawn time reached maximum: ", max_respawn_time)
                        else:
                            self.protocol.green_respawn_time += diff_respawn_time
                            print("Increased green spawn time by: ", diff_respawn_time, ", it's now: ", self.protocol.green_respawn_time)
                    
                        print("Blue: +%d kills", kills_per_update)
            else:
                print("killer is None or self")

            return connection.on_kill(self, killer, type, grenade)

        # TODO:
        def on_spawn(self, pos):
            for line in HELP:
                self.send_chat(line)

            if self.team == self.protocol.blue_team:
                self.respawn_time = self.protocol.blue_respawn_time
            else:
                self.respawn_time = self.protocol.green_respawn_time

            return connection.on_spawn(self, pos)
            
    class TugProtocol(protocol):
        game_mode = TC_MODE

        # TODO:
        initial_respawn_time = 2
        green_respawn_time = initial_respawn_time
        blue_respawn_time = initial_respawn_time
        last_stalemate_cooldown_time = None

        def on_game_end(self):
            print("Game end")
            self.reset_kills_and_respawn_time()
            return protocol.on_game_end(self)

        def get_cp_entities(self):
            map = self.map
            points = []

            # TODO: hardcoded for CP_EXTRA_COUNT == 8

            crutch_offset_ratio = 8.0/CP_EXTRA_COUNT
            #crutch_offset_ratio = 1.0

            # TODO: builds diagonal. Need to unhardcode offsets
            # TODO: add random direction of diagonal, random offset, random angle
            x, y = (46 * crutch_offset_ratio, 46 * crutch_offset_ratio)

            blue_cp = []
            green_cp = []

            for i in range(CP_EXTRA_COUNT):
                points.append((int(x), int(y)))
                x += 60 * crutch_offset_ratio
                y += 60 * crutch_offset_ratio
            
            for i in range(CP_EXTRA_COUNT):
                p_x, p_y = points[i]
                if i < CP_EXTRA_COUNT / 2:
                    blue_cp.append((p_x, p_y))
                else:
                    green_cp.append((p_x, p_y))

            # Note: copy/past from otiginal TOW
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

        # Original algorithm without modification. Unused
        def original_tow_get_cp_entities(self):
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

        reset_kills_and_respawn_time_call = None

        # TODO:
        def reset_kills_and_respawn_time(self):
            # TODO: just resetting actual protocol values seems to work
            print("reset_kills_and_respawn_time")
            self.green_team.kills = 0
            self.blue_team.kills = 0

            self.blue_respawn_time = self.initial_respawn_time
            self.green_respawn_time = self.initial_respawn_time
    
        def on_cp_capture(self, territory):
            # TODO: issue - somehow this reverses balance, so try to call later and see if helps
            if self.reset_kills_and_respawn_time_call != None and self.reset_kills_and_respawn_time_call.active():
                self.reset_kills_and_respawn_time_call.cancel()
                self.reset_kills_and_respawn_time_call = None

            # TODO: sometimes still too much, maybe immediately respawn some players, some later? But that could reverse roles too
            delay = 30
            self.reset_kills_and_respawn_time_call = reactor.callLater(delay, self.reset_kills_and_respawn_time)

            # TODO: smh blue make more kills after reset. Maybe its lack of airstike.py or modifying protocol values flips teams, idk. Why 1st push is ok though?

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

            # TODO: what if bots are already alive, about to die? Do we reset respawn time for them? 
            # TODO: actually even if we do respawn them, should reset their respawn time I guess?
            # Instantly respawn some players to hold off advancing enemy
            player_team_count = int(len(self.players) / 2.0)
            random_players_count = int(0.25 * player_team_count)
            print("Respawning instantly ", random_players_count, " players from the team that lost tent")
            for random_player in self.select_random_players(random_players_count, False, territory.team.other):
                random_player.respawn_time = self.initial_respawn_time
                self.instant_respawn(random_player)

        def select_random_players(self, count, isAlive = False, team = None):
            selected_players = []

            if count <= 0:
                return selected_players

            # TODO: really don't think copying is a good idea
            players = []
            for player in self.players.values():
                if player == None or player.world_object == None:
                    continue

                alive_check = isAlive == True or player.world_object.dead
                team_check = team == None or (team == True or player.team == team)
                if alive_check and team_check:
                    players.append(player)

            if len(players) <= 0:
                return selected_players

            for _ in range(0, count):
                random_player = random.choice(players)
                selected_players.append(random_player)
                players.remove(random_player)
                
            return selected_players

        def instant_respawn(self, player):
            print("instant_respawn")
            delay = 0.1
            if player != None and player.spawn_call != None:
                print("Force-spawning player with respawn time: ", player.respawn_time)
                player.spawn_call.cancel()
                player.spawn_call = reactor.callLater(delay, player.spawn)

    return TugProtocol, TugConnection
