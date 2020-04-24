import os

try:
    from localConfig import LocalConfig as Config
except:
    from config import Config


os.environ["SPOTIPY_CLIENT_ID"] = Config.SPOTIPY_CLIENT_ID
os.environ["SPOTIPY_CLIENT_SECRET"] = Config.SPOTIPY_CLIENT_SECRET

import hashlib
from mutagen.id3 import ID3
from io import BytesIO
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def get_hash(data):
    hash = hashlib.sha1()
    hash.update(data.encode("utf-8"))
    return hash.hexdigest()[:8]


class CoverManager:
    @staticmethod
    def get_cover(track):
        filename = CoverManager.get_existing(track)
        if filename is None:
            filename = CoverManager.get_from_id3_tags(track.hash)
        if filename is None:
            filename = CoverManager.search_from_album(track.album)
        if filename is None:
            filename = CoverManager.search_from_full_track(track.album, track.title)
        if filename is None:
            filename = Config.DEFAULT_TRACK_IMG
        print("found:", filename)
        return filename

    @staticmethod
    def get_existing(track):
        filename_track_id = (
            Config.TRACKS_IMG_FOLDER + get_hash(str(track.hash)) + ".jpg"
        )
        filename_album = Config.TRACKS_IMG_FOLDER + get_hash(track.album) + ".jpg"
        filename_mixed = (
            Config.TRACKS_IMG_FOLDER + get_hash(track.album + track.title) + ".jpg"
        )
        for fname in [filename_track_id, filename_album, filename_mixed]:
            if os.path.exists(fname):
                return fname
        return None

    @staticmethod
    def get_from_id3_tags(track_id):
        hash = get_hash(str(track_id))
        filename = Config.TRACKS_IMG_FOLDER + hash + ".jpg"
        if os.path.exists(filename):  # if file alreadw exists we return it
            return filename

        tags = ID3(Config.TRACKS_FOLDER + "%06d.mp3" % track_id)
        try:
            img_data = tags.get("APIC:").data
            with open(filename, "wb") as fd:
                fd.write(img_data)
            return filename
        except:
            print("No id3 tag")
            return None

    @staticmethod
    def search_from_album(album):
        hash = get_hash(album)
        filename = Config.TRACKS_IMG_FOLDER + hash + ".jpg"
        if os.path.exists(filename):  # if file alreadw exists we return it
            return filename

        sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        # first we search with album name + track title
        result = sp.search(q=album, type="album", limit=1)
        try:
            url = [
                e for e in result["albums"]["items"][0]["images"] if e["width"] == 300
            ][0]["url"]
            img_data = requests.get(url).content
            with open(filename, "wb") as fd:
                fd.write(img_data)
            return filename
        except Exception as e:
            print("No spotify album found")
        return None

    @staticmethod
    def search_from_full_track(album, title):
        hash = get_hash(album + title)
        filename = Config.TRACKS_IMG_FOLDER + hash + ".jpg"
        if os.path.exists(filename):  # if file alreadw exists we return it
            return filename

        sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        # first we search with album name + track title
        result = sp.search(q=album + " " + title, type="track", limit=1)
        try:
            url = [
                e
                for e in result["tracks"]["items"][0]["album"]["images"]
                if e["width"] == 300
            ][0]["url"]
            img_data = requests.get(url).content
            with open(filename, "wb") as fd:
                fd.write(img_data)
            return filename
        except Exception as e:
            print("No spotify album + title found")
            pass
        # first we search with album name + track title
        result = sp.search(q=title, type="track", limit=1)
        try:
            url = [
                e
                for e in result["tracks"]["items"][0]["album"]["images"]
                if e["width"] == 300
            ][0]["url"]
            img_data = requests.get(url).content
            with open(filename, "wb") as fd:
                fd.write(img_data)
            return filename
        except Exception as e:
            print("No spotify track found")
            pass
        return None


if __name__ == "__main__":
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    result = sp.search(q="thriller", type="track", limit=1)
    print(result)
