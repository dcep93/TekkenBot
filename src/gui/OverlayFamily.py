from . import CommandInputOverlay, FrameDataOverlay

member_classes = [FrameDataOverlay.FrameDataOverlay, CommandInputOverlay.CommandInputOverlay]

class OverlayFamily:
    def __init__(self):
        self.overlays = []
        for mc in member_classes:
            self.overlays.append(mc())

    def update(self):
        for overlay in self.overlays:
            overlay.update()
