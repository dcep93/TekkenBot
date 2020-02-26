::get pyinstaller if you haven't already!
::pip install pyinstaller
<<<<<<< HEAD
pyinstaller --noconfirm --onefile --windowed --clean --icon=src/export/assets/tekken_bot_close.ico --name TekkenBotPrime src/main.py
cp -r src/export dist/export
=======
pyinstaller --noconfirm --onefile --windowed --clean --icon=asssets/img/tekken_bot_close.ico --name TekkenBotPrime main.py
cp dist/TekkenBotPrime.exe ./
>>>>>>> 597e52dcf62a81754aa99e336fb8b5d14740bd50
