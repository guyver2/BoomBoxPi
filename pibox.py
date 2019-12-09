import glob
import os
import json

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
import unicodedata

SONG_END = pygame.USEREVENT + 1


class Track:

    def __init__(self, path=""):
        if path == "":
            return
        self.path = path
        self.valid = os.path.isfile(path)
        if self.valid:
            try:
                tag = EasyID3(path)
                self.title = tag["title"][0].encode("utf8")
                self.title = unicodedata.normalize('NFKD', self.title).encode(
                    'ascii', 'ignore')
            except:
                self.title = "unknown".encode("utf8")

    def __repr__(self):
        return self.title

    def toDict(self):
        result = {}
        result["path"] = self.path
        result["title"] = self.title
        return result

    def fromDict(self, data):
        self.path = data["path"]
        self.title = data["title"]
        self.valid = os.path.isfile(self.path)


class Playlist:

    def __init__(self, path):
        self.name = os.path.basename(path)
        self.path = path
        self.tracks = []
        self.loadTracks()
        self.trackID = 0

    def toDict(self):
        result = {}
        result["path"] = self.path
        result["name"] = self.name
        result["tracks"] = [track.toDict() for track in self.tracks]
        return result

    def fromDict(self, data):
        self.path = data["path"]
        self.name = data["name"]
        self.tracks = []
        for track in data["tracks"]:
            t = Track()
            t.fromDict(track)
            self.tracks.append(t)
        self.trackID = -0

    def loadTracks(self):
        for trackFile in sorted(glob.glob(self.path + "/*")):
            if os.path.isfile(trackFile) and trackFile.lower().endswith("mp3"):
                self.tracks.append(Track(trackFile))

    def isValidFile(self, trackFile):
        if not os.path.isFile(trackFile): return False

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
        self.thread = threading.Thread(target = self.watchdog)
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
        self.stop()
        self.playlists = playlists
        if (self.playlists is not None and len(self.playlists) > 0):
            self.setPlaylist(self.playlists[0])

    def setPlaylist(self, playlist):
        self.stop()
        self.currentPlaylist = playlist
        if self.shuffleMode:
            self.shuffle()
        print("using playlist", self.currentPlaylist.name)
        print(self.currentPlaylist)

    def play(self):
        if self.playing and self.paused:
            pygame.mixer.music.unpause()
            pygame.mixer.music.set_volume(self.volume)
            print("unpause", self.currentTrack)
            self.paused = False
        else:
            self.currentTrack = self.currentPlaylist.current()
            self.resetMixer(
                mutagen.mp3.MP3(self.currentTrack.path).info.sample_rate)
            pygame.mixer.music.load(self.currentTrack.path)
            pygame.mixer.music.play(0)
            print("now playing", self.currentTrack)
            self.playing = True
            self.paused = False

    def stop(self):
        self.playing = False
        self.paused = False
        self.currentTrack = None
        pygame.mixer.music.stop()

    def pause(self):
        if not self.paused:
            pygame.mixer.music.pause()
            print("pause", self.currentTrack)
            self.paused = True

    def playPause(self):
        if self.playing and not self.paused:
            self.pause()
        else:
            self.play()

    def shuffle(self, onOrOff=True):
        self.shuffleMode = onOrOff
        if self.shuffleMode and self.currentPlaylist is not None:
            self.currentPlaylist.shuffle()

    def next(self):
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
        self.playlistID = (self.playlistID + 1) % len(self.playlists)
        self.setPlaylist(self.playlists[self.playlistID])
        self.next()

    def prevPlaylist(self):
        self.playlistID = (self.playlistID - 1) % len(self.playlists)
        self.setPlaylist(self.playlists[self.playlistID])
        self.next()

    def getTrackPos(self):
        if self.playing:
            return pygame.mixer.music.get_pos()

    def setVolume(self, vol):
        self.volume = vol / 100.0
        if self.playing:
            pygame.mixer.music.set_volume(self.volume)

    def getVolume(self):
        return self.volume * 100

    def watchdog(self):
        global SONG_END
        while self.alive:
            for event in pygame.event.get():
                if event.type == SONG_END:
                    print("song ended, playing next one")
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
        with open("data/playlists.dat", "wb") as write_file:
            pickle.dump(playlists, write_file)
    print("done loading playlists", len(playlists))
    return playlists


if __name__ == "__main__":
    playlists = importPlaylists()

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
