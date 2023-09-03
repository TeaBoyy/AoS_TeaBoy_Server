from pyspades.constants import MAX_TERRITORY_COUNT, MIN_TERRITORY_COUNT, TC_MODE
from pyspades.server import Territory

def apply_script(protocol, connection, config):
    class TCExtensionProtocol(protocol):
        game_mode = TC_MODE
        
        def get_cp_entities(self): 
            # Edited algorithm to be able to scale the battlefield
            # Scale 1.0 is default value, scale below 1.0 isn't supported
            scale_x = config.get('mini_tc_scale_x', 1.5)
            scale_y = config.get('mini_tc_scale_y', 1.5)

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
            
            j = 512.0 / territory_count

            # Scale down distance between entities on X-axis
            if scale_x > 1.0:
                j /= scale_x

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

                flag = Territory(i, self, *self.get_random_location(
                    zone = (x1, y1, x2, y2)))
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

    return TCExtensionProtocol, connection