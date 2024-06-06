from pyspades.constants import MAX_TERRITORY_COUNT, MIN_TERRITORY_COUNT, TC_MODE
from pyspades.server import Territory

def apply_script(protocol, connection, config):
    class TCExtensionProtocol(protocol):
        game_mode = TC_MODE
        
        tents_grid = []

        def reset_tc(self):
            self.tents_grid = []
            protocol.reset_tc(self)

        # TODO:
        def get_cp_entities(self): 
            max_entities_count = 16

            grid_width = 4
            grid_height = 3

            if (grid_width * grid_height > max_entities_count):
                print("Exceeding 16 tents limit")
                return []

            extra_fallback_tent_count = 1

            offset_x = 512 / (grid_width + extra_fallback_tent_count)
            offset_y = 512 / (grid_height + extra_fallback_tent_count)

            for i in range(grid_height):
                self.tents_grid.append([None for i in range(grid_width)])

            # Skip one tent distance
            start_x = offset_x
            start_y = offset_y

            entities = []
            counter = 0 
            for x in range(0, grid_width):
                for y in range(0, grid_height):

                    point_x = start_x + offset_x * x
                    point_y = start_y + offset_y * y


                    tent = Territory(counter, self, *(point_x, point_y, self.map.get_z(point_x, point_y)))
                    if x < grid_width / 2:
                        tent.team = self.blue_team
                    elif x > (grid_width - 1) / 2:
                        tent.team = self.green_team
                    else:
                        # Neutral
                        tent.team = None

                    self.tents_grid[y][x] = tent
                    entities.append(tent)
                    counter += 1

            return entities

    return TCExtensionProtocol, connection