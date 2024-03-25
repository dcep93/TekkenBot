set -euo pipefail

cd TekkenBot
pip install pyinstaller
python -m PyInstaller --debug noarchive --clean --hidden-import json --hidden-import _bootlocale --noconfirm --onefile --windowed --clean --icon=assets/img/tekken_bot_close.ico --name TekkenBotPrime main.py

mv dist/TekkenBotPrime ./TekkenBotPrime.exe
rm -rf dist
