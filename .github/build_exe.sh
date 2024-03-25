pwd
pip install pyinstaller
ls
python -m PyInstaller --noconfirm --onefile --windowed --clean --icon=assets/img/tekken_bot_close.ico --name TekkenBotPrime main.py
ls
mv dist/TekkenBotPrime.exe ./TekkenBotPrime.exe
ls
# TODO release
