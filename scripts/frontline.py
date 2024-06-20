from pyspades.constants import MAX_TERRITORY_COUNT, MIN_TERRITORY_COUNT, TC_MODE
from pyspades.server import Territory

MAX_ENTITIES_COUNT = 16

def apply_script(protocol, connection, config):
    class FrontlineConnection(connection):
        def get_spawn_location(self):
            return connection.get_spawn_location(self)

    class FrontlineProtocol(protocol):
        game_mode = TC_MODE
        
        tents_grid = []
        grid_width = 4
        grid_height = 3

        blue_team_home_bases = []
        green_team_home_bases = []

        def reset_tc(self):
            self.tents_grid = []
            self.blue_team_home_bases = []
            self.green_team_home_bases = []

            protocol.reset_tc(self)

            if not self.tents_grid or not self.blue_team_home_bases or not self.green_team_home_bases:
                print("Warning: missing tents grid or home bases list")
            
        def get_cp_entities(self): 
            if (self.grid_width * self.grid_height > MAX_ENTITIES_COUNT):
                print("Error: exceeding {} tents limit".format(MAX_ENTITIES_COUNT))
                return []

            extra_fallback_tent_count = 1

            offset_x = 512 / (self.grid_width + extra_fallback_tent_count)
            offset_y = 512 / (self.grid_height + extra_fallback_tent_count)

            for i in range(self.grid_height):
                self.tents_grid.append([None for i in range(self.grid_width)])

            # Skip one tent distance
            start_x = offset_x
            start_y = offset_y

            entities = []
            counter = 0 
            for x in range(0, self.grid_width):
                for y in range(0, self.grid_height):
                    point_x = start_x + offset_x * x
                    point_y = start_y + offset_y * y

                    tent = Territory(counter, self, *(point_x, point_y, self.map.get_z(point_x, point_y)))
                    if x < self.grid_width / 2:
                        tent.team = self.blue_team
                        self.blue_team_home_bases.append(tent)
                    elif x > (self.grid_width - 1) / 2:
                        tent.team = self.green_team
                        self.green_team_home_bases.append(tent)
                    else:
                        # Neutral
                        tent.team = None

                    self.tents_grid[y][x] = tent
                    entities.append(tent)
                    counter += 1

            return entities

        # TODO:
        def get_valid_spawn_points(self, team):
            valid_spawn_points = []
            if team == None:
                return valid_spawn_points

            for x in range(0, self.grid_width):
                for y in range(0, self.grid_height):
                    tent = self.tents_grid[x][y]

                    if tent.team != team:
                        continue

                    # TODO: if own tent, check if got any enemy tents neighbors
                    print("test")

        # TODO:
        def is_tent_a_frontline(self, x, y):
            left, right, down, up = None
            
            if x > 0:
                left = self.tents_grid[x - 1][y]

            if x < self.grid_width - 1:
                right = self.tents_grid[x - 1][y]

            if y > 0:
                down = self.tents_grid[x][y + 1]

             if y < self.grid_height - 1:
                up = self.tents_grid[x][y - 1]

            

    return FrontlineProtocol, FrontlineConnection