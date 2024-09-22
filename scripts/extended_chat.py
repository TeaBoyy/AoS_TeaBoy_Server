from pyspades.constants import CHAT_ALL
from pyspades.server import chat_message

from pyspades.loaders import Loader
from pyspades.packet import load_client_packet
from pyspades.bytes import ByteReader, ByteWriter

class VersionResponse(Loader):
    id = 34
    
    client = str()
    version = tuple()
    os_info = str() 

    def read(self, reader):
        magic_no = reader.readByte(True)
        self.client = chr(magic_no)
        self.version = (
            reader.readByte(True),
            reader.readByte(True),
            reader.readByte(True),
        )
        self.os_info = decode(reader.readString())
    
    def write(self, reader):
        writer.writeByte(self.id, True)

# TODO: test
from sys import version
if version.startswith("2"):
    def isnt_voxlap(self):
        return self.client_info.client in (ord("B"), ord("o"))
else:
    def isnt_voxlap(self):
        return self.client_info["client"] in ("OpenSpades", "BetterSpades")

# TODO:
if version.startswith("2"):
    def is_openspades_client(self):
        return is_client(self, "OpenSpades")

    def is_betterspades_client(self):
        return is_client(self, "BetterSpades")

    def is_other_client(self):
        return not is_openspades_client(self) and not is_betterspades_client(self)

    def is_client(self, client):
        return self.client_info and self.client_info["client"] in (client)

(CHAT_BIG, CHAT_INFO, CHAT_WARNING, CHAT_ERROR) = range(3, 7)

OPENSPADES_CHATTYPES = {
    CHAT_BIG: "C% ",
    CHAT_INFO: "N% ",
    CHAT_WARNING: "%% ",
    CHAT_ERROR: "!% "
}

def apply_script(protocol, connection, config):
    class ExtendedChatConnection(connection):
        def send_chat_warning(self, message, team=None):
            self.send_chat(message, team, CHAT_WARNING)

        def send_chat(self, message, team=None, custom_type=CHAT_ALL):
            if custom_type > 2:
                if self.client_info == None:
                    print("Couldn't print the custom message: ", message)
                    return

                if is_openspades_client(self):
                    return self.send_chat(OPENSPADES_CHATTYPES[custom_type] + str(message), team)
                elif is_betterspades_client(self):
                    # TODO: do word wrap and show piece by pice to fit on the screen
                    chat_message.chat_type = custom_type
                else:
                    print("Unknown client, don't print custom message: ", message)

        """
        def loader_received(self, loader):
            print("TEST loader_received")
            #if self.player_id is not None:
            contained = load_client_packet(ByteReader(loader.data))
            print("contained.id: ", contained.id)
            if contained.id != VersionResponse.id:
                return connection.loader_received(self, loader)

            print("contained.client: ", contained.client)

            # TODO: maybe only return if did nothing?
            return connection.loader_received(self, loader)
        """

    return protocol, ExtendedChatConnection

"""
def apply_script(protocol, connection, config):
    class ExtendedChatConnection(connection):
        def send_chat(self, value, global_message = None):
            print("TEST REDIRECT send_chat. Value: ", value)
            return
    return protocol, ExtendedChatConnection
"""

"""
chat_message = loaders.ChatMessage()
    if custom_type > 2 and "client" in self.client_info:
        if EXTENSION_CHATTYPE in self.proto_extensions:
            chat_message.chat_type = custom_type
        else:
            value = OPENSPADES_CHATTYPES[custom_type] + value

        chat_message.player_id = 35
        prefix = ''
"""