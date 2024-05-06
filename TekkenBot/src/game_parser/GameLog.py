from . import GameReader
from game_parser import MoveInfoEnums
from record import Record

class GameLog:
    obj = None

    def __init__(self):
        self.state_log = []

    def get(self, is_p1, frames_ago=0):
        if len(self.state_log) <= frames_ago:
            return None
        state = self.state_log[-1-frames_ago]
        return state.p1 if is_p1 else state.p2

    def update(self, game_reader, overlay):
        overlay.update_location(game_reader)
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
                            self.track_gamedata(dropped_state, overlay)

                self.track_gamedata(game_snapshot, overlay)

    def track_gamedata(self, game_snapshot, overlay):
        if len(self.state_log) > 0 and self.state_log[-1].frame_count == game_snapshot.frame_count:
            return

        self.state_log.append(game_snapshot)

        obj = None # for debugging
        obj = [i.complex_state for i in [game_snapshot.p1, game_snapshot.p2]]
        if obj != self.obj:
            print(game_snapshot.frame_count, obj)
            self.obj = obj

        overlay.update_state(self)
        Record.record_if_activated()

        if len(self.state_log) > 3000:
            self.state_log.pop(0)

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
        state = self.get(not is_p1)
        throw_tech = state.throw_tech
        if throw_tech in [MoveInfoEnums.ThrowTechs.NONE, MoveInfoEnums.ThrowTechs.BROKEN_ThrowTechs]:
            return False
        
        prev_state = self.get(is_p1, 2)
        if prev_state is None: return False
        move_id = prev_state.move_id
        current_buttons = self.get(not is_p1, 1).input_button.name
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
                throw_break_string = '%s/%s %d' % (break_string, correct, i-2)
                return throw_break_string
            buttons = state.input_button.name
            if '1' in buttons or '2' in buttons:
                return False
            i += 1
        raise Exception("get_throw_break")

    def just_lost_health(self, is_p1):
        prev_state = self.get(is_p1, 2)
        if prev_state is None:
            return False
        next_state = self.get(is_p1, 1)
        return next_state.damage_taken != prev_state.damage_taken

    def get_free_frames(self, is_p1):
        return 0
