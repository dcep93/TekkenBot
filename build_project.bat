::get pyinstaller if you haven't already!
::pip install pyinstaller
del TekkenBotPrime.exe
rmdir /S /Q dist
pyinstaller --noconfirm --onefile --windowed --clean --icon=assets/img/tekken_bot_close.ico --name TekkenBotPrime main.py
copy dist\TekkenBotPrime.exe .\TekkenBotPrime.exe
