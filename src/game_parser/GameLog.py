from . import GameReader
from game_parser import MoveInfoEnums
from record import Record

class GameLog:
    obj = None
    is_player_player_one = True

    def __init__(self):
        self.state_log = []

    def get(self, is_p1, frames_ago=0):
        if len(self.state_log) <= frames_ago:
            return None
        state = self.state_log[-1-frames_ago]
        return state.p1 if is_p1 else state.p2

    def update(self, game_reader, overlay_family):
        overlay_family.update_location(game_reader)
        game_snapshot = game_reader.get_updated_state(0)

        if game_snapshot is not None:
            # we don't run perfectly in sync, if we get back the same frame, throw it away
            if len(self.state_log) == 0 or game_snapshot.frame_count != self.state_log[-1].frame_count:
                if len(self.state_log) > 0:
                    frames_lost = game_snapshot.frame_count - self.state_log[-1].frame_count - 1
                    missed_states = min(7, frames_lost)

                    for i in range(missed_states):
                        dropped_state = game_reader.get_updated_state(missed_states - i)
                        if dropped_state is not None:
                            self.track_gamedata(dropped_state, overlay_family)

                self.track_gamedata(game_snapshot, overlay_family)

    def track_gamedata(self, game_snapshot, overlay_family):
        if len(self.state_log) > 0 and self.state_log[-1].frame_count == game_snapshot.frame_count:
            return

        self.is_player_player_one = game_snapshot.is_player_player_one

        self.state_log.append(game_snapshot)

        obj = None # for debugging
        if obj != self.obj:
            print(game_snapshot.frame_count, obj)
            self.obj = obj

        overlay_family.update_state(self)
        Record.record_if_activated()

        if len(self.state_log) > 300:
            self.state_log.pop(0)

    def get_current_move_string(self, is_p1):
        state = self.get(is_p1, 1)
        move_id = state.move_id
        if state.movelist_parser is not None:
            return self.deduce_move_string_from_parser(is_p1, move_id, parser)
        return self.deduce_move_string_from_inputs(is_p1, move_id)

    def deduce_move_string_from_parser(self, is_p1, move_id, parser):
        previous_move_id = -1

        input_array = []

        i = 1
        done = False

        for _ in range(1000):
            next_move, last_move_was_empty_cancel = parser.input_for_move(move_id, previous_move_id)
            next_move = str(next_move)

            if last_move_was_empty_cancel:
                input_array[-1] = ''

            input_array.append(next_move)

            if parser.can_be_done_from_neutral(move_id):
                break

            for _ in range(1000):
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

        clean_input_array = tuple(reversed([a for a in input_array if len(a) > 0]))
        if clean_input_array != ("N/A",):
            string = ','.join(clean_input_array)
            return '$ %s' % string

    def deduce_move_string_from_inputs(self, is_p1, move_id):
        for i in range(1, len(self.state_log)):
            state = self.get(is_p1, i)
            if state is None:
                break
            if state.move_id != move_id:
                input_string = state.get_input_as_string()
                return '* %s' % input_string
        return "N/A"

    def was_just_floated(self, is_p1):
        player = self.get(is_p1, 1)
        if player is None:
            return False
        return player.is_jump

    def is_starting_attack(self, is_p1):
        before = 2
        player = self.get(is_p1, before)
        if player is not None and player.startup != 0:
            cur_frame_count = self.state_log[-1].frame_count
            prev_frame_count = self.state_log[-2].frame_count
            dropped_frames = cur_frame_count - prev_frame_count - 1
            diff = player.startup - player.move_timer - 1
            if diff >= 0 and diff <= dropped_frames:
                previous_player = self.get(is_p1, before + 1)
                if previous_player is not None and previous_player.move_timer < player.move_timer:
                    return True
        return False

    def get_throw_break(self, is_p1):
        frames_to_break = 20
        state = self.get(not is_p1)
        throw_tech = state.throw_tech
        if throw_tech in [MoveInfoEnums.ThrowTechs.NONE, MoveInfoEnums.ThrowTechs.BROKEN_ThrowTechs]:
            return False
        
        prev_state = self.get(is_p1, 2)
        if prev_state is None: return False
        move_id = prev_state.move_id
        current_buttons = self.get(not is_p1, 1).get_input_state()[1].name
        if '1' not in current_buttons and '2' not in current_buttons:
            if move_id != self.get(is_p1, 1).move_id:
                return 'br: %s' % throw_tech.name
            return False

        correct = state.throw_tech.name

        i = 2
        for _ in range(1000):
            state = self.get(not is_p1, i)
            if state == None or move_id != self.get(is_p1, i).move_id:
                relevant = current_buttons.replace('x3', '').replace('x4', '')
                throw_break = MoveInfoEnums.InputAttackCodes[relevant]
                break_string = throw_break.name.replace('x', '')
                throw_break_string = 'br: %s/%s %d/%d' % (break_string, correct, i-2, frames_to_break)
                return throw_break_string
            buttons = state.get_input_state()[1].name
            if '1' in buttons or '2' in buttons:
                return False
            i += 1
        print("impossible a")

    def just_lost_health(self, is_p1):
        prev_state = self.get(is_p1, 2)
        if prev_state is None:
            return False
        next_state = self.get(is_p1, 1)
        return next_state.damage_taken != prev_state.damage_taken
