::get pyinstaller if you haven't already!
::pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --clean --icon=asssets/img/tekken_bot_close.ico --name TekkenBotPrime main.py
cp dist/TekkenBotPrime.exe ./
