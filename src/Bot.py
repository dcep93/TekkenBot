"""
The parent class for all bots.

"""

class Bot:
    def __init__(self, botCommands):
        self.botCommands = botCommands


    def Update(self, gameState):
        pass
