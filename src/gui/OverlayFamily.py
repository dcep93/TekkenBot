from . import CommandInputOverlay, FrameDataOverlay

member_classes = [
    FrameDataOverlay.FrameDataOverlay,
    # CommandInputOverlay.CommandInputOverlay
]

class OverlayFamily:
    def __init__(self):
        self.overlays = {mc: mc() for mc in member_classes}

    def update_state(self, game_log):
        for overlay in self.overlays.values():
            overlay.update_state(game_log)

    def update_location(self, game_reader):
        for overlay in self.overlays.values():
            overlay.update_location(game_reader)
