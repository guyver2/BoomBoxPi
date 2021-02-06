import os
if os.name == "nt":
    RPI_MODE = False
else:
    RPI_MODE = True

try:
    from localConfig import LocalConfig as Config
except:
    from config import Config
if Config.FAKE:
    RPI_MODE = False

from flask import Flask, redirect
from flask import render_template, request, send_from_directory, jsonify
import os
import time
from pathlib import Path
import alsaaudio
import requests

from boomboxDB import BoomboxDB
from pibox import Player, Playlist
from cover_manager import CoverManager

if RPI_MODE:
    from button import Button
    from pot import Potentiometer
    from nfc import NFC
else:
    from fake import Button, Potentiometer, NFC

#set volume to 100% using alsamixer
mixer = alsaaudio.Mixer("PCM")
mixer.setvolume(100, 0)
mixer.setvolume(100, 1)

app = Flask(__name__)

player = None
buttons = []
pot = None
nfc = None


def getStatus(base_url):
    return {
        "base_url":
            base_url,
        "playlist":
            player.currentPlaylist.toDict(),
        "track":
            None
            if player.currentTrack is None else player.currentTrack.toDict(),
        "isPlaying":
            player.playing,
        "isPaused":
            player.paused,
        "lock":
            pot.lock,
        "mute":
            player.muted,
        "volume":
            player.getVolume(),
        "nfc":
            nfc.mode,
    }


@app.route("/js/<path:path>")
def send_js(path):
    return send_from_directory("js", path)


@app.route("/css/<path:path>")
def send_css(path):
    return send_from_directory("css", path)


@app.route("/img/<path:path>")
def send_img(path):
    return send_from_directory("img", path)


@app.route("/covers/track/<path:path>")
def send_track_cover(path):
    return send_from_directory(Config.TRACKS_IMG_FOLDER, path)


@app.route("/covers/playlist/<path:path>")
def send_playlist_cover(path):
    return send_from_directory(Config.PLAYLISTS_IMG_FOLDER, path)


@app.route("/covers/radio/<path:path>")
def send_webradio_cover(path):
    return send_from_directory(Config.WEBRADIOS_IMG_FOLDER, path)


@app.route("/api/", methods=["GET"])
def api_index():
    global player
    global pot
    global nfc

    try:
        q = request.args.get("q")
        if q == "status":
            return jsonify(getStatus(request.url_root))
        elif q == "volume":
            player.setVolume(int(float(request.args.get("value"))))
            return {}
        elif q == "play":
            player.play()
        elif q == "pause":
            player.pause()
        elif q == "playPause":
            player.playPause()
        elif q == "nextSong":
            player.next()
        elif q == "previousSong":
            player.prev()
        elif q == "nextPlayList":
            player.nextPlaylist()
        elif q == "previousPlayList":
            player.prevPlaylist()
        elif q == "lock":
            if not pot.lock:
                for b in buttons:
                    b.lockUnlock()
                pot.lockUnlock()
        elif q == "unlock":
            if pot.lock:
                for b in buttons:
                    b.lockUnlock()
                pot.lockUnlock()
        elif q == "mute":
            player.mute()
        elif q == "unmute":
            player.unmute()
        elif q == "nfcTrack":
            track_hash = request.args.get("hash")
            if track_hash is not None:
                nfc.write("t " + track_hash)
        elif q == "nfcPlaylist":
            pls_hash = request.args.get("hash")
            if pls_hash is not None:
                nfc.write("p " + pls_hash)
        elif q == "request":
            req = request.args.get("value")
            player.request(req)
    except Exception as e:
        return jsonify({
            "status": False,
            "error": "Could not understand request\n" + str(e)
        })

    return jsonify(getStatus(request.url_root))


@app.route("/data/", methods=["GET"])
def data():
    boomboxDB = BoomboxDB()
    try:
        q = request.args.get("q")
        if q == "playlist":
            pid = request.args.get("pid")
            result = boomboxDB.get_playlists_json(pid)
            result["base_url"] = request.url_root
            return jsonify(result)
        if q == "track":
            tid = request.args.get("tid")
            if tid is None:
                raise Exception("A track ID is needed")
            result = boomboxDB.get_tracks_json(tid)
            result["base_url"] = request.url_root
            return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": False,
            "error": "Could not understand request\n" + str(e)
        })
    return jsonify({"status": False, "error": "no request"})


@app.route("/", methods=["GET", "POST"])
def index():
    global player
    np = player.nowPlaying().replace("_", " ")
    locked = pot.lock
    muted = player.muted
    volume = player.getVolume()
    return render_template("index.html",
                           now_playing=np,
                           volume=volume,
                           locked=locked,
                           muted=muted)


@app.route("/playlist", methods=["GET", "POST"])
def playlist_page():
    try:
        pid = request.args.get("pid")
        if pid is None:
            cover_url = request.url_root + "covers/playlist/"
            boomboxDB = BoomboxDB()
            playlists = boomboxDB.get_playlists_no_tracks()
            return render_template("playlists_list.html",
                                   playlists=playlists,
                                   cover_base_url=cover_url,
                                   base_url=request.url_root)
        else:
            pid = int(pid)
            cover_url = request.url_root + "covers/track/"
            boomboxDB = BoomboxDB()
            pl = boomboxDB.get_playlists(int(pid))
            tracks = [(t.hash, t.title, cover_url + Path(t.cover).name)
                      for t in pl.tracks]
            return render_template("playlist.html",
                                   pid=pid,
                                   title=pl.name,
                                   tracks=tracks,
                                   base_url=request.url_root)
    except Exception as e:
        return jsonify({
            "status": False,
            "error": "Could not understand request\n" + str(e)
        })


@app.route("/radios", methods=["GET", "POST"])
def radio_page():
    print("showing webradios")
    try:
        cover_url = request.url_root + "covers/radio/"
        boomboxDB = BoomboxDB()
        radios = boomboxDB.get_web_radios()
        for radio in radios:
            radio[3] = Path(radio[3]).name
        print(radios)
        return render_template("radios_list.html",
                               radios=radios,
                               cover_base_url=cover_url,
                               base_url=request.url_root)
    except Exception as e:
        return jsonify({
            "status": False,
            "error": "Could not understand request: " + str(e)
        })


@app.route("/search", methods=["GET", "POST"])
def search_page():
    value = request.args.get("value")
    if value is None:
        return redirect("/")
    try:
        search_result = BoomboxDB().search(value)
        playlists = search_result["playlists"]
        cover_pls_url = request.url_root + "covers/playlist/"
        tracks = search_result["tracks"]
        cover_track_url = request.url_root + "covers/track/"
        tracks = [{
            "id": t["id"],
            "title": t["title"],
            "cover": cover_track_url + Path(t["cover"]).name,
        } for t in tracks]
        return render_template("search_result.html",
                               playlists=playlists,
                               tracks=tracks,
                               cover_pls_url=cover_pls_url,
                               cover_track_url=cover_track_url,
                               base_url=request.url_root)
    except Exception as e:
        print(e)
        return redirect("/")


def startSignal():
    global buttons
    for b in buttons:
        b.on()
        time.sleep(0.2)
    for b in buttons:
        b.off()
        time.sleep(0.2)


if __name__ == "__main__":
    boomboxDB = BoomboxDB()
    boomboxDB.process_dump()
    boomboxDB.update_covers()
    playlists = boomboxDB.get_playlists()
    del boomboxDB

    player = Player(playlists)

    but0 = Button(24, 13, 0, player)
    but1 = Button(25, 5, 1, player)
    but2 = Button(23, 6, 2, player)
    but3 = Button(27, 12, 3, player)
    buttons = [but0, but1, but3, but2]
    startSignal()
    pot = Potentiometer(player)
    nfc = NFC(player, buttons)

    app.run(host="0.0.0.0")
