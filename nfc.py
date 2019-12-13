#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import threading

class NFC:
    READ = 0
    WRITE = 1

    def __init__(self, player):
        self.last_read = None
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
                    if (id != None) and (text != self.last_read):
                        self.last_read = text
                        self.player.request(self.last_read)
                if self.mode == NFC.WRITE:
                    id, text = self.reader.write_no_block("t " + self.player.currentTrack.hash + " " + self.player.currentTrack.title)
                    if id is not None:
                        print("nfc written")
                        self.last_read = text
                        self.mode = NFC.READ
        finally:
            GPIO.cleanup()


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
