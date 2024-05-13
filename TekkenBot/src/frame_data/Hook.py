from ..frame_data import Database, Entry

def start_match():
    pass

def finish_match():
    Database.finish_match()

def handle_entry(entry: Entry.Entry):
    if Entry.DataColumns.is_player in entry:
        Database.record_move(entry)
