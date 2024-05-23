from pyspades.constants import MAX_TERRITORY_COUNT, MIN_TERRITORY_COUNT, TC_MODE
from pyspades.server import Territory

def apply_script(protocol, connection, config):
    class TCExtensionProtocol(protocol):
        game_mode = TC_MODE
        
        # TODO:
        def get_cp_entities(self): 
            return protocol.get_cp_entities(self)
            entities = []
            #flag = FrontlineTerritory(i, self, *self.get_random_location(zone = (x1, y1, x2, y2)))
            
            #entities.append(flag)
            return entities

    return TCExtensionProtocol, connection