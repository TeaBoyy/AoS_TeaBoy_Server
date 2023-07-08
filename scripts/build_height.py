"""
Sets hardcoded build height
"""

MAX_BUILD_HEIGHT=30
MAX_DEFAULT_BLOCK_COUNT=50
MAX_BUILD_HEIGHT_MSG="You can't build this high!"

def apply_script(protocol, connection, config):
    class BuildHeightConnection(connection):
        def on_block_build_attempt(self, x, y, z):
            if z <= MAX_BUILD_HEIGHT:
                self.send_chat(MAX_BUILD_HEIGHT_MSG)

                # Fix issue when server code subtracts one block even if it will not be placed
                restored_blocks_count = self.blocks + 1 if self.blocks < MAX_DEFAULT_BLOCK_COUNT else MAX_DEFAULT_BLOCK_COUNT
                self.blocks = restored_blocks_count

                return False
            return connection.on_block_build_attempt(self, x, y, z)
        
        def on_line_build_attempt(self, points):
            for point in points:
                _, _, z = point
                if z <= MAX_BUILD_HEIGHT:
                    self.send_chat(MAX_BUILD_HEIGHT_MSG)
                    return False
            return connection.on_line_build_attempt(self, points)
    
    return protocol, BuildHeightConnection