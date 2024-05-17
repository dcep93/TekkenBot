from ..frame_data import Entry
from ..game_parser import GameReader, GameSnapshot, MoveInfoEnums
from ..gui import TekkenBot420
from ..record import Record

import typing


class GameLog:

    def __init__(self) -> None:
        self.obj: typing.Any = None
        self.state_log: typing.List[GameSnapshot.GameSnapshot] = []

    def get(self, is_p1: bool, frames_ago: int = 0) -> GameSnapshot.PlayerSnapshot:
        if len(self.state_log) <= frames_ago:
            return None  # type: ignore
        state = self.state_log[-1-frames_ago]
        return state.p1 if is_p1 else state.p2

    def update(self, game_reader: GameReader.GameReader) -> None:
        overlay = TekkenBot420.TekkenBot420.t.overlay
        overlay.update_location(game_reader)
        game_snapshot = game_reader.get_updated_state(0)

        if game_snapshot is not None:
            # we don't run perfectly in sync, if we get back the same frame, throw it away
            if len(self.state_log) == 0 or game_snapshot.frame_count != self.state_log[-1].frame_count:
                if len(self.state_log) > 0:
                    frames_lost = game_snapshot.frame_count - \
                        self.state_log[-1].frame_count - 1
                    missed_states = min(7, frames_lost)

                    for i in range(missed_states):
                        dropped_state = game_reader.get_updated_state(
                            missed_states - i)
                        if dropped_state is not None:
                            self.track_gamedata(dropped_state)

                self.track_gamedata(game_snapshot)

    def track_gamedata(self, game_snapshot: GameSnapshot.GameSnapshot) -> None:
        overlay = TekkenBot420.TekkenBot420.t.overlay
        if len(self.state_log) > 0 and self.state_log[-1].frame_count == game_snapshot.frame_count:
            return

        self.state_log.append(game_snapshot)

        obj = None  # for debugging
        if obj != self.obj:
            print(game_snapshot.frame_count, obj)
            self.obj = obj

        overlay.update_state(self)
        Record.record_if_activated()

        if len(self.state_log) > 3000:
            self.state_log.pop(0)

    def is_starting_attack(self, is_p1: bool) -> bool:
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

    def get_throw_break(self, is_p1: bool) -> typing.Optional[str]:
        state = self.get(not is_p1)
        throw_tech = state.throw_tech
        if throw_tech in [MoveInfoEnums.ThrowTechs.NONE, MoveInfoEnums.ThrowTechs.BROKEN_ThrowTechs]:
            return None

        prev_state = self.get(is_p1, 2)
        if prev_state is None:
            return None
        move_id = prev_state.move_id
        current_buttons = self.get(not is_p1, 1).input_button.name
        if '1' not in current_buttons and '2' not in current_buttons:
            if move_id != self.get(is_p1, 1).move_id:
                return 'br: %s' % throw_tech.name
            return None

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
                return None
            i += 1
        raise Exception("get_throw_break")

    def just_lost_health(self, is_p1: bool) -> bool:
        prev_state = self.get(is_p1, 2)
        if prev_state is None:
            return False
        next_state = self.get(is_p1, 1)
        return next_state.damage_taken != prev_state.damage_taken

    def get_time_str(self, entry: Entry.Entry, is_p1: bool) -> str:
        state = self.get(not is_p1, 1)
        if state.move_timer != 0:
            return str(-state.move_timer)
        if state.stun_state not in [
            MoveInfoEnums.StunStates.NONE,
            MoveInfoEnums.StunStates.DOING_THE_HITTING,
        ]:
            return state.stun_state.name
        for age in range(2, 30):
            s = self.get(not is_p1, age)
            if s is None:
                break
            if s.stun_state != state.stun_state:
                old = self.state_log[-age].frame_count
                if state.stun_state == MoveInfoEnums.StunStates.NONE:
                    return str(old)
                if state.stun_state == MoveInfoEnums.StunStates.DOING_THE_HITTING:
                    return str(-old)
        return "?"
