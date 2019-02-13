import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
import threading
import glob
import os
import time
from pibox import Player, Playlist

class ButtonHandler(threading.Thread):
    def __init__(self, pin, funcDown, funcUp, bouncetime=200):
        threading.Thread.__init__(self)
        self.funcDown = funcDown
        self.funcUp = funcUp
        self.pin = pin
        self.bouncetime = float(bouncetime)/1000
        self.lastpinval = GPIO.input(self.pin)
        self.lock = threading.Lock()

    def __call__(self, *args):
        if not self.lock.acquire(False):
            return
        t = threading.Timer(self.bouncetime, self.read, args=args)
        t.start()

    def read(self, *args):
        pinval = GPIO.input(self.pin)
        if (pinval == 0 and self.lastpinval == 1):
            self.funcUp(*args)
        if (pinval == 1 and self.lastpinval == 0):
            self.funcDown(*args)
        self.lastpinval = pinval
        self.lock.release()


class Button:
    def __init__(self, pinSwitch, pinLED, ID, player):
        self.lock = False
        self.pinSwitch = pinSwitch
        self.pinLED = pinLED
        self.ID = ID
        self.player = player
        GPIO.setup(self.pinSwitch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.handler = ButtonHandler(self.pinSwitch, self.down, self.up, 100)
        self.handler.start()
        GPIO.add_event_detect(self.pinSwitch, GPIO.RISING, callback=self.handler)
        GPIO.setup(self.pinLED, GPIO.OUT)
        GPIO.output(self.pinLED, GPIO.HIGH)
        
    def down(self, args):
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
                print("not ready yet")
                pass
        GPIO.output(self.pinLED, GPIO.LOW)
    
    def up(self, args):
        GPIO.output(self.pinLED, GPIO.HIGH)
    
    def on(self):
        GPIO.output(self.pinLED, GPIO.LOW)
    
    def off(self):
        GPIO.output(self.pinLED, GPIO.HIGH)
        
    def lockUnlock(self):
        self.lock = not self.lock
    
    

if __name__ == "__main__":
    def startSignal(buttons):
        for b in buttons:
            b.on()
            time.sleep(0.2)
        for b in buttons:
            b.off()
            time.sleep(0.2)


    playlists = []
    for playlistDir in glob.glob("/home/pi/pibox/data/playlists/*"):
        if os.path.isdir(playlistDir):
            print playlistDir
            playlists.append(Playlist(playlistDir))

    player = Player(playlists)

    GPIO.setwarnings(False) # Ignore warning for now
    GPIO.setmode(GPIO.BCM) # Use physical pin numbering

    but0 = Button(24, 13, 0, player)
    but1 = Button(22, 5, 1, player)
    but2 = Button(23, 12, 2, player)
    but3 = Button(6, 27, 3, player)


    startSignal([but0, but1, but3, but2])

    print("started")
    while(True):
        pass
    GPIO.cleanup() # Clean up
