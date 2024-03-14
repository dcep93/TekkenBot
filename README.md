# TekkenBot

GUI to study frame data while in game.

Created by roguelike2d. Maintained by the community.

### Note: Do not move the exe to a different folder - it needs to be able to see the 'assets' directory.

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

### Frame Data

- [x] Characters' frame data is imported from tekken8framedata.com - when that move is detected, its data is shown instead of reading game state
- [x] When an unknown move is performed, its data is remembered so that next time there are fewer 'unknown' values
- [x] Remaining opponent health is displayed so you don't have to guess what will kill them
- [x] Tells you what break a throw is, along with what and when the user attempted to break, even if the break is late.
- [x] Includes the relative frame numbers to precisely compare events.

### Record/Replay

- [x] Record and replay feature built. Intended for combo construction/hypothetical scenario validation. Could potentially be used for cheating, but would need a nefarious coder to implement, as the current iteration requires mouse moving and such.
- [x] Recording works for both players to allow easy creation, editing, and sharing of TAS duels.
- [x] Shows the distance from 2.00 the player is after the recording finishes. Can be used for kbd practice.

### TODO

- [ ] fresh images
- [ ] autobuild exe and release on commit if version is updated!
- [ ] documentation
- [ ] reduce noise from strings
- [ ] get_update_wait_ms
