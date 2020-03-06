class Globals:
    master = None
    tekken_state = None
    game_reader = None

    @classmethod
    def get_master(cls):
        return self.master

    @classmethod
    def get_state(cls):
        return cls.tekken_state

    @classmethod
    def get_reader(cls):
        return cls.game_reader
