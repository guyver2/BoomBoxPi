import glob
import os
import json
from config import Config

if True:    # fake screen for raspberry pi
    os.environ['SDL_VIDEODRIVER'] = 'dummy'

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import mutagen.mp3
import random
import pygame
from time import sleep
import threading
import pickle
import uuid
from pathlib import Path

SONG_END = pygame.USEREVENT + 1


def get_uuid():
    full_uuid = uuid.uuid4()
    return full_uuid.hex[0:6]


class Track:

    def __init__(self, uid, title, artist, hidden, nb_plays):
        self.title = title
        self.artist = artist
        self.hidden = hidden
        self.nb_plays = nb_plays
        self.hash = uid
        self.path = Config.TRACKS_FOLDER + "%06d.mp3" % uid

    def __repr__(self):
        if self.artist is not None:
            return self.title + " by " + self.artist
        else:
            return self.title


class Playlist:

    def __init__(self, uid, name, tracks, hidden):
        self.name = name
        self.hash = uid
        self.tracks = tracks
        self.trackID = 0
        self.hidden = hidden

    def current(self):
        return self.tracks[self.trackID]

    def next(self):
        self.trackID = (self.trackID + 1) % len(self.tracks)
        return self.tracks[self.trackID]

    def prev(self):
        self.trackID = (self.trackID - 1) % len(self.tracks)
        return self.tracks[self.trackID]

    def shuffle(self):
        random.shuffle(self.tracks)


class Player:

    def __init__(self, playlists):
        global SONG_END
        self.lock = threading.RLock()
        self.volume = 0.05
        self.muted = False
        self.volumeMax = 100
        self.playing = False
        self.paused = False
        self.playlists = playlists
        self.playlistID = 0
        self.currentPlaylist = None
        self.currentTrack = None
        self.shuffleMode = False
        pygame.mixer.pre_init(44100, -16, 2,
                              2048)    # setup mixer to avoid sound lag
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.set_endevent(SONG_END)
        self.alive = True
        if (self.playlists is not None and len(self.playlists) > 0):
            self.setPlaylist(self.playlists[0])
        self.thread = threading.Thread(target=self.watchdog)
        self.thread.start()

    def resetMixer(self, freq):
        pygame.mixer.quit()
        pygame.mixer.init(frequency=freq)
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.set_endevent(SONG_END)

    def __del__(self):
        self.alive = False

    def nowPlaying(self):
        return self.currentPlaylist.name + " - " + str(self.currentTrack)

    def setPlaylists(self, playlists):
        with self.lock:
            self.stop()
            self.playlists = playlists
            if (self.playlists is not None and len(self.playlists) > 0):
                self.setPlaylist(self.playlists[0])

    def setPlaylist(self, playlist):
        with self.lock:
            self.stop()
            self.currentPlaylist = playlist
            if self.shuffleMode:
                self.shuffle()
            print("using playlist", self.currentPlaylist.name)

    def play(self):
        with self.lock:
            if self.playing and self.paused:
                pygame.mixer.music.unpause()
                pygame.mixer.music.set_volume(self.volume)
                print("unpause", self.currentTrack)
                self.paused = False
            else:
                self.currentTrack = self.currentPlaylist.current()
                print("gonna play", self.currentTrack.path)
                self.resetMixer(
                    mutagen.mp3.MP3(self.currentTrack.path).info.sample_rate)
                pygame.mixer.music.load(self.currentTrack.path)
                pygame.mixer.music.play(0)
                print("now playing", self.currentTrack)
                self.playing = True
                self.paused = False

    def stop(self):
        with self.lock:
            self.playing = False
            self.paused = False
            self.currentTrack = None
            pygame.mixer.music.stop()

    def pause(self):
        with self.lock:
            if not self.paused:
                pygame.mixer.music.pause()
                print("pause", self.currentTrack)
                self.paused = True

    def playPause(self):
        with self.lock:
            if self.playing and not self.paused:
                self.pause()
            else:
                self.play()

    def shuffle(self, onOrOff=True):
        self.shuffleMode = onOrOff
        if self.shuffleMode and self.currentPlaylist is not None:
            self.currentPlaylist.shuffle()

    def next(self):
        with self.lock:
            self.currentTrack = self.currentPlaylist.next()
            self.resetMixer(
                mutagen.mp3.MP3(self.currentTrack.path).info.sample_rate)
            pygame.mixer.music.load(self.currentTrack.path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(0)
            print("now playing", self.currentTrack)
            self.playing = True
            self.paused = False

    def prev(self):
        with self.lock:
            self.currentTrack = self.currentPlaylist.prev()
            self.resetMixer(
                mutagen.mp3.MP3(self.currentTrack.path).info.sample_rate)
            pygame.mixer.music.load(self.currentTrack.path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(0)
            print("now playing", self.currentTrack)
            self.playing = True
            self.paused = False

    def nextPlaylist(self):
        with self.lock:
            self.playlistID = (self.playlistID + 1) % len(self.playlists)
            self.setPlaylist(self.playlists[self.playlistID])
            self.next()

    def prevPlaylist(self):
        with self.lock:
            self.playlistID = (self.playlistID - 1) % len(self.playlists)
            self.setPlaylist(self.playlists[self.playlistID])
            self.next()

    def getTrackPos(self):
        with self.lock:
            if self.playing:
                return pygame.mixer.music.get_pos()

    def setVolume(self, vol):
        with self.lock:
            self.volume = vol / 100.0
            if self.playing and pygame.mixer.get_init() is not None:
                pygame.mixer.music.set_volume(self.volume)

    def getVolume(self):
        return self.volume * 100

    def request(self, path):
        with self.lock:
            print("requested:", path)
            data = path.split()
            if len(data) < 2:
                print("Error: Invalid request")
                return
            flag = data.pop(0)
            uid = int(data.pop(0))
            if (flag == "p"):
                for p in self.playlists:
                    if uid == p.hash:
                        self.setPlaylist(p)
                        self.play()
                        return
            if (flag == "t"):
                for p in self.playlists:
                    for i, t in enumerate(p.tracks):
                        if uid == t.hash:
                            p.trackID = i
                            self.setPlaylist(p)
                            self.play()
                            return
            print("no match found, or invalid request")

    def watchdog(self):
        global SONG_END
        while self.alive:
            for event in pygame.event.get():
                if event.type == SONG_END:
                    print("song ended, playing next one")
                    self.currentTrack.nb_plays += 1
                    self.next()


def importPlaylists():
    playlists = []
    if os.path.isfile("data/playlists.json"):
        with open('data/playlists.json') as f:
            data = json.load(f)
            for p in data["playlists"]:
                play = Playlist("fake")
                play.fromDict(p)
                if len(play.tracks) != 0:
                    playlists.append(play)
    else:
        for playlistDir in glob.glob("data/playlists/*"):
            if os.path.isdir(playlistDir):
                playlists.append(Playlist(playlistDir))
        with open("data/playlists.json", "w") as write_file:
            data = {"playlists": [p.toDict() for p in playlists]}
            json.dump(data, write_file)
    print("done loading playlists", len(playlists))
    return playlists


if __name__ == "__main__":
    playlists = importPlaylists()
    for p in playlists:
        print("[p]", p.name, p.hash)
        for t in p.tracks:
            print("  *", t.title, t.hash)

    for p in playlists:
        print(p.name, len(p.tracks))

    player = Player(playlists)
    player.shuffle()
    player.nextPlaylist()
    player.play()
    sleep(5)
    player.pause()
    sleep(5)
    player.play()
    sleep(5)
    player.pause()
    sleep(5)
    player.next()
    sleep(5)
    player.next()
    sleep(5)
    player.prev()
    sleep(5)
    player.nextPlaylist()

    sleep(5)
    player.alive = False

    print("all closed")
