::get pyinstaller if you haven't already!
::pip install pyinstaller
rm -f TekkenBotPrime.exe && rm -rf dist && pyinstaller --noconfirm --onefile --windowed --clean --icon=assets/img/tekken_bot_close.ico --name TekkenBotPrime main.py && cp dist/TekkenBotPrime.exe ./
