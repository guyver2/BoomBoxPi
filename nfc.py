#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import threading
import time


class NFC:
    READ = 0
    WRITE_TRACK = 1
    WRITE_PLAYLIST = 2
    WRITE = 3

    def __init__(self, player, buttons):
        self.reader = SimpleMFRC522()
        self.player = player
        self.buttons = buttons
        self.mode = NFC.READ
        self.clear_payload = None
        self.payload = None
        self.write_thread_running = False
        if self.player is not None:
            self.thread = threading.Thread(target=self.watchdog)
            self.thread.start()

    def watchdog(self):
        try:
            while self.player.alive:

                if self.clear_payload is not None:
                    if time.time() > self.clear_payload:
                        self.payload = None
                        self.clear_payload = None

                if self.mode == NFC.READ:
                    id, text = self.reader.read_no_block()
                    if (id != None):
                        if self.payload is not None and text.strip(
                        ) == self.payload.strip():
                            continue
                        splits = text.split()
                        if len(splits) >= 2:
                            hashRequest = splits[1]
                            currentTrack = self.player.currentTrack
                            if splits[
                                    0] == "t" and currentTrack is not None and hashRequest == str(
                                        currentTrack.hash):
                                print("requested track already playing", text)
                                continue
                            if splits[
                                    0] == "p" and self.player.currentPlaylist is not None and hashRequest == str(
                                        self.player.currentPlaylist.hash):
                                print("requested playlist already playing",
                                      text)
                                continue
                            self.player.request(text)
                if self.mode == NFC.WRITE:
                    if self.payload == None:
                        continue
                    id, text = self.reader.write_no_block(self.payload)
                    if id is not None:
                        print("nfc written")
                        self.mode = NFC.READ
        finally:
            GPIO.cleanup()

    def write(self, payload):
        if not self.write_thread_running:
            print("asking to write:", payload)
            self.payload = payload
            self.mode = NFC.WRITE
            self.thread = threading.Thread(target=self.write_mode_timeout)
            self.thread.start()

    def write_mode_timeout(self, timeout=5):
        self.write_thread_running = True
        t0 = time.time()
        but_id = 0
        for b in self.buttons[:-1]:
            b.on()
        while self.player.alive and self.mode != NFC.READ and time.time(
        ) - t0 < timeout:
            self.buttons[(but_id - 1) % len(self.buttons)].on()
            self.buttons[but_id % len(self.buttons)].off()
            time.sleep(0.2)
            but_id += 1
        for b in self.buttons:
            b.off()
        self.mode = NFC.READ
        self.write_thread_running = False
        self.clear_payload = time.time() + 5    # clear payload in 5 secs


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
