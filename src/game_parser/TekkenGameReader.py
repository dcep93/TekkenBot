from . import GameReader

for n,c in GameReader.__dict__.items():
    if type(c) is type(type):
        vars()[n] = c
