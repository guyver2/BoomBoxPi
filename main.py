import os

if os.name == "nt":
    RPI_MODE = False
else:
    RPI_MODE = True
import threading

from flask import Flask
from flask import render_template, request, send_from_directory, jsonify
import glob
import os
import time
from boomboxDB import BoomboxDB
from pibox import Player, Playlist

if RPI_MODE:
    from button import Button
    from pot import Potentiometer
    from nfc import NFC
else:
    from fake import Button, Potentiometer, NFC

app = Flask(__name__)

player = None
buttons = []
pot = None
nfc = None


def getStatus():
    return {
        "playlist": player.currentPlaylist.toDict(),
        "track": player.currentTrack.toDict(),
        "isPlaying": player.playing,
        "isPaused": player.paused,
        "lock": pot.lock,
        "mute": player.muted == 0,
        "volume": player.getVolume(),
        "nfc": nfc.mode,
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


@app.route("/api/", methods=["GET"])
def api_index():
    global player
    global pot
    global nfc

    try:
        q = request.args.get("q")
        if q == "status":
            return jsonify(getStatus())
        elif q == "volume":
            player.setVolume(int(float(request.args.get("value"))))
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
            nfc.switchMode(NFC.WRITE_TRACK)
        elif q == "nfcPlaylist":
            nfc.switchMode(NFC.WRITE_PLAYLIST)
        elif q == "request":
            req = request.args.get("value")
            player.request(req)
    except Exception as e:
        return jsonify(
            {"status": False, "error": "Could not understand request\n" + str(e)}
        )

    return jsonify(getStatus())


@app.route("/", methods=["GET", "POST"])
def newIndex():
    global player
    np = player.nowPlaying().replace("_", " ")
    locked = pot.lock
    muted = player.muted
    volume = player.getVolume()
    playlists = [(p.hash, p.name.replace("_", " ")) for p in player.playlists]
    tracks = [
        (t.hash, t.title.replace("_", " ")) for t in player.currentPlaylist.tracks
    ]
    pid = player.currentPlaylist.hash
    tid = player.currentTrack.hash
    return render_template(
        "index_new.html",
        now_playing=np,
        volume=volume,
        locked=locked,
        muted=muted,
        playlists=playlists,
        pid=pid,
        tracks=tracks,
        tid=tid,
    )


def startSignal():
    global buttons
    for b in buttons:
        b.on()
        time.sleep(0.2)
    for b in buttons:
        b.off()
        time.sleep(0.2)


if __name__ == "__main__":
    bbdb = BoomboxDB()
    bbdb.process_dump()
    playlists = bbdb.get_playlists()

    player = Player(playlists)

    but0 = Button(24, 13, 0, player)
    but1 = Button(25, 5, 1, player)
    but2 = Button(23, 6, 2, player)
    but3 = Button(27, 12, 3, player)
    buttons = [but0, but1, but3, but2]
    startSignal()
    pot = Potentiometer(player)
    nfc = NFC(player)

    app.run(host="0.0.0.0")
