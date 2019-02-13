import glob
import os

if True: # fake screen for raspberry pi
    os.environ['SDL_VIDEODRIVER'] = 'dummy'

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import unicodedata    
import random
import pygame
from time import sleep
import thread

SONG_END = pygame.USEREVENT + 1

class Track:
    def __init__(self, path):
        self.path = path
        self.valid = os.path.isfile(path)
        if self.valid:
            tag = EasyID3(path)
            self.artist = unicode(tag["artist"][0]).encode("utf8")
            self.album = unicode(tag["album"][0]).encode("utf8")
            self.title = unicode(tag["title"][0]).encode("utf8")
            self.length = MP3(path).info.length
            
    def __repr__(self):
        data = unicode("%s - %s"%(self.artist, self.title), "utf8")
        return unicodedata.normalize('NFKD', data).encode('ascii','ignore')

        
class Playlist:
    def __init__(self, path):
        self.name = os.path.basename(path)
        self.path = path
        self.tracks = []
        self.loadTracks()
        self.trackID = 0
    
    def loadTracks(self):
        for trackFile in glob.glob(self.path+"/*"):
            if os.path.isfile(trackFile) and trackFile.lower().endswith("mp3"):
               self.tracks.append(Track(trackFile)) 
    
    def isValidFile(self, trackFile):
        if not os.path.isFile(trackFile) : return False     
        
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
        pygame.mixer.pre_init(44100, -16, 2, 2048) # setup mixer to avoid sound lag
        pygame.init()
        pygame.display.set_mode((1,1))
        pygame.mixer.init()
        pygame.mixer.music.set_endevent(SONG_END)
        self.alive = True
        if(self.playlists is not None and len(self.playlists) > 0):
            self.setPlaylist(self.playlists[0])
        thread.start_new_thread(Player.watchdog, (self,))
    
    def __del__(self):
        self.alive = False
    
    def nowPlaying(self):
        return self.currentPlaylist.name + " - " + str(self.currentTrack)
    
    def setPlaylists(self, playlists):
        self.stop()
        self.playlists = playlists
        self.setPlaylist(self.playlists[0])
    
    def setPlaylist(self, playlist):
        self.stop()
        self.currentPlaylist = playlist
        if self.shuffleMode:
            self.shuffle()
        print "using playlist", self.currentPlaylist.name
    
    def play(self):
        if self.playing and self.paused :
            pygame.mixer.music.unpause()
            print "unpause", self.currentTrack
            self.paused = False
        else:
            self.currentTrack = self.currentPlaylist.current()
            pygame.mixer.music.load(self.currentTrack.path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(0)
            print "now playing", self.currentTrack
            self.playing = True
            self.paused = False
    
    def stop(self):
        self.playing = False
        self.paused = False
        self.currentTrack = None
        pygame.mixer.music.stop()
    
    def pause(self):
        if not self.paused :
            pygame.mixer.music.pause()
            print "pause", self.currentTrack
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
        pygame.mixer.music.load(self.currentTrack.path)
        pygame.mixer.music.play(0)
        print "now playing", self.currentTrack
        self.playing = True
        self.paused = False
    
    def prev(self):
        self.currentTrack = self.currentPlaylist.prev()
        pygame.mixer.music.load(self.currentTrack.path)
        pygame.mixer.music.play(0)
        print "now playing", self.currentTrack
        self.playing = True
        self.paused = False
        
    def nextPlaylist(self):
        self.playlistID = (self.playlistID+1) % len(self.playlists)
        self.setPlaylist(self.playlists[self.playlistID])
        self.next()
        
    def prevPlaylist(self):
        self.playlistID = (self.playlistID-1) % len(self.playlists)
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
                    print "song ended, playing next one"
                    self.next()
    



if __name__ == "__main__":

    playlists = []
    for playlistDir in glob.glob("data/playlists/*"):
        if os.path.isdir(playlistDir):
            print playlistDir
            playlists.append(Playlist(playlistDir))

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

    print "all closed"
        
        
        
        
        
        
        
    
