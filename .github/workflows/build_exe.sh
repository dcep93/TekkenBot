set -euo pipefail

pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --clean --icon=assets/img/tekken_bot_close.ico --name TekkenBotPrime main.py
ls dist
