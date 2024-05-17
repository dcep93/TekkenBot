from ..gui import TekkenBot420
from ..misc import Flags, recorded_sha

import sys
import traceback


def main() -> None:
    print("https://github.com/dcep93/TekkenBot")
    print("sha:", recorded_sha.sha)
    Flags.handle()
    app = TekkenBot420.TekkenBot420()
    app.mainloop()
