from gui import TekkenBotPrime
from misc import Flags

def main():
    Flags.handle()
    app = TekkenBotPrime.TekkenBotPrime()
    app.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
    input()
