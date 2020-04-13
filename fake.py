class Button:
    def __init__(self, pinSwitch, pinLED, ID, player):
        self.lock = False
        pass

    def down(self):
        pass

    def up(self, args):
        pass

    def on(self):
        pass

    def off(self):
        pass

    def lockUnlock(self):
        self.lock = not self.lock
        pass


class Potentiometer:
    def __init__(self, player):
        self.lock = False
        pass

    def lockUnlock(self):
        self.lock = not self.lock
        pass


class NFC:
    READ = 0
    WRITE_TRACK = 1
    WRITE_PLAYLIST = 2

    def __init__(self, player):
        self.mode = NFC.READ
        pass

    def switchMode(self, mode):
        if mode in [NFC.READ, NFC.WRITE_TRACK, NFC.WRITE_PLAYLIST]:
            self.mode = mode
