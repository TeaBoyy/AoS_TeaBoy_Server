"""
Makes guns shoot grenades. Work in progress.
"""

from pyspades.server import block_action
from pyspades.common import Vertex3
from pyspades.constants import *
from commands import add, admin, get_player
from pyspades.world import Grenade
from pyspades.server import orientation_data, grenade_packet
from twisted.internet.task import LoopingCall
from pyspades.collision import distance_3d, distance_3d_vector
from math import sin, floor
from pyspades.contained import BlockAction, SetColor
from pyspades.common import make_color

GUNS_INTERVALS = {
    RIFLE_WEAPON : 0.5,
    SMG_WEAPON : 0.11,
    SHOTGUN_WEAPON : 1.0
}

global G_RIFLE_LAUNCHER_DAMAGE
G_RIFLE_LAUNCHER_DAMAGE=50.0

global G_SMG_LAUNCHER_DAMAGE
G_SMG_LAUNCHER_DAMAGE=15.0

global G_SHOTGUN_LAUNCHER_DAMAGE
G_SHOTGUN_LAUNCHER_DAMAGE=50.0

global G_RIFLE_GRENADE_NAME
G_RIFLE_GRENADE_NAME="rifle_underslung"

def set_weapon_launcher_damage(connection, value = None, damage_ordinal = 0, launcher_type = "Unknown"):
    global G_RIFLE_LAUNCHER_DAMAGE
    global G_SMG_LAUNCHER_DAMAGE
    global G_SHOTGUN_LAUNCHER_DAMAGE

    try:
        if value is not None:
            old_damage = 0.0

            # May throw
            new_damage = float(value)

            if damage_ordinal is 0:
                old_damage = G_RIFLE_LAUNCHER_DAMAGE
                G_RIFLE_LAUNCHER_DAMAGE = new_damage
            elif damage_ordinal is 1:
                old_damage = G_SMG_LAUNCHER_DAMAGE
                G_SMG_LAUNCHER_DAMAGE = new_damage
            elif damage_ordinal is 2:
                old_damage = G_SHOTGUN_LAUNCHER_DAMAGE
                G_SHOTGUN_LAUNCHER_DAMAGE = new_damage
            else:
                return

            chat_message = "[INFO] Changed " + launcher_type  + " grenade launcher damage from " + str(old_damage) + " to " + str(new_damage)
            connection.protocol.send_chat(chat_message)
    except Exception:
        print("Got some exception for set_weapon_launcher_damage")
    return 

@admin
def setrifledamage(connection, value = None):
    set_weapon_launcher_damage(connection, value, 0, "Rifle")
    return

@admin
def setsmgdamage(connection, value = None):
    set_weapon_launcher_damage(connection, value, 1, "SMG")
    return

@admin
def setshotgundamage(connection, value = None):
    set_weapon_launcher_damage(connection, value, 2, "Shotgun")
    return

add(setrifledamage)
add(setsmgdamage)
add(setshotgundamage)

def shoot_grenade(connection, protocol, player, x, y, z, color):
    if x < 0 or y < 0 or x >= 512 or y >= 512 or z > 62:
        return False

    player.spawn_grenade(connection, protocol, player, x, y, z)
    return True

def generate_grenade(player, connection):
    if player.tool != WEAPON_TOOL:
        return

    location = player.world_object.position
    x, y, z = location.x, location.y, location.z

    shoot_grenade(connection, player.protocol, player, x, y, z, player.color)
    
def apply_script(protocol, connection, config):
    class GrenadeLaunchersConnection(connection):
        should_stop_loop = False
        smg_shot_ordinal = 0
        
        def on_connect(self):
            self.bullet_loop = LoopingCall(self.bullet_shoot)
            return connection.on_connect(self)
        
        def bullet_shoot(self):
            if self.should_stop_loop:
                self.bullet_loop.stop()
                self.should_stop_loop = False
                self.smg_shot_ordinal = 0
                return
                
            if self.weapon == SMG_WEAPON:
                if self.smg_shot_ordinal != 0 and self.smg_shot_ordinal % 2 == 0:
                    # Skip every third bullet
                    self.smg_shot_ordinal = 0
                    return
                    
                self.smg_shot_ordinal += 1
                
            generate_grenade(self, connection)
        
        def on_reset(self):
            if self.bullet_loop and self.bullet_loop.running:
                self.bullet_loop.stop()
                
            self.should_stop_loop = False
            self.smg_shot_ordinal = 0
            connection.on_reset(self)
        
        def on_shoot_set(self, fire):
            if self.bullet_loop:
                if not self.bullet_loop.running and fire:
                    if self.tool == WEAPON_TOOL:
                        # Start shooting loop
                        self.bullet_loop.start(GUNS_INTERVALS[self.weapon])
                elif self.bullet_loop.running and not fire:
                    # Stop shooting loop
                    self.should_stop_loop = True
                elif self.bullet_loop.running and fire:
                    if self.tool == WEAPON_TOOL:
                        self.should_stop_loop = False
                        
            return connection.on_shoot_set(self, fire)
        
        def on_kill(self, killer, type, grenade):
            if self.bullet_loop:
                if self.bullet_loop.running:
                    self.bullet_loop.stop()
            
            self.should_stop_loop = False
            self.smg_shot_ordinal = 0
            
            return connection.on_kill(self, killer, type, grenade)
            
        def on_hit(self, hit_amount, hit_player, hit_type, grenade):  
            if self.player_id == hit_player.player_id:
                # Player can't hit themselves
                return False
               
            if hit_player.god:
                return connection.on_hit(self, hit_amount, hit_player, hit_type, grenade)

            if grenade and grenade.name == "no_damage_grenade":
                return False

            if grenade:
                newAmount = hit_amount
                
                global G_RIFLE_LAUNCHER_DAMAGE
                global G_SMG_LAUNCHER_DAMAGE
                global G_SHOTGUN_LAUNCHER_DAMAGE

                # Assume it's grenade launcher's projectile (and not a regular grenade).
                # Regular grenades will deal the same damage as launcher's projectiles for now
                if self.weapon == SMG_WEAPON:
                    newAmount = G_SMG_LAUNCHER_DAMAGE
                elif self.weapon == RIFLE_WEAPON: 
                    newAmount = G_RIFLE_LAUNCHER_DAMAGE
                elif self.weapon == SHOTGUN_WEAPON: 
                    newAmount = G_SHOTGUN_LAUNCHER_DAMAGE

                return newAmount
            elif hit_type is WEAPON_KILL or hit_type is HEADSHOT_KILL:
                    # This is regular bullet, it deals no damage
                    return False

            # Handle melee, fall
            return connection.on_hit(self, hit_amount, hit_player, hit_type, grenade)

        def _on_reload(self):
            # Refill ammo only
            self.weapon_object.restock()
            return connection._on_reload(self)

        def spawn_grenade(self, connection, protocol, player, x, y, z):
            position = Vertex3(x, y, z)
            direction = player.world_object.orientation.copy().normal()
            velocity = direction
            
            multipler = 2
            grenade_name = "underslung"
            if self.weapon is SMG_WEAPON:
                multipler = 2.0
                grenade_name = "smg_underslung"
            elif self.weapon is RIFLE_WEAPON:
                multipler = 2.2
                grenade_name = G_RIFLE_GRENADE_NAME
            elif self.weapon is SHOTGUN_WEAPON:
                multipler = 2.2
                grenade_name = "shotgun_underslung"

            velocity.x *= multipler
            velocity.y *= multipler
            velocity.z *= multipler
             
            grenade_callback = self.nade_exploded
            if player.world_object.sneak:
                if not config.get('nade_launcher_restore_blocks', False):
                    protocol.send_chat("Block restoration is temporarily turned off!")
                    return
                grenade_callback = self.rollback_seed_exploded
                
            grenade = self.create_grenade(position, velocity, grenade_callback, grenade_name)

            # Figure out when grenade will land
            collision = grenade.get_next_collision(UPDATE_FREQUENCY)
            if collision:
                eta, tmpA, tmpA, tmpA = collision
                grenade.fuse = eta
                
            self.send_grenade_packet(grenade.fuse, player.player_id, position, velocity)
           
        def nade_exploded(self, grenade):
            position, velocity = grenade.position, grenade.velocity
            velocity.normalize()

            # Penetrate up to 2 blocks to get to the solid block
            self.penetrate_blocks(grenade, 2)
            
            # Explode a bit higher to not damage ground too much on indirect impact
            if position.z >= 1:
                position.z -= 1
            
            # TODO: read big explosion bool from config
            # TODO: allow other weapons to be togglable with own explosion size
            # TODO: what about shotgun rn?

            # Increase destruction area for Rifle
            if grenade.name == G_RIFLE_GRENADE_NAME:
                # TODO: read size from config
                grid_size = 2 # 2x2x2
                self.create_grenade_grid(position, grid_size, False, 1)

            connection.grenade_exploded(self, grenade)

        def create_grenade_grid(self, position, grid_size, send_to_client = False, extra_height = 0):
            zero_vector = Vertex3(0, 0, 0)
            grenade_impact_size = 3.0

            if grid_size < 0 or grid_size - 1 < 0:
                return

            offset = (grenade_impact_size / 2) * (grid_size - 1)
            top_left_center_positon = position.copy()
            top_left_center_positon.x -= offset
            top_left_center_positon.y -= offset
            top_left_center_positon.z -= offset
            
            for dx in range(0, grid_size):
                for dy in range(0, grid_size):
                    for dz in range(0, grid_size):
                        origin_position = top_left_center_positon.copy()
                        origin_position.x += dx * grenade_impact_size
                        origin_position.y += dy * grenade_impact_size
                        origin_position.z += dz * grenade_impact_size

                        origin_position.z -= extra_height

                        # Spawn extra grenades on server side only
                        _ = self.create_grenade(origin_position, zero_vector, self.grenade_exploded, "no_damage_grenade")

            # Create extra explosions at origin point on client side for better visual/audio feedback
            for _ in range(0,3):
                # TODO: maybe don't spawn extra nades if exploded too close, to avoid water splash and other effects (though keep performance in mind)
                self.send_grenade_packet(0, 31, position, zero_vector)

        def create_grenade(self, position, velocity, grenade_callback, name, fuse = 0.0):
            grenade = self.protocol.world.create_object(Grenade, 0.0, position, None, velocity, grenade_callback)
            grenade.name = name
            grenade.fuse = fuse
            
            return grenade

        def send_grenade_packet(self, fuse, player_id, position, velocity):
            grenade_packet.value = fuse
            grenade_packet.player_id = player_id
            grenade_packet.position = position.get()
            grenade_packet.velocity = velocity.get()
            self.protocol.send_contained(grenade_packet)

        def rollback_seed_exploded(self, grenade):
            try:
                self.penetrate_blocks(grenade, 1)
                self.rollback_area(grenade.position)
            except Exception:
                print("Got some exception for rollback_seed_exploded")

            return False
        
        # TODO: use this for nade_exploded as well
        def penetrate_blocks(self, grenade, depth = 2):
            position, velocity = grenade.position, grenade.velocity
            velocity.normalize()

            # Penetrate up to 2 blocks to get to the solid block
            extra_distance = depth
            for _ in range(extra_distance):
                solid = self.protocol.map.get_solid(*position.get())
                if solid or solid is None:
                    break
                    
                position += velocity
            return 
        
        def rollback_area(self, position):
            # Hardcoded size
            size = 5 
            start_point = position.copy() 
            start_point.x -= 2
            start_point.y -= 2

            block_action = BlockAction()
            block_action.player_id = 31 

            set_color = SetColor()
            set_color.player_id = 31

            for z in range(-2, size - 2):
                for x in range(0, size):
                    for y in range(0, size):
                        current_restore_pos = start_point.copy()
                        current_restore_pos.z -= z
                        current_restore_pos.x += x
                        current_restore_pos.y += y

                        cur_solid = self.protocol.map.get_solid(current_restore_pos.x, current_restore_pos.y, current_restore_pos.z)
                        old_solid = self.protocol.original_map.get_solid(current_restore_pos.x, current_restore_pos.y, current_restore_pos.z)

                        action = None

                        if cur_solid and not old_solid:
                            action = DESTROY_BLOCK
                            self.protocol.map.remove_point(current_restore_pos.x, current_restore_pos.y, current_restore_pos.z)
                        elif old_solid and not cur_solid:
                            action = BUILD_BLOCK
                            new_color = self.protocol.original_map.get_color(current_restore_pos.x, current_restore_pos.y, current_restore_pos.z)
                            
                            if config.get('nade_launcher_restore_blocks_grayscale', True):
                                r, g, b = new_color
                                r = g = b = ((r + g + b) / 2)
                                new_color = (r, g, b)

                            self.protocol.map.set_point(current_restore_pos.x, current_restore_pos.y, current_restore_pos.z, new_color)
                            set_color.value = make_color(*new_color)
                            self.protocol.send_contained(set_color, save = True)

                        if action is not None:
                            block_action.x = current_restore_pos.x
                            block_action.y = current_restore_pos.y
                            block_action.z = current_restore_pos.z
                            block_action.value = action
                            self.protocol.send_contained(block_action, save = True)

            return
        
        def on_block_destroy(self, x, y, z, mode):
            if mode is SPADE_DESTROY or mode is GRENADE_DESTROY:
                return connection.on_block_destroy(self, x, y, z, mode) 
                    
            if self.bullet_loop.running:
                return False

            return connection.on_block_destroy(self, x, y, z, mode)
        
    class GrenadeSeedRollbackProtocol(protocol):
        def on_map_change(self, map):
            self.original_map = map.copy()
            protocol.on_map_change(self, map)
        
    return GrenadeSeedRollbackProtocol, GrenadeLaunchersConnection
    
       