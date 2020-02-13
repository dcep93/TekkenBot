# TekkenBot

AI and tools for playing and understanding Tekken 7.

Created by roguelike2d. Maintained by the community.

## Related

1. The original repository:
    - WAZAAAAA0: [https://github.com/WAZAAAAA0/TekkenBot](https://github.com/WAZAAAAA0/TekkenBot)
2. Check out this additional fork for new TekkenBotPrime features:
    - compsyguy: [https://github.com/compsyguy/TekkenBot/](https://github.com/compsyguy/TekkenBot/)
3. Check out this additional fork for new TekkenBotPrime features:
    - Alchemy-Meister: [https://github.com/Alchemy-Meister/TekkenBot/](https://github.com/Alchemy-Meister/TekkenBot/)

## New Features in this fork

### Code

-   [x] The main purpose of this project was to simplify the code so that other devs can more easily iterate or fork
-   [x] I'll watch the github issues tab for improvements/bug fixes when they're posted

### Frame Data

-   [x] Characters' frame data is imported from rbnorway - when that move is detected, its data is shown instead of reading game state
-   [x] When an unknown move is performed, its data is remembered so that next time there are fewer 'unknown' values
-   [x] Remaining opponent health is displayed so you don't have to guess what will kill them

### TODO

-   [ ] Throws - how to break and importing from rbnorway
-   [ ] What do do about moves that have more than one hit for a single input
-   [ ] Package into exe
-   [ ] Fix punish column
