from ..frame_data import Database, Entry

def start_match() -> None:
    pass

def finish_match() -> None:
    Database.d.finish_match()

def handle_entry(entry: Entry.Entry) -> None:
    if Entry.DataColumns.is_player in entry:
        Database.d.record_move(entry)
