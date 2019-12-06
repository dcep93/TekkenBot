from ButtonCommandEnum import Command


INPUT_DELAY = 4

def ParseMoveList(moveList:str):
    commands = []
    tempTiming = None
    timingOccurances = 0

    for i, moveOrTiming in enumerate(moveList.split(',')):
        notationResult = ConvertNotationToCommands(moveOrTiming.strip(), timingOccurances)
        timingOccurances = notationResult[1]
        commands += notationResult[0]

    return commands

def ConvertNotationToCommands(notation:str, timingOccurances:int):
    commands = []
    occurances = 0
    attackCommands = GetAttackCommands(notation)
    if 'recovery' in notation:
        commands.append((Command.FullRecovery, 0))
    elif 'S!' in notation or 'L!' in notation:
        commands.append((Command.FullRecovery, 0))
    elif 'nextmove' in notation:
        commands.append((Command.Nextmove, 0))
    elif 'startup' in notation:
        commands.append((Command.Startupmove, 0))
    elif 'debug' in notation:
        commands.append((Command.HoldBack, 1))
        commands.append((Command.HoldDown, 2))
        commands.append((Command.ReleaseBack, 2))
        commands.append((Command.HoldForward, 2))
        commands += attackCommands
        commands.append((Command.ReleaseAll, 2))
    elif 'dp' in notation:
        commands.append((Command.TapForward, 1))
        commands.append((Command.TapDown, 1))
        commands.append((Command.TapForward, 1))
        commands.append((Command.TapDown, 1))
        commands += attackCommands
    elif 'qcb' in notation:
        commands.append((Command.HoldDown, 2))
        commands.append((Command.HoldBack, 2))
        commands.append((Command.ReleaseDown, 2))
        commands += attackCommands
        commands.append((Command.ReleaseBack, 2))
    elif 'qcf' in notation:
        commands.append((Command.HoldDown, 1))
        commands.append((Command.HoldForward, 1))
        commands.append((Command.ReleaseDown, 1))
        commands += attackCommands
        commands.append((Command.ReleaseForward, 2))
    elif 'pewgf' in notation:
        commands.append((Command.TapForward, 0))
        commands.append((Command.TapDown, 2))
        commands.append((Command.TapForward, 0))
        commands += attackCommands
        commands.append((Command.ReleaseDown, 1))
    elif 'ewgf' in notation:
        commands.append((Command.TapForward, 0))
        commands.append((Command.HoldDown, 2))
        commands.append((Command.TapForward, 1))
        commands += attackCommands
        commands.append((Command.ReleaseDown, 1))
    elif 'iWS' in notation:
        commands.append((Command.HoldDown, 0))
        commands.append((Command.HoldForward, 2))
        commands.append((Command.ReleaseDown, 2))
        commands.append((Command.ReleaseForward, 0))
        commands.append((Command.Wait, 2))
        commands += attackCommands
    elif ':' in notation:
        waitFrames = int(notation.split('[')[1].split(']')[0])
        commands.append((Command.Wait, waitFrames - INPUT_DELAY))
    elif 'UF' in notation:
        commands.append((Command.HoldForward, 1))
        commands.append((Command.HoldUp, 0))
        waitFrames = int(notation.split('[')[1].split(']')[0])
        commands.append((Command.Wait, waitFrames))
        commands.append((Command.ReleaseForward, 1))
        commands.append((Command.ReleaseUp, 0))
    elif 'ff' in notation:
        commands.append((Command.TapForward, 0))
        commands.append((Command.HoldForward, 2))
        waitFrames = int(notation.split('[')[1].split(']')[0])
        commands.append((Command.Wait, 1 + waitFrames ))
        commands += attackCommands
        commands.append((Command.ReleaseForward, 1))

    elif notation.isdigit() and '+' not in notation:
        commands.append((Command.Wait, int(notation)))
    elif '>' in notation:
        occurances = notation.count('>')
        for i in range(occurances):
            if (i + timingOccurances) % 2 == 0:
                commands.append((Command.Recovery, 0))
            else:
                commands.append((Command.Nextmove, 0))
    elif 'wr' in notation:
        commands.append((Command.TapForward, 0))
        commands.append((Command.Wait, 2))
        commands.append((Command.TapForward, 0))
        commands.append((Command.Wait, 2))
        commands.append((Command.HoldForward, 0))
        waitFrames = int(notation.split('[')[1].split(']')[0])

        commands.append((Command.Wait, 2 + waitFrames))
        commands += attackCommands
        commands.append((Command.ReleaseForward, 2))
    elif 'rel' in notation:
        commands.append((Command.ReleaseAll, 0))
    elif '-U' in notation:
        commands.append((Command.ReleaseUp, 0))
    elif '-D' in notation:
        commands.append((Command.ReleaseDown, 0))
    elif '-B' in notation:
        commands.append((Command.ReleaseBack, 0))
    elif '-F' in notation:
        commands.append((Command.ReleaseForward, 0))
    elif '-R' in notation:
        commands.append((Command.ReleaseRage, 0))
    else:
        if 'u' in notation:
            commands.append((Command.TapUp, 0))
        if 'd' in notation:
            commands.append((Command.TapDown, 0))
        if 'b' in notation:
            commands.append((Command.TapBack, 0))
        if 'f' in notation:
            commands.append((Command.TapForward, 0))
        if 'U' in notation:
            commands.append((Command.HoldUp, 0))
        if 'D' in notation:
            commands.append((Command.HoldDown, 0))
        if 'B' in notation:
            commands.append((Command.HoldBack, 0))
        if 'F' in notation:
            commands.append((Command.HoldForward, 0))
        if 'R' in notation:
            commands.append((Command.HoldRage, 0))

        commands += GetAttackCommands(notation)



    return (commands, timingOccurances + occurances)


def GetAttackCommands(notation:str):
    commands = []

    if '*' in notation:
        if '+1' in notation:
            commands.append((Command.Hold1, 0))
        if '+2' in notation:
            commands.append((Command.Hold2, 0))
        if '+3' in notation:
            commands.append((Command.Hold3, 0))
        if '+4' in notation:
            commands.append((Command.Hold4, 0))

    elif '-' in notation:
        if '+1' in notation:
            commands.append((Command.Release1, 0))
        if '+2' in notation:
            commands.append((Command.Release2, 0))
        if '+3' in notation:
            commands.append((Command.Release3, 0))
        if '+4' in notation:
            commands.append((Command.Release4, 0))
    else:
        if '+1' in notation:
            commands.append((Command.Tap1, 0))
        if '+2' in notation:
            commands.append((Command.Tap2, 0))
        if '+3' in notation:
            commands.append((Command.Tap3, 0))
        if '+4' in notation:
            commands.append((Command.Tap4, 0))
    return commands
