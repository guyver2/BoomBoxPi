class Config:
    FAKE = False
    DATA = "/home/pi/boomboxpi/data/playlists/"
    TRACKS_FOLDER = DATA + "tracks/"
    DUMP_FOLDER = DATA + "dump/"
    TRACKS_IMG_FOLDER = DATA + "covers/tracks/"
    PLAYLISTS_IMG_FOLDER = DATA + "covers/playlists/"
    DEFAULT_TRACK_IMG = TRACKS_IMG_FOLDER + "default.jpg"
    DEFAULT_PL_IMG = PLAYLISTS_IMG_FOLDER + "default.jpg"
    WEBRADIOS_IMG_FOLDER = DATA + "covers/webradios/"
    DEFAULT_WR_IMG = WEBRADIOS_IMG_FOLDER + "default.png"
    SPOTIPY_CLIENT_ID = "XXXXXXXX"
    SPOTIPY_CLIENT_SECRET = "XXXXXXXX"
