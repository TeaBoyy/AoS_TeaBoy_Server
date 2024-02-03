from pyspades.constants import MAX_TERRITORY_COUNT, MIN_TERRITORY_COUNT, TC_MODE
from pyspades.server import Territory

def apply_script(protocol, connection, config):
    class RespawnConnection(connection):
        def get_spawn_location(self):
            alive_enemy_count = 0
            alive_friendly_count = 0
            for bot in self.protocol.players.values():
                if bot.world_object is None:
                    continue

                if bot.world_object.dead == False:
                    if bot.team != self.team: 
                        alive_enemy_count += 1
                    else:
                        alive_friendly_count += 1

            move = 0    

            # TODO: doesn't take into account respawn time
            print("alive_enemy_count: ", alive_enemy_count, "; alive_friendly_count: ", alive_friendly_count)
            if False and alive_enemy_count < alive_friendly_count:
                # TODO: respawn further to let enemy team survive longer
                move = 2
                if self.team.id == 0:
                    move = move * -1
                print("Spawning bot further. team.id: ", self.team.id)

            #self.protocol.blue_spawn_ordinal = 1
            #self.protocol.green_spawn_ordinal = 1
            if move == 0 and self.team.id == 0:
                player_count = 5
                print("self.protocol.blue_spawn_ordinal: ", self.protocol.blue_spawn_ordinal)
                if self.protocol.blue_spawn_ordinal <= int(player_count / 2):
                    move = 1
                    self.protocol.blue_spawn_ordinal += 1
                    self.protocol.blue_spawn_ordinal = 100
                    #print("Blue spawn: first")
                elif self.protocol.blue_spawn_ordinal > int(player_count / 2) and self.protocol.blue_spawn_ordinal < int(player_count):
                    move = 2
                    self.protocol.blue_spawn_ordinal += 1
                    #print("Blue spawn: second")
                else:
                    move = 1
                    #print("Blue spawn: next - always first")

                """
                if self.protocol.blue_spawn_ordinal == 0:
                    move = 1
                    self.protocol.blue_spawn_ordinal += 1
                elif self.protocol.blue_spawn_ordinal == 1:
                    move = 2
                    self.protocol.blue_spawn_ordinal += 1
                    #self.protocol.blue_spawn_ordinal = 0
                else:
                    move = 1
                    #self.protocol.blue_spawn_ordinal = 1 
                    """
                move = move * -1
            elif move == 0:
                player_count = 5
                if self.protocol.green_spawn_ordinal <= int(player_count / 2):
                    move = 1
                    self.protocol.green_spawn_ordinal += 1
                    self.protocol.green_spawn_ordinal = 100
                    #print("Green spawn: first")
                elif self.protocol.green_spawn_ordinal > int(player_count / 2) and self.protocol.green_spawn_ordinal < int(player_count):
                    move = 2
                    self.protocol.green_spawn_ordinal += 1
                    #print("Green spawn: second")
                else:
                    move = 1
                    #print("Green spawn: next - always first")

                move = move * 1

                """
                if self.protocol.green_spawn_ordinal == 0:
                    move = 1
                    self.protocol.green_spawn_ordinal += 1
                elif self.protocol.green_spawn_ordinal == 1:
                    move = 2
                    self.protocol.green_spawn_ordinal += 1
                    #self.protocol.green_spawn_ordinal = 0
                else:
                    move = 1
                    #self.protocol.green_spawn_ordinal = 1
                """
                print("move: ", move)

            spawn_id = 0
            territory_count = 6
            if self.team.id == 0:
                spawn_id = (territory_count / 2 - 1) + move
            else:
                spawn_id = (territory_count / 2) + move

            if spawn_id < 0 or spawn_id >= territory_count:
                print("ERROR: out of tents")
            else:
                base = self.protocol.entities[spawn_id]
            print("base.id: ", base.id)

            return base.get_spawn_location()
            #return (base.x, base.y, base.z)
            return self.protocol.get_random_location(zone = (base.x - 10, base.y - 10, base.x + 10, base.y + 10))

    def convert_entity_pos_to_map_label(pos = (0.0, 0.0)):
        x, y = pos

        map_chunks_count = 8
        map_chunk_size = 512 / map_chunks_count

        x_index = int(x / map_chunk_size)
        y_index = int(y / map_chunk_size)

        if x_index >= map_chunks_count:
            x_index = map_chunks_count - 1
        elif x_index < 0:
            x_index = 0

        if y_index >= map_chunks_count:
            y_index = map_chunks_count - 1
        elif y_index < 0:
            y_index = 0

        return "" + chr(ord('A') + x_index) + "" + chr(ord('1') + y_index)
    
    class TCExtensionTerritory(Territory):
        def send_tent_map_label_to_chat(self, team, isTaking = True, pos = (0.0, 0.0)):
            # TODO: test
            return
            if team is None:
                team_str = "Unknown"
            elif team.id == 0:
                team_str = "Blue"
            elif team.id == 1:
                team_str = "Green"
            else:
                team_str = "Unknown"

            chat_message = team_str + " team is "

            if not isTaking:
                chat_message += "no longer "

            chat_message += "taking objective " + convert_entity_pos_to_map_label(pos) + "!"
            self.protocol.send_chat(chat_message)

        def update_rate(self):
            had_finish_call = self.finish_call != None
            Territory.update_rate(self)
            has_finish_call = self.finish_call != None

            if not had_finish_call and has_finish_call:
                self.send_tent_map_label_to_chat(self.capturing_team, True,  (self.x, self.y))
            elif had_finish_call and not has_finish_call:
                self.send_tent_map_label_to_chat(self.capturing_team, False,  (self.x, self.y))

    class TCExtensionProtocol(protocol):
        game_mode = TC_MODE
        
        # TODO: test
        blue_spawn_ordinal = 0
        green_spawn_ordinal = 0

        def get_cp_entities(self): 
            entities = []

            territory_count = 6
            offset = int(512 / territory_count)

            for i in range(0, territory_count):
                x1 = offset * i + 32
                x2 = x1 + 5

                y1 = 256
                y2 = 264

                location = self.get_random_location(zone = (x1, y1, x2, y2))
                flag = TCExtensionTerritory(i, self, *location)
                if i < territory_count / 2:
                    team = self.blue_team
                elif i > (territory_count-1) / 2:
                    team = self.green_team
                else:
                    # odd number - neutral
                    team = None
                flag.team = team
                entities.append(flag)

            return entities

            # Edited algorithm to be able to scale the battlefield
            # Scale 1.0 is default value, scale below 1.0 isn't supported
            scale_x = config.get('mini_tc_scale_x', 1.5)
            scale_y = config.get('mini_tc_scale_y', 1.5)

            # TODO:
            scale_x = 1.25
            scale_y = 100

            # Shift by a half of total area outside of battlefield
            offset_x = (512.0 - (512.0 / scale_x)) / 2
            
            y_beginning = (512.0 / 4)
            y_end = y_beginning * 3
            y_size = (y_end - y_beginning)

            # Shift by a half of total area outside of battlefield (relative to pre-defined area for Y-axis)
            offset_y = (y_size - (y_size / scale_y)) / 2

            # cool algorithm number 1
            entities = []
            land_count = self.map.count_land(0, 0, 512, 512)
            territory_count = int((land_count/(512.0 * 512.0))*(
                MAX_TERRITORY_COUNT-MIN_TERRITORY_COUNT) + MIN_TERRITORY_COUNT)
            
            # TODO: test
            territory_count = 12

            j = 512.0 / territory_count

            # Scale down distance between entities on X-axis
            if scale_x > 1.0:
                j /= scale_x

            count = 0
            row_count = 0
            for i in range(territory_count):
                x1 = i * j
                y1 = 512 / 4
                x2 = (i + 1) * j
                y2 = y1 * 3

                # Shift coordinates according to scale
                x1 += offset_x
                x2 += offset_x
                y1 += offset_y
                y2 -= offset_y

                # TODO:
                offset_gray = 32
                if i < territory_count / 2:
                    x1 -= offset_gray
                    x2 -= offset_gray
                elif i > (territory_count-1) / 2:
                    x1 += offset_gray
                    x2 += offset_gray

                if count == 0:
                    y1 -= 128
                    y2 -= 128
                elif count == 1:
                    y1 -= 0
                    y2 -= 0
                else:
                    y1 += 128
                    y2 += 128

                y1 += row_count * 16
                y2 += row_count * 16

                count+=1
                if count >= 3:
                    row_count+=1
                    count = 0

                if row_count >= 2:
                    row_count = 0

                location = self.get_random_location(zone = (x1, y1, x2, y2))
                _, _, check_z = location
                if check_z >= 63:
                    print("skipping z: ", check_z)
                    continue

                flag = TCExtensionTerritory(i, self, *location)
                if i < territory_count / 2:
                    team = self.blue_team
                elif i > (territory_count-1) / 2:
                    team = self.green_team
                else:
                    # odd number - neutral
                    team = None
                flag.team = team
                entities.append(flag)
            return entities

    return TCExtensionProtocol, RespawnConnection