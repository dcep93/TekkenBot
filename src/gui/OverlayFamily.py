from . import CommandInputOverlay, FrameDataOverlay

member_classes = [FrameDataOverlay.FrameDataOverlay, CommandInputOverlay.CommandInputOverlay]

class OverlayFamily:
    def __init__(self):
        self.overlays = {mc: mc() for mc in member_classes}

    def update(self, game_reader, game_log):
        for overlay in self.overlays.values():
            overlay.update(game_reader, game_log)
