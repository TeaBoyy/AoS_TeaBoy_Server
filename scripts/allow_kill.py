# Allows non-admin players to kill their Deuce, yet allow admin players to kill others

from commands import add, get_player

def kill(connection, value=None):
    if value is None:
        player = connection
    else:
        if not connection.rights.kill and not connection.admin:
            return
        player = get_player(connection.protocol, value, False)
    player.kill()

add(kill)

def apply_script(protocol, connection, config):
    return protocol, connection