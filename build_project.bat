::get pyinstaller if you haven't already!
::pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --clean --icon=src/export/assets/tekken_bot_close.ico --name TekkenBotPrime src/main.py
cp dist/TekkenBotPrime.exe ./
