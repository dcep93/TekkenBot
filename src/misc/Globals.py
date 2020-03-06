# todo this should be used everywhere

class Globals:
    master = None

    @classmethod
    def is_foreground_pid(cls):
        return cls.master.tekken_state.game_reader.is_foreground_pid()
