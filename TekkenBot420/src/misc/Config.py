from ..misc import Path

import json

with open(Path.path("config/config.json")) as fh:
    config = json.load(fh)
