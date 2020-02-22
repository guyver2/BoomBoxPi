#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import threading

class NFC:
    READ = 0
    WRITE_TRACK = 1
    WRITE_PLAYLIST = 2


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
                            if splits[0] == "t" and self.player.currentTrack is not None and hashRequest == str(self.player.currentTrack.hash):
                                print("requested track already playing", text)
                                continue
                            if splits[0] == "p" and self.player.currentPlaylist is not None and hashRequest == str(self.player.currentPlaylist.hash):
                                print("requested playlist already playing", text)
                                continue
                            self.player.request(text)
                if self.mode == NFC.WRITE_TRACK:
                    id, text = self.reader.write_no_block("t " + str(self.player.currentTrack.hash))
                    if id is not None:
                        print("nfc written")
                        self.mode = NFC.READ
                if self.mode == NFC.WRITE_PLAYLIST:
                    id, text = self.reader.write_no_block("p " + str(self.player.currentPlaylist.hash))
                    if id is not None:
                        print("nfc written")
                        self.mode = NFC.READ
        finally:
            GPIO.cleanup()
    
    def switchMode(self, mode):
        if mode in [NFC.READ, NFC.WRITE_TRACK, NFC.WRITE_PLAYLIST]:
            self.mode = mode


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
