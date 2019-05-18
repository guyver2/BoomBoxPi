import gpiozero as gz
import sys

from pibox import Player, Playlist, importPlaylists
from functools import partial


class Button:
    def __init__(self, pinSwitch, pinLED, ID, player):
        self.lock = False
        self.pinSwitch = pinSwitch
        self.pinLED = pinLED
        self.ID = ID
        self.player = player
        self.button = gz.Button(self.pinSwitch, pull_up=False)
        self.led = gz.LED(pinLED, active_high=False)
        self.led.off()
        self.button.when_pressed = self.down
        self.button.when_released = self.up
        
    def down(self):
        self.led.on()
        if not self.lock:
            try:
                if self.ID == 0:
                    self.player.nextPlaylist()
                if self.ID == 1:
                    self.player.playPause()
                if self.ID == 2:
                    self.player.prev()
                if self.ID == 3:
                    self.player.next()
            except:
                print("not ready yet", sys.exc_info()[0])
                pass
    
    def up(self, args):
        self.led.off()
        
    def on(self):
        self.led.on()
        
    def off(self):
        self.led.off()
        
    def lockUnlock(self):
        self.lock = not self.lock
    
    

if __name__ == "__main__":
    import time
    def startSignal(buttons):
        for b in buttons:
            b.on()
            time.sleep(0.2)
        for b in buttons:
            b.off()
            time.sleep(0.2)


    playlists = importPlaylists()

    player = Player(playlists)

    but0 = Button(24, 13, 0, player)
    but1 = Button(22, 5, 1, player)
    but2 = Button(23, 12, 2, player)
    but3 = Button(6, 27, 3, player)


    startSignal([but0, but1, but3, but2])

    print("started")
    while(True):
        pass

