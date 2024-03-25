set -euo pipefail

cd TekkenBot
pip install pyinstaller
python -m PyInstaller --debug all --noconfirm --onefile --windowed --clean --icon=assets/img/tekken_bot_close.ico --name TekkenBotPrime main.py

mv dist/TekkenBotPrime ./TekkenBotPrime.exe

cd ../..

zip -r TekkenBotPrime.zip TekkenBot

mv TekkenBotPrime.zip TekkenBot
