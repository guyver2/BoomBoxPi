import sqlite3
import glob
from pathlib import Path
from mutagen.easyid3 import EasyID3

connection = None
connection = sqlite3.connect("boombox.db")
connection.execute("alter table tracks add column 'album' 'text'")


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


for f in glob.glob("tracks/*.mp3"):
    print(f)
    tid = int(Path(f).stem)
    t, ar, al = extract_tags(f)
    print(tid, t, ar, al)
    connection.execute("UPDATE tracks SET album=? WHERE id=?", (al, tid))
connection.commit()
connection.close()
