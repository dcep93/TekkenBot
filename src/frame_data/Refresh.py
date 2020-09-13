import sys

from . import Database

def refresh():
    for ch in Database.Characters:
        refresh_ch(ch)

def refresh_ch(ch):
    print(ch)
