class Button:
    def __init__(self, pinSwitch, pinLED, ID, player):
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
        pass
   

class Potentiometer:
    def __init__(self, player):
        pass

    def lockUnlock(self):
        pass

class NFC:
    READ = 0
    WRITE = 1
    def __init__(self, player):
        self.mode = NFC.READ
        pass

    def switchMode(self):
        if self.mode == NFC.READ:
            self.mode = NFC.WRITE
        else:
            self.mode = NFC.READ