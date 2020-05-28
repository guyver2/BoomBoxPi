import sqlite3
from sqlite3 import Error
from pibox import Track, Playlist
from config import Config
import glob
import os
import shutil
from pathlib import Path
from mutagen.easyid3 import EasyID3
import hashlib
import json


def get_hash(filename):
    BLOCK_SIZE = 65536
    hash = hashlib.sha1()
    with open(filename, "rb") as fd:
        data = fd.read(BLOCK_SIZE)
        while len(data) > 0:
            hash.update(data)
            data = fd.read(BLOCK_SIZE)
    return hash.hexdigest()[:8]


def extract_tags(filename):
    tag = EasyID3(filename)
    try:
        title = tag["title"][0]
        if isinstance(title, bytes):
            title = title.decode("ASCII")
    except:
        title = Path(filename).stem
    try:
        artist = tag["artist"][0]
        if isinstance(title, bytes):
            artist = artist.decode("ASCII")
    except:
        artist = "Unknown"
    try:
        album = tag["album"][0]
        if isinstance(album, bytes):
            album = album.decode("ASCII")
    except:
        album = "Unknown"
    return (title, artist, album)


class BoomboxDB:

    def __init__(self):
        self.db_file = Config.DATA + "boombox.db"
        self.connection = None
        self.create_connection()
        self.create_table_if_needed()

    def close(self):
        if self.connection is not None:
            self.connection.close()

    def create_connection(self):
        """ create a database connection to the SQLite database
            specified by self.db_file
        """
        self.connection = None
        try:
            self.connection = sqlite3.connect(self.db_file)
        except Error as e:
            print(e)

    def create_table(self, sql):
        """ create a table from the create_table_sql statement
        :param sql: a CREATE TABLE statement
        """
        try:
            c = self.connection.cursor()
            c.execute(sql)
        except Error as e:
            print(e)

    def create_table_if_needed(self):
        sql_create_tracks_table = """ CREATE TABLE IF NOT EXISTS tracks (
                                            id integer PRIMARY KEY,
                                            title text NOT NULL,
                                            artist text NOT NULL,
                                            album text NOT NULL,
                                            cover text,
                                            hidden integer DEFAULT 0,
                                            nb_plays integer DEFAULT 0,
                                            sha1 text NOT NULL UNIQUE
                                        );"""

        sql_create_playlists_table = """CREATE TABLE IF NOT EXISTS playlists (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL UNIQUE, 
                                        hidden integer DEFAULT 0
                                    );"""

        sql_create_playlists_songs_table = """CREATE TABLE IF NOT EXISTS playlists_tracks (
                                        playlist_id INTEGER,
                                        track_id INTEGER,
                                        FOREIGN KEY (playlist_id) REFERENCES playlists (id),
                                        FOREIGN KEY (track_id) REFERENCES tracks (id),
                                        UNIQUE(playlist_id, track_id)
                                    );"""

        sql_create_web_radios_table = """CREATE TABLE IF NOT EXISTS webradios (
                                        id INTEGER PRIMARY KEY,
                                        name text NOT NULL UNIQUE,
                                        url text NOT NULL UNIQUE,
                                        cover text
                                    );"""

        # create tables
        self.create_table(sql_create_tracks_table)
        self.create_table(sql_create_playlists_table)
        self.create_table(sql_create_playlists_songs_table)
        self.create_table(sql_create_web_radios_table)

    def get_tracks_from_playlist(self, playlist_id):
        sql_search_tracks = """SELECT id, title, artist, album, hidden, nb_plays, cover
                               FROM tracks WHERE id IN 
                               (SELECT track_id from playlists_tracks 
                                WHERE playlist_id IS ?);"""
        cur = self.connection.cursor()
        cur.execute(sql_search_tracks, (playlist_id,))
        rows = cur.fetchall()
        result = []
        for row in rows:
            result.append(
                Track(row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
        return result

    def add_web_radio(self, name, url, cover=None):
        try:
            if cover is None:
                cover = Config.DEFAULT_WR_IMG
            sql = """ INSERT INTO webradios(name, url, cover)
                    VALUES(?,?,?)"""
            cur = self.connection.cursor()
            cur.execute(sql, (name,))
            print("new web radio", name, url)
            return True, cur.lastrowid
        except Exception as e:
            print("Error with web radio", name, e)
            return False, None

    def get_web_radios(self):
        sql_search = """SELECT id, name, url, cover FROM webradios;"""
        cur = self.connection.cursor()
        cur.execute(sql_search)
        rows = cur.fetchall()
        result = []
        for row in rows:
            result.append([
                row[0], row[1], row[2],
                Config.DEFAULT_WR_IMG if row[3] is None else row[3]
            ])
        return result

    def get_web_radio(self, rid):
        sql_search = """SELECT id, name, url, cover FROM webradios WHERE id=?;"""
        cur = self.connection.cursor()
        cur.execute(sql_search, (rid,))
        rows = cur.fetchall()
        for row in rows:
            return [
                row[0], row[1], row[2],
                Config.DEFAULT_WR_IMG if row[3] is None else row[3]
            ]
        return None

    def get_web_radios_json(self):
        return self.get_web_radios()

    def get_track(self, track_id):
        sql_search_tracks = """SELECT id, title, artist, album, hidden, nb_plays, cover
                               FROM tracks WHERE id=?;"""
        cur = self.connection.cursor()
        cur.execute(sql_search_tracks, (track_id,))
        rows = cur.fetchall()
        result = None
        for row in rows:
            result = Track(row[0], row[1], row[2], row[3], row[4], row[5],
                           row[6])
        return result

    def update_covers(self):
        from cover_manager import CoverManager

        sql_search_tracks = """SELECT id, title, artist, album, hidden, nb_plays, cover
                               FROM tracks;"""
        cur = self.connection.cursor()
        cur.execute(sql_search_tracks)
        rows = cur.fetchall()
        result = None
        for row in rows:
            if row[6] is None:
                print("updating cover for ", row[1], row[3])
                track = Track(row[0], row[1], row[2], row[3], row[4], row[5],
                              row[6])
                track.cover = CoverManager.get_cover(track)
                self.connection.execute("UPDATE tracks SET cover=? WHERE id=?",
                                        (track.cover, track.hash))
        self.connection.commit()
        return result

    def get_tracks_from_playlist_json(self, playlist_id):
        sql_search_tracks = """SELECT id, title, artist, album, hidden, nb_plays, cover
                               FROM tracks WHERE id IN 
                               (SELECT track_id from playlists_tracks 
                                WHERE playlist_id IS ?);"""
        cur = self.connection.cursor()
        cur.execute(sql_search_tracks, (playlist_id,))
        rows = cur.fetchall()
        result = []
        for row in rows:
            track = Track(row[0], row[1], row[2], row[3], row[4], row[5],
                          row[6])
            result.append(track.toDict())
        return result

    def get_tracks_id_from_playlist_json(self, playlist_id):
        sql_search_tracks = """SELECT track_id from playlists_tracks 
                                WHERE playlist_id IS ?;"""
        cur = self.connection.cursor()
        cur.execute(sql_search_tracks, (playlist_id,))
        rows = cur.fetchall()
        result = {"playlist_id": playlist_id}
        tracks_id = []
        for row in rows:
            tracks_id.append(row[0])
        result["tracks_id"] = tracks_id
        return result

    def get_tracks_json(self, track_id):
        sql_search_tracks = """SELECT id, title, artist, album, hidden, nb_plays, cover
                               FROM tracks WHERE id=?;"""
        cur = self.connection.cursor()
        cur.execute(sql_search_tracks, (track_id,))
        rows = cur.fetchall()
        for row in rows:
            track = Track(row[0], row[1], row[2], row[3], row[4], row[5],
                          row[6])
            return track.toDict()
        return {}

    def get_playlists(self, pid=None):
        sql_search = """SELECT id, name, hidden from playlists;"""
        if pid is not None:
            sql_search = """SELECT id, name, hidden from playlists WHERE id=%d;""" % pid
        cur = self.connection.cursor()
        cur.execute(sql_search)
        rows = cur.fetchall()
        result = []
        for row in rows:
            tracks = self.get_tracks_from_playlist(row[0])
            result.append(
                Playlist(row[0], row[1].replace("_", " "), tracks, row[2]))
        if pid is None:
            return result
        elif len(result) > 0:
            return result[0]
        else:
            return None

    def get_playlists_no_tracks(self):
        sql_search = """SELECT id, name, hidden from playlists;"""
        cur = self.connection.cursor()
        cur.execute(sql_search)
        rows = cur.fetchall()
        result = []
        for row in rows:
            result.append((row[0], row[1].replace("_",
                                                  " "), row[2], "default.jpg"))
        return result

    def get_playlists_json(self, playlist_id=None):
        cur = self.connection.cursor()
        if playlist_id is None:
            sql_search = """SELECT id, name, hidden FROM playlists;"""
            cur.execute(sql_search)
            rows = cur.fetchall()
            result = []
            for row in rows:
                result.append({
                    "id":
                        row[0],
                    "name":
                        row[1],
                    "hidden":
                        row[2],
                    "tracks": [{
                        "id": tid,
                        "url": "data/?q=track&tid=" + str(tid)
                    } for tid in self.get_tracks_id_from_playlist_json(row[0])
                               ["tracks_id"]],
                })
            return {"playlists": result}
        else:
            sql_search = """SELECT id, name, hidden FROM playlists WHERE id=?"""
            cur.execute(sql_search, (playlist_id,))
            rows = cur.fetchall()
            result = {}
            for row in rows:
                result["id"] = row[0]
                result["name"] = row[1]
                result["hidden"] = row[2]
                result["tracks"] = [
                    "data/?q=track&tid=" + str(tid) for tid in
                    self.get_tracks_id_from_playlist_json(row[0])["tracks_id"]
                ]

            return result

    def get_playlist_uid(self, name):
        cur = self.connection.cursor()
        cur.execute("SELECT id FROM playlists WHERE name=?", (name,))
        rows = cur.fetchall()
        if len(rows) == 0:
            return None
        else:
            return rows[0][0]

    def add_playlist(self, name):
        """
        Create a new playlist
        :return: (is it a new playlist), playlist uid
        """
        try:
            sql = """ INSERT INTO playlists(name)
                    VALUES(?)"""
            cur = self.connection.cursor()
            cur.execute(sql, (name,))
            print("new playlist " + name)
            return True, cur.lastrowid
        except Exception as e:
            print("Error with playlist " + name + str(e))
            return False, self.get_playlist_uid(name)

    def get_track_uid(self, sha1):
        cur = self.connection.cursor()
        cur.execute("SELECT id FROM tracks WHERE sha1=?", (sha1,))
        rows = cur.fetchall()
        if len(rows) == 0:
            return None
        else:
            return rows[0][0]

    def add_track(self, title, artist, album, sha1):
        """
        Create a new track
        :return: (is it a new track), track uid
        """
        try:
            sql = """ INSERT INTO tracks(title, artist, album, sha1)
                    VALUES(?,?,?,?)"""
            cur = self.connection.cursor()
            cur.execute(sql, (title, artist, album, sha1))
            print("new track " + title)
            return True, cur.lastrowid
        except Exception as e:
            print("Error with track " + title + str(e))
            return False, self.get_track_uid(sha1)

    def delete_track(self, track_id):
        """
        Delete a track an removes it from all playlists
        """
        try:
            sql = """DELETE FROM tracks WHERE id = ?"""
            cur = self.connection.cursor()
            cur.execute(sql, (track_id,))
            sql = """DELETE FROM playlists_tracks WHERE track_id = ?"""
            cur = self.connection.cursor()
            cur.execute(sql, (track_id,))
        except Exception as e:
            print("Error while removing track ", track_id, str(e))

    def add_song_to_playlist(self, playlist_id, track_id):
        try:
            sql = """ INSERT INTO playlists_tracks(playlist_id, track_id)
                    VALUES(?,?)"""
            cur = self.connection.cursor()
            cur.execute(sql, (playlist_id, track_id))
            return cur.lastrowid
        except:
            return None

    def process_dump(self):
        """ process all files in the dump folder and add them to the DB.
            All first level folders are treated as playlists.
        """
        new_playlists = {}
        for playlist_dir in glob.glob(Config.DUMP_FOLDER + "*"):
            if os.path.isdir(playlist_dir):
                name = os.path.basename(playlist_dir)
                _, new_playlists[name] = self.add_playlist(name)
        self.connection.commit()

        for track_file in Path(Config.DUMP_FOLDER).rglob("*.mp3"):
            track_file = str(track_file)
            if os.path.isfile(track_file):
                local_filename = track_file[len(Config.DUMP_FOLDER):]
                local_filename = local_filename.replace("\\", "/")
                # add track
                title, artist, album = extract_tags(track_file)
                sha1 = get_hash(track_file)
                new_track, track_id = self.add_track(title, artist, album, sha1)
                # check if the track belongs to a playlist
                parts = local_filename.split("/")
                if len(parts) > 1:
                    playlist = parts[0]
                    self.add_song_to_playlist(new_playlists[playlist], track_id)
                    print("song %s from %s" % (title, playlist))
                else:
                    print("song %s" % (title,))
            if track_id is not None and new_track:
                try:
                    shutil.move(track_file,
                                Config.TRACKS_FOLDER + "%06d.mp3" % track_id)
                except Exception as _:
                    self.delete_track(track_id)
        self.connection.commit()


if __name__ == "__main__":
    bbdb = BoomboxDB()
    bbdb.process_dump()
    pl = bbdb.get_playlists()
