import glob
import os
from eyed3 import id3
import unicodedata    
import random

class Track:
	def __init__(self, path):
		self.path = path
		self.valid = os.path.isfile(path)
		if self.valid:
			tag = id3.Tag()
			tag.parse(self.path)
 			self.artist = unicode(tag.artist).encode("utf8")
			self.album = unicode(tag.album).encode("utf8")
			self.title = unicode(tag.title).encode("utf8")
			
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
		
	def next(self):
		track = self.tracks[self.trackID]
		self.trackID = (self.trackID + 1) % len(self.tracks)
		return track
	
	def prev(self):
		self.trackID = (self.trackID - 1) % len(self.tracks)
		return self.tracks[self.trackID]
	
	def shuffle(self):
		random.shuffle(self.tracks)
	

class Player:
	def __init__(self):
		self.volume = 50
		self.muted = False
		self.volumeMax = 100
		self.playing = False
		self.paused = False
		self.currentPlaylist = None
		self.currentTrack = None
		self.shuffleMode = False
	
	def setPlaylist(self, playlist):
		self.currentPlaylist = playlist
		if self.shuffleMode:
			self.shuffle()
		print "using playlist", self.currentPlaylist.name
	
	def play(self):
		if self.playing and self.paused :
			print "unpause", self.currentTrack
			self.paused = False
		else:
			self.next()
	
	def pause(self):
		if not self.paused :
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
		print "now playing", self.currentTrack
		self.playing = True
		self.paused = False
	
	def prev(self):
		self.currentTrack = self.currentPlaylist.prev()
		print "now playing", self.currentTrack
		self.playing = True
		self.paused = False
	

playlists = []
for playlistDir in glob.glob("data/playlists/*"):
	if os.path.isdir(playlistDir):
		print playlistDir
		playlists.append(Playlist(playlistDir))

player = Player()
player.shuffle()
player.setPlaylist(playlists[0])
player.play()
player.pause()
player.next()
player.next()
player.prev()
		
		
		
		
		
		
		
		
		
		
    
