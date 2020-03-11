from misc import Path

RAW_PATH = 'recording.txt'

def get_path(file_name=RAW_PATH):
    return Path.path('./record/%s' % file_name)
