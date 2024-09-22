from pyspades.constants import CHAT_ALL
from pyspades.server import chat_message

# TODO: test
from sys import version
if version.startswith("2"):
    def isnt_voxlap(self):
        return self.client_info.client in (ord("B"), ord("o"))
else:
    def isnt_voxlap(self):
        return self.client_info["client"] in ("OpenSpades", "BetterSpades")

# TODO:
if not version.startswith("2"):
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


    return protocol, ExtendedChatConnection

