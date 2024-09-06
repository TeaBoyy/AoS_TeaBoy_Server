from twisted.internet.task import LoopingCall

# Utils
def convert_entity_pos_to_map_label(pos = (0.0, 0.0)):
    x, y = pos

    map_chunks_count = 8
    map_chunk_size = 512 / map_chunks_count

    x_index = int(x / map_chunk_size)
    y_index = int(y / map_chunk_size)

    if x_index >= map_chunks_count:
        x_index = map_chunks_count - 1
    elif x_index < 0:
        x_index = 0

    if y_index >= map_chunks_count:
        y_index = map_chunks_count - 1
    elif y_index < 0:
        y_index = 0

    return "" + chr(ord('A') + x_index) + "" + chr(ord('1') + y_index)

def generate_flag_status_report_message(team, isTaking, pos):
    chat_message = team_to_str(team) + " team is "

    if not isTaking:
        chat_message += "no longer "

    chat_message += "taking objective " + convert_entity_pos_to_map_label(pos) + "!"
    return chat_message

def team_to_str(team):
    team_str = "Unknown"
    if team != None:
       team_str = "Blue" if team.id == 0 else "Green"
    return team_str

# Main logic
def apply_script(protocol, connection, config):
    class CaptureReporterProtocol(protocol):
        reporter_loop = None
        reporter_loop_interval = 4.0 # Seconds

        last_flags_capture_states_dict = {}

        def reset_tc(self):
            # Ensure self.entites are up-to-date
            protocol.reset_tc(self)
            try:
                self.setup_reporter_loop()
            except Exception as ex:
                print("Failed to setup flag status reporter. Error: ", ex)

        def setup_reporter_loop(self):
            if self.reporter_loop != None and self.reporter_loop.running:
                self.reporter_loop.stop()

            # Fill up initial state to compare with later
            self.last_flags_capture_states_dict = {}
            for flag in self.entities:
                self.update_flag_state(flag)

            self.reporter_loop = LoopingCall(self.reporter_loop_callback)
            self.reporter_loop.start(self.reporter_loop_interval)

        def update_flag_state(self, flag):
            if flag != None:
                flag_is_capturing = flag.finish_call != None
                self.last_flags_capture_states_dict[flag] = (flag_is_capturing, flag.team, flag.capturing_team)
        
        def reporter_loop_callback(self):
            try:
                for flag in self.entities:
                    self.report_flag_status(flag)
            except Exception as ex:
                print("Failed to check and report flag status. Error: ", ex)

        def report_flag_status(self, flag):
            if flag == None or not self.last_flags_capture_states_dict.has_key(flag):
                return

            needs_reporting = False
            flag_is_capturing = flag.finish_call != None        

            last_state, last_team, last_attacker_team = self.last_flags_capture_states_dict[flag]
            was_captured = (last_team != flag.team)
            if last_state != flag_is_capturing and not was_captured:
                needs_reporting = True
                if flag_is_capturing:
                    # Report current team when capturing, and last team when no longer capturing 
                    last_attacker_team = flag.capturing_team
            
            self.update_flag_state(flag)

            if needs_reporting:
                self.send_chat(generate_flag_status_report_message(last_attacker_team, flag_is_capturing, (flag.x, flag.y)))

    return CaptureReporterProtocol, connection