# TekkenBot420

GUI to study frame data while in game.

Created by roguelike2d. Maintained by the community.

### Note: Do not move the exe to a different folder - it needs to be able to see the 'assets' directory. Create a shortcut if you want to have an easy reference file.

### You can run the code yourself using main.py, or unzip the tar from the latest [release](https://github.com/dcep93/TekkenBot/releases) and run the exe

## Related

1. The original repository:
   - WAZAAAAA0: [https://github.com/WAZAAAAA0/TekkenBot](https://github.com/WAZAAAAA0/TekkenBot)
2. Check out this additional fork for new TekkenBotPrime features:
   - compsyguy: [https://github.com/compsyguy/TekkenBot/](https://github.com/compsyguy/TekkenBot/)
3. Check out this additional fork for new TekkenBotPrime features:
   - Alchemy-Meister: [https://github.com/Alchemy-Meister/TekkenBot/](https://github.com/Alchemy-Meister/TekkenBot/)

## New Features in this fork

### Code

- [x] The main purpose of this project was to simplify the code so that other devs can more easily iterate or fork
- [x] I'll watch the github issues tab for improvements/bug fixes when they're posted
- [x] Information about data displayed is briefly described in [Entry.py](https://github.com/dcep93/TekkenBot/blob/master/TekkenBot420/src/frame_data/Entry.py)
- [x] For simplicity, you can easily add custom code to [Hook.py](https://github.com/dcep93/TekkenBot/blob/master/TekkenBot420/src/frame_data/Hook.py)
- [x] When there is a code or config change, automatically builds an exe file available on the [releases page](https://github.com/dcep93/TekkenBot/releases)

### Database

- [x] Since we can no longer parse the move list from the game memory, we record information in assets/database/frame_data, which is utilized in future matches. It's probably a good idea to wipe this folder when there is a patch, otherwise it's liable to report old info.
- [x] It also records lots of data to assets/database/oppoent_moves, which I think could be used to get some insights in aggregate. I'll probably do a reddit post someday, describing most commonly used moves from each character.

### Record/Replay

- [ ] TODO this is horribly broken at the moment
- [x] Record and replay feature built. Intended for combo construction/hypothetical scenario validation. Could potentially be used for cheating, but would need a nefarious coder to implement, as the current iteration requires clicking on the button, and there is a delay.
- [x] Recording works for both players to allow easy creation, editing, and sharing of TAS duels.

### update_memory_address.py

- [x] When there is a Tekken8 patch, config settings in memory_address.ini break. Open practice mode as p1 Jin vs Kazuya and run `python update_memory_address.py` to automatically determine new address locations and update the file. This should take about 10 minutes, but might need you to close Tekken and reopen it, in case a problem is found. Once the file is committed to the repo, github actions will automatically rebuild a package for non-coders to download.
