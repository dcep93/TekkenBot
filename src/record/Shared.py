from misc import Path

RAW_PATH = 'recording.txt'

class Shared:
    frame_data_overlay = None
    game_reader = None
    game_log = None

def get_path(file_name=RAW_PATH):
    return Path.path('./record/%s' % file_name)
