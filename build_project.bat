::get pyinstaller if you haven't already!
::pip install pyinstaller
pyinstaller --windowed --clean --icon=src/assets/tekken_bot_close.ico --add-data src/assets;src/assets  --name TekkenBotPrime src/main.py
pause