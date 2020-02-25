::get pyinstaller if you haven't already!
::pip install pyinstaller
pyinstaller --onefile --clean --icon=src/export/assets/tekken_bot_close.ico --add-data src/export;src/export --name TekkenBotPrime src/main.py
pause