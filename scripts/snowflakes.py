import random
import time

"""
Generares snowflakes in the sky.
Points are generated randomly.

Config parameters:
1. snowflakes_amount (default=1500) -> total amount of snowflakes on map.
2. snowflakes_height_start (default=35) -> height starting from which snowflakes begin to appear.

Compatibility note: make sure to apply this script AFTER snow generation (with snow.py).
Generally, do this after any other terrain modifications in on_map_change() (so that other code doesn't add stuff on top of snowflakes).

Known issues:
1. Tents (and probably intels) can spawn on top of snowflakes. The higer the density, the higher propability of this happening.
2. Players can spawn on snowflakes as well. 

Ideas:
1. Apply snow and snowflakes randomly, not on every map change.
2. Allow to dynamically change snowflakes color (via config change + reloadconfig.py).
3. Consider adding some gradient for color, though white color might be the best.
4. Optimization - takes 80ms for only 1500 snowflakes to generate, maybe use some noise algorithm instead of just random points.
"""

# TODO: add ability to exclude, or include maps

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
        def generate_snowflakes_on_map(self, map):
            snowflakes_amount = config.get('snowflakes_amount', 1500)
            snowflakes_height_start = config.get('snowflakes_height_start', 35)

            points = get_snowflake_points(snowflakes_amount, snowflakes_height_start)

            # Check collisions with map before adding snowflakes
            valid_points = []
            for x, y, z in points:
                if is_valid_snowflake_point(map, x, y, z):
                    valid_points.append((x, y, z))
                
            # Spawn snowflakes on map
            for x, y, z in valid_points:
                map.set_point(x, y, z, SNOW_COLOR)

        def on_map_change(self, map):
            try:
                if not config.get('snow_enabled', True):
                    return protocol.on_map_change(self, map)
                
                # TODO: doesn't work for random maps like "classicgen #N"
                current_map_name = self.map_info.name.lower()
                exluded_map_names = config.get('snow_exclude_maps', [])
                
                for exluded_map_name in exluded_map_names:
                    if current_map_name == exluded_map_name.lower():
                        print("Skipping snowflakes generation for map: %s" % current_map_name)
                        return protocol.on_map_change(self, map)

                print("Generating snowflakes...")
                start_time = time.time()

                self.generate_snowflakes_on_map(map)

                elapsed_time_ms = (time.time() - start_time) * 1000.0
                print("Done Generating snowflakes in: %s ms" % elapsed_time_ms)
            except Exception as error:
                print("ERROR: failed to generate snowflakes. Exception: ", error)

            return protocol.on_map_change(self, map)
        
    return SnowflakesProtocol, connection