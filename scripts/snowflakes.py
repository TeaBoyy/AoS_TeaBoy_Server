import random
import time

# TODO: resolve issue with tents/intels spawning on snowflakes. 
# TODO: In case of custom gamemodes like tow, mini-tc can just change order
# TODO: yet players spawning of flakes..welp, gotta check in script itself, but order matters i think

# TODO: add ability to turn on/off
# TODO: add ability to exclude, or include maps
# TODO: add option for random map picking from included maps (yet with reasonable probability)

# TODO: read snow color from config
SNOW_COLOR = (240, 240, 240)

SNOWFLAKE_DIST_TO_SURFACE = 25

def get_snowflake_points(snowflakes_amount, snowflakes_height_start):
    # TODO: more range checks
    # TODO: optimization?

    xrange = (0, 511)
    yrange = (0, 511)
    zrange = (0, min(snowflakes_height_start, 60))

    points = []

    [ points.append((random.uniform(*xrange), random.uniform(*yrange), random.uniform(*zrange))) for i in range(snowflakes_amount) ]

    return points

def is_valid_snowflake_point(map, x, y, z):
    if map.get_solid(x, y, z):
        return False
    
    # Check if too close to mountain/hill top, or just surface in general
    acceptable_distance_from_surface = SNOWFLAKE_DIST_TO_SURFACE
    check_z = z + acceptable_distance_from_surface

    if check_z >= 60 or check_z <= 0:
        return False
    
    if map.get_solid(x, y, check_z):
        return False

    return True

def apply_script(protocol, connection, config):
    class SnowflakesProtocol(protocol):
        def on_map_change(self, map):
            # TODO: add try/catch

            snowflakes_amount = config.get('snowflakes_amount', 1500)
            snowflakes_height_start = config.get('snowflakes_height_start', 35)

            print("Generating %i snowflakes..." % snowflakes_amount)
            start_time = time.time()

            points = get_snowflake_points(snowflakes_amount, snowflakes_height_start)

            # Check collisions with map before adding snowflakes
            valid_points = []
            for x, y, z in points:
                if is_valid_snowflake_point(map, x, y, z):
                    valid_points.append((x, y, z))
                   
            # Spawn snowflakes on map
            for x, y, z in valid_points:
                map.set_point(x, y, z, SNOW_COLOR)

            elapsed_time_ms = (time.time() - start_time) * 1000.0
            print("Done Generating snowflakes in: %s ms" % elapsed_time_ms)

            return protocol.on_map_change(self, map)
        
    return SnowflakesProtocol, connection