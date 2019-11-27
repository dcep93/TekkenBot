"""
A GUI that launches the frame trap bot, to practice frame traps on. The move the bot does out of block can be changed.

"""


from tkinter import *
from tkinter.ttk import *
from _TekkenBotLauncher import TekkenBotLauncher
from BotFrameTrap import BotFrameTrap
import sys


class GUI_FrameTrapBot(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.wm_title("Tekken Bot")
        self.geometry(str(720) + 'x' + str(720))

        #self.configure(background='white')
        #self.wm_attributes("-transparentcolor", "white")
        #self.attributes("-alpha", "0.80")

        Style().theme_use('alt')
        self.DoStyleNotebook()
        #self.s = Style()
        #self.s.configure('TNotebook', background='black')

        self.controller_select_radio = self.GetRadiobuttonFrame()

        self.note = Notebook(self, width=999, height=50)

        self.frame_bot = FrameTrapBotTab(self.note)

        self.dummy_tab1 = Frame(self.note)
        self.dummy_tab2 = Frame(self.note)
        self.dummy_tab3 = Frame(self.note)

        Grid.columnconfigure(self, 0, weight=0)
        Grid.columnconfigure(self, 1, weight=0)
        #Grid.columnconfigure(self, 2, weight=0)
        Grid.rowconfigure(self, 0, weight=0)
        Grid.rowconfigure(self, 1, weight=1)

        self.frame_bot.frame.grid(row=0, column=0)

        self.note.add(self.frame_bot.frame, text = "Frame Trap Bot")
        self.note.add(self.dummy_tab1, text="dummy bot")
        self.note.add(self.dummy_tab2, text="dummy bot")
        self.note.add(self.dummy_tab3, text="dummy bot")

        self.controller_select_radio.grid(row=0, column=0, sticky=W)
        self.note.grid(row=1, column=0, columnspan=2, sticky=N+S+E+W)


    def DoStyleNotebook(self):
        myTabBarColor = 'black'
        myActiveTabBackgroundColor = 'gray22'
        myActiveTabForegroundColor = 'green'
        myTabBackgroundColor = 'black'
        myTabForegroundColor = 'green'

        Style().configure("TNotebook", background=myTabBarColor, foreground=myTabBarColor);
        Style().map("TNotebook.Tab", background=[("selected", myActiveTabBackgroundColor)],
                    foreground=[("selected", myActiveTabForegroundColor)]);
        Style().configure("TNotebook.Tab", background=myTabBackgroundColor, foreground=myTabForegroundColor,  font=("Consolas", 18));


    def GetRadiobuttonFrame(self):
        player_var = IntVar()
        radio_frame = Frame(self)
        radio_label = Label(radio_frame, text="Bot Controls:")
        radio_player_2 = Radiobutton(radio_frame, text='Player 2 (right side)', variable=player_var, value=2)
        radio_player_1 = Radiobutton(radio_frame, text='Player 1 (left side)', variable=player_var, value=1)
        radio_label.grid(row=0, column = 0, sticky=W)
        radio_player_2.grid(row=1, column=1, sticky=W)
        radio_player_1.grid(row=1, column=0, sticky=W)
        #cell.grid(row=2, column=1, sticky=W)
        return radio_frame

    def update_launcher(self):
        self.frame_bot.update()
        self.after(7, self.update_launcher)

class FrameTrapBotTab():
    def __init__(self, notebook):
        self.frame = Frame(notebook)
        self.launcher = TekkenBotLauncher(BotFrameTrap, False)

        self.notation_display = NotationDisplayEntry(self.frame, self.launcher.GetBot())
        self.notation_display.frame.grid(row=0, column=0, sticky=N + S + E + W)

        Style().configure('TFrame', background='black')



    def update(self):
        self.launcher.GetBot().SetFrameTrapCommandFromNotationString(self.notation_display.entry_var.get())
        self.launcher.Update()

class NotationDisplayEntry():
    def __init__(self, parent, bot):
        self.bot = bot
        self.frame = Frame(parent)
        self.entry_var = StringVar()
        self.entry_var.set("+4")
        self.entry = Entry(self.frame, textvariable=self.entry_var, font=("Consolas", 44))
        self.entry.configure(state="normal")

        self.recording = False
        self.button_record = Button(self.frame, text="Record")
        self.button_record.bind("<Button-1>", self.record_button)

        self.button_record.grid(row=1, column=0, sticky=W)
        self.entry.grid(row=0, column=0, sticky=N + S + E + W)

    def record_button(self, event):
        if not self.recording:
            self.bot.Record()
            print('pressed record')
        else:
            notation = self.bot.Stop()
            self.entry_var.set(notation)
            print('stopped record')

        self.recording = not self.recording

if __name__ == '__main__':
    app = GUI_FrameTrapBot()
    app.update_launcher()
    app.mainloop()