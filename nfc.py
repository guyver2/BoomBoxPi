#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import threading

class NFC:
    READ = 0
    WRITE = 1

    def __init__(self, player):
        self.reader = SimpleMFRC522()
        self.player = player
        self.mode = NFC.READ
        if self.player is not None:
            self.thread = threading.Thread(target = self.watchdog)
            self.thread.start()

    def watchdog(self):
        try:
            while self.player.alive:
                if self.mode == NFC.READ:
                    id, text = self.reader.read_no_block()
                    if (id != None):
                        splits = text.split()
                        if len(splits) >= 2:
                            hashRequest = splits[1]
                            if self.player.currentTrack is not None and hashRequest == self.player.currentTrack.hash:
                                continue
                            if self.player.currentPlaylist is not None and hashRequest == self.player.currentPlaylist.hash:
                                continue
                            self.player.request(text)
                if self.mode == NFC.WRITE:
                    id, text = self.reader.write_no_block("t " + self.player.currentTrack.hash + " " + self.player.currentTrack.title)
                    if id is not None:
                        print("nfc written")
                        self.mode = NFC.READ
        finally:
            GPIO.cleanup()
    
    def switchMode(self):
        if self.mode == NFC.READ:
            self.mode = NFC.WRITE
        else:
            self.mode = NFC.READ


if __name__ == "__main__":

    class DummyPlayer:
        alive = True
    
        def request(self, path):
            print("requesting:", path)


    import time
    nfc = NFC(DummyPlayer())
    print("waiting")
    while True:
        time.sleep(0.1)
