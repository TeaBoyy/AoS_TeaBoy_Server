# TODO: test
from sys import version
if version.startswith("2"):
    def isnt_voxlap(self):
        return self.client_info.client in (ord("B"), ord("o"))
else:
    def isnt_voxlap(self):
        return self.client_info["client"] in ("OpenSpades", "BetterSpades")


def apply_script(protocol, connection, config):
    class ExtendedChatConnection(connection):
        def broadcast_chat_warning(self, message, team=None):
            return self.send_chat("%% " + str(message), team)
            
    return protocol, ExtendedChatConnection

