# TekkenBot

GUI to study frame data while in game.

Created by roguelike2d. Maintained by the community.

### Note: Do not move the exe to a different folder - it needs to be able to see the 'assets' directory. Create a shortcut if you want to have an easy reference file.

## Related

1. The original repository:
   - WAZAAAAA0: [https://github.com/WAZAAAAA0/TekkenBot](https://github.com/WAZAAAAA0/TekkenBot)
2. Check out this additional fork for new TekkenBotPrime features:
   - compsyguy: [https://github.com/compsyguy/TekkenBot/](https://github.com/compsyguy/TekkenBot/)
3. Check out this additional fork for new TekkenBotPrime features:
   - Alchemy-Meister: [https://github.com/Alchemy-Meister/TekkenBot/](https://github.com/Alchemy-Meister/TekkenBot/)

## New Features in this fork

### Auto build and release

- [x] When there is a code or config change, automatically builds an exe file available on the [releases page](https://github.com/dcep93/TekkenBot/releases).

### Code

- [x] The main purpose of this project was to simplify the code so that other devs can more easily iterate or fork
- [x] I'll watch the github issues tab for improvements/bug fixes when they're posted

### Record/Replay

- [x] Record and replay feature built. Intended for combo construction/hypothetical scenario validation. Could potentially be used for cheating, but would need a nefarious coder to implement, as the current iteration requires clicking on the button, and there is a delay.
- [x] Recording works for both players to allow easy creation, editing, and sharing of TAS duels.

### update_memory_address.py

- [ ] When there is a Tekken8 patch, config settings in memory_address.ini break. Open practice mode and run `python update_memory_address.py` to automatically determine new address locations and update the file. Once the file is committed to the repo, github actions will automatically rebuild a package for non-coders to download.

### TODO

- [ ] fresh images
- [ ] documentation how-to
- [ ] autobuild memory_address.ini on patch
- [ ] get_free_frames: notify interrupts like drag's d+3,2,1+2
- [ ] mypy typechecking
