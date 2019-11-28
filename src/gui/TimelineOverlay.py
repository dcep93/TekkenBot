from . import Overlay
from tkinter import *
from tkinter.ttk import *



class TextRedirector(object):
    def __init__(self, canvas, height):
        self.canvas = canvas
        self.h = height

        self.p1_color = 'hot pink'
        self.p2_color = 'CadetBlue1'

        self.FRAMES = 360

        self.round_start(0)



    def round_start(self, round_number):
        self.base_x = self.FRAMES * (round_number + 1)
        self.p1_x0 = 0
        self.p1_y0 = 0
        self.p2_x0 = 0
        self.p2_y0 = 0

    def write(self, str):
        if 'HIT' in str:
            if '!ROUND' in str:
                round_number = int(str.split('|')[1])
                if round_number == 0:
                    self.canvas.delete('lines')
                self.round_start(round_number)

            else:
                split_player = str.split(':')
                player = split_player[0]
                is_p1 = 'p1' in player

                args = split_player[1].split('|')

                type = args[0]
                damage = int(args[1])
                start_frame = int(args[3])
                end_frame = int(args[4])
                command = args[5]

                if end_frame > start_frame: #sometimes we get data from when the fight was already reset
                    end_frame = start_frame

                if is_p1:
                    x0, y0 = self.p1_x0, self.p1_y0
                    line_color = self.p1_color
                else:
                    x0, y0 = self.p2_x0, self.p2_y0
                    line_color = self.p2_color

                x1 = self.base_x - (start_frame / 10)
                x2 = self.base_x - (end_frame / 10)

                y1 = y0
                y2 = min(self.h, y0 + (damage / 2))

                self.canvas.create_line([(x0, y0), (x1, y1), (x2, y2)], fill=line_color, tag="lines")

                if is_p1:
                    self.p1_x0, self.p1_y0 = x2, y2
                else:
                    self.p2_x0, self.p2_y0 = x2, y2


class TimelineOverlay(Overlay.Overlay):
    def __init__(self, master, launcher):


        Overlay.Overlay.__init__(self, master, (1800, 86), "Tekken Bot: Timeline Overlay")

        #self.launcher = FrameDataLauncher(self.enable_nerd_data)
        self.launcher = launcher

        self.canvas = Canvas(self.toplevel, width=self.w, height=self.h, bg='black', highlightthickness=0, relief='flat')
        # figures out how the canvas sits in the window
        self.canvas.pack()


        self.redirector = TextRedirector(self.canvas, self.h)

        #dataList= [(12, 56), (20, 94), (33, 98), (45, 12), (61, 18),
        #                (75, 16), (98, 0)]



        # and some dots at the corner points
        #for (xs, ys) in dataList:
        #    canvas.create_oval(xs - 2, ys - 2, xs + 2, ys + 2, width=1,
        #                       outline='black', fill='SkyBlue2')

