from . import GameReader
from game_parser import ScriptedGame
from misc import Flags, Globals

class GameState:
    def __init__(self):
        if Flags.Flags.pickle_dest is not None:
            game_reader = ScriptedGame.Recorder(Flags.Flags.pickle_dest)
        elif Flags.Flags.pickle_src is not None:
            game_reader = ScriptedGame.Reader(Flags.Flags.pickle_src)
        else:
            game_reader = GameReader.GameReader()
        Globals.Globals.game_reader = game_reader

        self.state_log = []

    def get(self, is_p1, frames_ago=0):
        if len(self.state_log) <= frames_ago:
            return None
        state = self.state_log[-1-frames_ago]
        return state.p1 if is_p1 else state.p2

    def update(self):
        game_data = Globals.Globals.game_reader.get_updated_state(0)

        if game_data is not None:
            # we don't run perfectly in sync, if we get back the same frame, throw it away
            if len(self.state_log) == 0 or game_data.frame_count != self.state_log[-1].frame_count:
                if len(self.state_log) > 0:
                    frames_lost = game_data.frame_count - self.state_log[-1].frame_count - 1
                    missed_states = min(7, frames_lost)

                    for i in range(missed_states):
                        dropped_state = Globals.Globals.game_reader.get_updated_state(missed_states - i)
                        self.append_gamedata(dropped_state)

                self.append_gamedata(game_data)
                return True
        return False

    def append_gamedata(self, game_data):
        self.state_log.append(game_data)

        if len(self.state_log) > 300:
            self.state_log.pop(0)

    def get_current_move_name(self, is_p1):
        player = self.get(is_p1)
        move_id = player.move_id
        if move_id > 30000:
            return 'Universal_{}'.format(move_id)
        if player.movelist_parser is not None:
            movelist_names = player.movelist_parser.movelist_names
            index = (move_id * 2) + 4
            if index < len(movelist_names):
                move = movelist_names[index]
                try:
                    return move.decode('utf-8')
                except:
                    pass
        return "ERROR"

    def get_current_move_string(self, is_p1):
        parser = self.get(is_p1).movelist_parser
        if parser is not None:
            move_id = self.get(is_p1, 1).move_id
            previous_move_id = -1

            input_array = []

            i = 1
            done = False

            while True:
                next_move, last_move_was_empty_cancel = parser.input_for_move(move_id, previous_move_id)
                next_move = str(next_move)

                if last_move_was_empty_cancel:
                    input_array[-1] = ''

                input_array.append(next_move)

                if parser.can_be_done_from_neutral(move_id):
                    break

                while True:
                    old_player = self.get(is_p1, i)
                    i += 1
                    if old_player is None:
                        done = True
                        break
                    if old_player.move_id != move_id:
                        previous_move_id = move_id
                        move_id = old_player.move_id
                        break
                if done:
                    break

            clean_input_array = reversed([a for a in input_array if len(a) > 0])
            return ','.join(clean_input_array)
        else:
            return 'N/A'

    def was_just_floated(self, is_p1):
        player = self.get(is_p1, 1)
        if player is None:
            return False
        return player.is_jump

    def is_starting_attack(self, is_p1):
        player = self.get(is_p1, 1)
        if player is not None and player.startup != 0:
            if player.startup != 0 and player.move_timer == player.startup:
                previous_player = self.get(is_p1, 2)
                if previous_player is not None and previous_player.move_timer != player.move_timer:
                    return True
        return False
