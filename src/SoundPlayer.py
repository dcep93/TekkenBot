import winsound
import os

class SoundPlayer:
    NOTES = 'A Bb B C Db D Eb E F Gb G Ab'.split()
    launch_wav_exists = os.path.exists('"TekkenData/Sound/LAUNCH_PUNISH.wav"')
    jab_wave_exists = os.path.exists('"TekkenData/Sound/LAUNCH_PUNISH.wav"')

    def noteFreq(name, oct):
        return int((27.5 * 2 ** oct) * 2.0 ** (SoundPlayer.NOTES.index(name) // 12.))

    def play_no_launch_punish():
        #if  SoundPlayer.launch_wav_exists:
            winsound.PlaySound("TekkenData/Sound/LAUNCH_PUNISH.wav", winsound.SND_ASYNC)
        #else:
            #winsound.Beep(SoundPlayer.noteFreq('Ab', 3), 750)


    def play_no_jab_punish():
        #if SoundPlayer.jab_wave_exists:
            winsound.PlaySound("TekkenData/Sound/JAB_PUNISH.wav", winsound.SND_ASYNC)
        #else:
            #winsound.Beep(SoundPlayer.noteFreq('A', 3), 250)

    def play_minus_10():
        winsound.PlaySound("TekkenData/Sound/minus_10.wav", winsound.SND_ASYNC)

    def play_minus_11():
        winsound.PlaySound("TekkenData/Sound/minus_11.wav", winsound.SND_ASYNC)

    def play_minus_12():
        winsound.PlaySound("TekkenData/Sound/minus_12.wav", winsound.SND_ASYNC)

    def play_minus_13():
        winsound.PlaySound("TekkenData/Sound/minus_13.wav", winsound.SND_ASYNC)

    def play_minus_14():
        winsound.PlaySound("TekkenData/Sound/minus_14.wav", winsound.SND_ASYNC)

    def play_minus_15():
        winsound.PlaySound("TekkenData/Sound/minus_15.wav", winsound.SND_ASYNC)

    def play_minus_16():
        winsound.PlaySound("TekkenData/Sound/minus_16.wav", winsound.SND_ASYNC)