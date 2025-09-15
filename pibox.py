import os
try:
    from localConfig import LocalConfig as Config
except:
    from config import Config
from enum import Enum

from contextlib import contextmanager
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import random
import threading
import uuid
from pathlib import Path
import mpd


def get_uuid():
    full_uuid = uuid.uuid4()
    return full_uuid.hex[0:6]


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


class Track:

    def __init__(self, uid, title, artist, album, hidden, nb_plays, cover,
                 tracknumber):
        self.title = title
        self.artist = artist
        self.album = album
        self.hidden = hidden
        self.nb_plays = nb_plays
        self.cover = cover
        self.tracknumber = tracknumber
        self.hash = uid
        self.path = Config.TRACKS_FOLDER + "%06d.mp3" % uid

    def toDict(self):
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "nb_plays": self.nb_plays,
            "hidden": self.hidden,
            "cover": self.get_cover_url(),
            "uuid": self.hash,
            "tracknumber": self.tracknumber,
            "url": "data/?q=track&tid=" + str(self.hash),
        }

    def __repr__(self):
        if self.artist is not None and self.artist != "Unknown":
            return self.title + " by " + self.artist
        else:
            return self.title

    def get_cover_url(self):
        return "covers/track/" + os.path.basename(self.cover)


class Playlist:

    def __init__(self, uid, name, tracks, hidden):
        self.name = name
        self.hash = uid
        self.tracks = tracks
        self.trackID = 0
        self.hidden = hidden

    def toDict(self):
        return {
            "name": self.name,
            "hidden": self.hidden,
            "uuid": self.hash,
            "cover": self.get_cover_url(),
            "url": "data/?q=playlist&pid=" + str(self.hash),
        }

    def get_cover_url(self):
        return "covers/playlist/default.jpg"

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


class PlayerMode(Enum):
    MUSIC = 1
    WEBRADIO = 2


class Player:

    def __init__(self, playlists):
        self.lock = threading.RLock()
        self.muted = False
        self.volumeMax = 100
        self.playing = False
        self.paused = False
        self.playlists = playlists
        self.currentPlaylist = None
        self.mode = PlayerMode.MUSIC
        self.currentWebRadio = None
        self.mpd_client = mpd.MPDClient(use_unicode=True)
        with self.connection():
            self.volume = int(self.mpd_client.status()["volume"])
            self.mpd_client.update()
            self.mpd_client.repeat(1)
            self.mpd_client.clear()

        self.alive = True
        if self.playlists is not None and len(self.playlists) > 0:
            self.setPlaylist(self.playlists[0])

    @property
    def currentTrack(self):
        with self.connection():
            try:
                trackID = int(self.mpd_client.currentsong()["pos"])
                return self.currentPlaylist.tracks[trackID]
            except:
                return None

    @currentTrack.setter
    def currentTrack(self, value):
        raise ValueError("currentTrack is not supposed to be set")

    @contextmanager
    def connection(self):
        try:
            self.mpd_client.connect(Config.MPD_HOST, Config.MPD_PORT)
            yield
        finally:
            self.mpd_client.close()
            self.mpd_client.disconnect()

    def __del__(self):
        self.alive = False

    def nowPlaying(self):
        if self.mode == PlayerMode.WEBRADIO:
            return "Radio: " + self.currentWebRadio
        else:
            return self.currentPlaylist.name + " - " + str(self.currentTrack)

    def setPlaylists(self, playlists):
        with self.lock:
            self.stop()
            self.playlists = playlists
            if self.playlists is not None and len(self.playlists) > 0:
                self.setPlaylist(self.playlists[0])

    def setPlaylist(self, playlist):
        with self.lock:
            self.stop()
            with self.connection():
                self.mpd_client.clear()
            if self.mode == PlayerMode.WEBRADIO:
                self.mode = PlayerMode.MUSIC
            self.currentPlaylist = playlist
            self.currentPlaylist.trackID = 0
            with self.connection():
                for track in self.currentPlaylist.tracks:
                    self.mpd_client.add(Path(track.path).name)
            print("using playlist", self.currentPlaylist.name)

    def play(self, songpos=0):
        with self.lock:
            if self.mode == PlayerMode.WEBRADIO:
                self.mode = PlayerMode.MUSIC
                self.setPlaylist(self.currentPlaylist)
            if self.playing and self.paused:
                with self.connection():
                    self.mpd_client.pause(0)
                self.setVolume(self.volume)
                self.paused = False
            elif not self.playing:
                with self.connection():
                    self.mpd_client.play(songpos)
                print("now playing", self.currentTrack)
                self.playing = True
                self.paused = False

    def stop(self):
        with self.lock:
            if self.mode == PlayerMode.WEBRADIO:
                with self.connection():
                    self.mpd_client.stop()
            else:
                self.playing = False
                self.paused = False
                with self.connection():
                    self.mpd_client.stop()

    def pause(self):
        with self.lock:
            if not self.paused and self.mode == PlayerMode.MUSIC:
                with self.connection():
                    self.mpd_client.pause(1)
                self.paused = True

    def playPause(self):
        with self.lock:
            if self.playing and not self.paused:
                self.pause()
            else:
                self.play()

    def next(self):
        with self.lock:
            self.currentPlaylist.next()
            if self.mode == PlayerMode.WEBRADIO:
                self.mode = PlayerMode.MUSIC
                self.setPlaylist(self.currentPlaylist)
                with self.connection():
                    self.play(self.currentPlaylist.trackID)
            else:
                with self.connection():
                    self.mpd_client.play()
                    self.mpd_client.next()
            print("now playing", self.currentTrack)
            self.playing = True
            self.paused = False

    def prev(self):
        with self.lock:
            self.currentPlaylist.prev()
            if self.mode == PlayerMode.WEBRADIO:
                self.mode = PlayerMode.MUSIC
                self.setPlaylist(self.currentPlaylist)
                with self.connection():
                    self.play(self.currentPlaylist.trackID)
            else:
                with self.connection():
                    self.mpd_client.play()
                    self.mpd_client.previous()
            print("now playing", self.currentTrack)
            self.playing = True
            self.paused = False

    def nextPlaylist(self):
        with self.lock:
            playlistID = self.playlists.index(self.currentPlaylist)
            previous_playlistID = playlistID
            playlistID = (playlistID + 1) % len(self.playlists)
            while self.playlists[
                    playlistID].hidden and playlistID != previous_playlistID:
                playlistID = (playlistID + 1) % len(self.playlists)
            self.setPlaylist(self.playlists[playlistID])
            self.play()

    def prevPlaylist(self):
        with self.lock:
            playlistID = self.playlists.index(self.currentPlaylist)
            previous_playlistID = playlistID
            playlistID = (playlistID - 1) % len(self.playlists)
            while self.playlists[
                    playlistID].hidden and playlistID != previous_playlistID:
                playlistID = (playlistID - 1) % len(self.playlists)
            self.setPlaylist(self.playlists[playlistID])
            self.play()

    def getTrackPos(self):
        with self.lock:
            if self.playing:
                with self.connection():
                    status = self.mpd_client.status()
                    return status["elapsed"], status["duration"]

    def setVolume(self, volume):
        with self.lock:
            volume = clamp(volume, 0, 100)
            self.volume = volume
            volume = 0 if self.muted else self.volume
            with self.connection():
                self.mpd_client.setvol(self.volume)

    def getVolume(self):
        if self.volume is None:
            with self.connection():
                return int(self.mpd_client.status()["volume"])
        else:
            return self.volume

    def mute(self):
        self.muted = True
        self.setVolume(self.getVolume())

    def unmute(self):
        self.muted = False
        self.setVolume(self.getVolume())

    def play_radio(self, name, url):
        self.stop()
        self.mode = PlayerMode.WEBRADIO
        self.currentWebRadio = name
        with self.connection():
            self.mpd_client.clear()
            self.mpd_client.add(url)
            self.mpd_client.play()

    def request(self, path):
        with self.lock:
            print("requested:", path)
            data = path.split()
            if len(data) < 2:
                print("Error: Invalid request")
                return
            flag = data.pop(0)
            uid = int(data.pop(0))
            if flag == "p":
                for p in self.playlists:
                    if uid == p.hash:
                        self.setPlaylist(p)
                        self.play()
                        return
            if flag == "t":
                for p in self.playlists:
                    for i, t in enumerate(p.tracks):
                        if uid == t.hash:
                            p.trackID = i
                            self.setPlaylist(p)
                            self.play(i)
                            return
            if flag == "r":
                from boomboxDB import BoomboxDB
                boomboxDB = BoomboxDB()
                radio = boomboxDB.get_web_radio(uid)
                self.play_radio(radio[1], radio[2])
                return
            print("no match found, or invalid request")

    def hide(self, pl_id):
        with self.lock:
            for p in self.playlists:
                if pl_id == p.hash:
                    p.hidden = not p.hidden
                    return p.hidden
        return None


if __name__ == "__main__":
    pass
