"""
A stop gap for testing punisher bot until we get a nicer, unifed bot interface

"""


from tkinter import *
from tkinter.ttk import *
from _TekkenBotLauncher import TekkenBotLauncher
from BotFrameTrap import BotFrameTrap
from BotPunisher import BotPunisher
import sys


class GUI_PunisherBot(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.wm_title("Punisher Bot")
        self.geometry(str(720) + 'x' + str(720))

        Style().theme_use('alt')

        self.launcher = TekkenBotLauncher(BotPunisher, False)

    def update_launcher(self):
        self.update()
        self.after(5, self.update_launcher)

    def update(self):
        self.launcher.Update()

if __name__ == '__main__':
    app = GUI_PunisherBot()
    app.update_launcher()
    app.mainloop()