from ..game_parser import GameReader, GameSnapshot
from ..misc import Flags

import pickle
import signal
import sys
import time
import typing

# this file is used to record a bug and quickly replay it so it can be fixed

class Recorder(GameReader.GameReader):
    def __init__(self) -> None:
        super().__init__()
        self.active: bool = False
        self.all_datas: typing.List[typing.Tuple[float, typing.List[GameSnapshot.GameSnapshot]]] = []
        self.num_datas: int = 0
        signal.signal(signal.SIGINT, lambda _,__: self.save_and_quit())

    def reset(self, active: typing.Optional[bool]=None) -> None:
        if active is not None:
            self.active = active
        self.all_datas = []
        self.num_datas = 0

    def get_updated_state(self, rollback_frame: int) -> typing.Optional[GameSnapshot.GameSnapshot]:
        game_snapshot = super().get_updated_state(rollback_frame)
        if game_snapshot is not None and self.active:
            self.record_data(rollback_frame == 0, game_snapshot)
        return game_snapshot

    def record_data(self, new_update: bool, game_snapshot: GameSnapshot.GameSnapshot) -> None:
        self.num_datas += 1
        if new_update:
            now = time.time()
            self.all_datas.append((now, [game_snapshot]))
        else:
            self.all_datas[-1][1].append(game_snapshot)

    def dump(self) -> None:
        self.active = False
        print('writing', self.num_datas, len(self.all_datas))
        with open(Flags.Flags.pickle_dest, 'wb') as fh:
            pickle.dump(self.all_datas, fh)
        self.reset()

    def save_and_quit(self) -> None:
        self.dump()
        sys.exit(0)

class Reader(Recorder):
    def __init__(self) -> None:
        super().__init__()
        print('loading', Flags.Flags.pickle_src, Flags.Flags.fast)
        with open(Flags.Flags.pickle_src, 'rb') as fh:
            self.all_datas = pickle.load(fh)

        if not self.all_datas:
            raise Exception("no data in pickle")

        self.offset: float = time.time() - self.load()

    def load(self) -> float:
        timestamp, self.datas = self.all_datas.pop(0)
        return timestamp

    def get_update_wait_ms(self, _: float) -> int:
        if len(self.all_datas) == 0:
            print("done with pickle")
            if Flags.Flags.fast:
                sys.exit(0)
            return -1

        next_timestamp = self.load()
        if Flags.Flags.fast:
            return 0
        wait_s = next_timestamp + self.offset - time.time()
        wait_ms = max(int(wait_s * 1000), 0)
        return wait_ms

    def get_updated_state(self, _: int) -> typing.Optional[GameSnapshot.GameSnapshot]:
        if len(self.datas) == 0:
            return None
        return self.datas.pop(0)
