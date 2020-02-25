::get pyinstaller if you haven't already!
::pip install pyinstaller
pyinstaller --noconfirm --onefile --console --clean --icon=src/export/assets/tekken_bot_close.ico --name TekkenBotPrime src/main.py
cp -r src/export dist/export
