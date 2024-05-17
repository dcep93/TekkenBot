set -euo pipefail

cd TekkenBot420
pip install pyinstaller
python -m PyInstaller \
    --debug noarchive \
    --clean \
    --hidden-import json \
    --hidden-import _bootlocale \
    --noconfirm \
    --onefile \
    --windowed \
    --clean \
    --icon=assets\\img\\favicon.ico \
    --name TekkenBot420 \
    main.py

mv dist\\TekkenBot420 ..\\TekkenBot420.exe
rm -rf dist
