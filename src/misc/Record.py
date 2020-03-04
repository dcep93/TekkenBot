class Recording:
    history = None

    @classmethod
    def record(cls, input_state):
        if cls.last_move_was(input_state):
            cls.history[-1][-1] += 1
        else:
            cls.history.append([input_state, 1])

    @classmethod
    def last_move_was(cls, input_state):
        if len(cls.history) == 0:
            return False
        return cls.history[-1][0] == input_state

    @classmethod
    def to_string(cls):
        return cls.history

def record_start():
    Recording.history = []

def record_end():
    print(Recording.to_string())
    Recording.history = None

def record_if_activated(tekken_state):
    if Recording.history is not None:
        input_state = tekken_state.get_input_state()
        Recording.record(input_state)

def replay():
    print('replay')