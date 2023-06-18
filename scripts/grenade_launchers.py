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
from pyspades.contained import BlockAction

GUNS_INTERVALS = {
    RIFLE_WEAPON : 0.5,
    SMG_WEAPON : 0.11,
    SHOTGUN_WEAPON : 1.0
}

def shoot_grenade(connection, protocol, player, x, y, z, color):
    if x < 0 or y < 0 or z < 0 or x >= 512 or y >= 512 or z > 62:
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
        
           if grenade:
               newAmount = hit_amount
               
               # Assume it's grenade launcher's projectile (and not a regular grenade).
               # Regular grenades will deal the same damage as launcher's projectiles for now
               if self.weapon == SMG_WEAPON:
                   newAmount = 20.0
               elif self.weapon == RIFLE_WEAPON: 
                   newAmount = 50.0
               elif self.weapon == SHOTGUN_WEAPON: 
                   newAmount = 50.0

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
            if self.weapon is SMG_WEAPON:
                multipler = 1.9
            else:
                multipler = 2.2
            
            velocity.x *= multipler
            velocity.y *= multipler
            velocity.z *= multipler
             
            grenade = protocol.world.create_object(Grenade, 0.0,
                position, None, velocity, self.nade_exploded)
            
            grenade.name = 'rocket'
            
            # Figure out when grenade will land
            collision = grenade.get_next_collision(UPDATE_FREQUENCY)
            if collision:
                eta, tmpA, tmpA, tmpA = collision
                grenade.fuse = eta
                
            grenade_packet.value = grenade.fuse
            grenade_packet.player_id = player.player_id
            grenade_packet.position = position.get()
            grenade_packet.velocity = velocity.get()
            
            protocol.send_contained(grenade_packet)
           
        def nade_exploded(self, grenade):
            position, velocity = grenade.position, grenade.velocity
            
            # Penetrate up to 2 blocks to get to the solid block
            extra_distance = 2
            while extra_distance:
                solid = self.protocol.map.get_solid(*position.get())
                if solid or solid is None:
                    break
                    
                position += velocity
            
            # Expload a bit higher to not damage ground too much on indirect impact
            if position.z >= 1:
                position.z -= 1
            
            connection.grenade_exploded(self, grenade)
            
    return protocol, GrenadeLaunchersConnection
    
       