# Logs player count whenever player joins/disconnects

from datetime import datetime

LOG_FILE_PATH="player_count_log.txt"

def apply_script(protocol, connection, config):
    class LogPlayerCountConnection(connection):
        logfile = None
        logfile_opened = False

        def on_connect(self):
            self.log_player_count()
            return connection.on_connect(self)
        
        def on_disconnect(self):
            self.log_player_count()
            return connection.on_disconnect(self)
        
        def log_player_count(self):
            try:
                player_count = len(self.protocol.connections)
                current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                log_entry = "[" + current_date + "] " + "Current player count: " + str(player_count) + ".\n"

                if not self.logfile_opened:
                    self.logfile = open(LOG_FILE_PATH, "a")

                if self.logfile is not None:
                    self.logfile.write(log_entry)
                    self.logfile.flush()
                else:
                    print(log_entry)
            except Exception:
                print("Got some exception for log_player_count")

    return protocol, LogPlayerCountConnection