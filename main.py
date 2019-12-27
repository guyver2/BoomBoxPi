from flask import Flask
from flask import render_template, request, send_from_directory
import os
if os.name == 'nt':
    RPI_MODE = False
else:
    RPI_MODE = True
import threading
import glob
import os
import time
from pibox import Player, Playlist, importPlaylists


if RPI_MODE:
    from button import Button
    from pot import Potentiometer
    from nfc import NFC
else:
    from fake import Button, Potentiometer, NFC


app = Flask(__name__)

player = None
lock = False
buttons = []
pot = None
nfc = None


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)


@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)


@app.route('/img/<path:path>')
def send_img(path):
    return send_from_directory('img', path)


@app.route("/", methods=['GET', 'POST'])
def index():
    global player
    global lock
    global nfc
    try:
        volume = request.form['volume']
    except:
        volume = player.getVolume()

    print(request.form)

    if "next" in request.form:
        player.next()
    if "prev" in request.form:
        player.prev()
    if "play" in request.form:
        player.playPause()
    if "volume" in request.form:
        player.setVolume(int(request.form["volume"]))
    if "lock" in request.form:
        for b in buttons:
            b.lockUnlock()
        pot.lockUnlock()
    if "mute" in request.form:
        player.setVolume(0)
    if "nextPlaylist" in request.form:
        player.nextPlaylist()
    if "NFC" in request.form:
        nfc.switchMode()

    np = player.nowPlaying()

    return render_template('index.html', now_playing=np, volume=volume)


send_from_directory


@app.route("/new", methods=['GET', 'POST'])
def newIndex():
    global player
    global lock
    try:
        volume = request.form['volume']
    except:
        volume = player.getVolume()

    print(request.form)

    if "next" in request.form:
        player.next()
    if "prev" in request.form:
        player.prev()
    if "play" in request.form:
        player.playPause()
    if "volume" in request.form:
        player.setVolume(int(request.form["volume"]))
    if "lock" in request.form:
        for b in buttons:
            b.lockUnlock()
        pot.lockUnlock()
    if "mute" in request.form:
        player.setVolume(0)
    if "nextPlaylist" in request.form:
        player.nextPlaylist()

    np = player.nowPlaying()

    return render_template('index_new.html', now_playing=np, volume=volume)


def startSignal():
    global buttons
    for b in buttons:
        b.on()
        time.sleep(0.2)
    for b in buttons:
        b.off()
        time.sleep(0.2)


if __name__ == "__main__":

    playlists = importPlaylists()

    player = Player(playlists)

    but0 = Button(24, 13, 0, player)
    but1 = Button(25, 5, 1, player)
    but2 = Button(23, 6, 2, player)
    but3 = Button(27, 12, 3, player)
    buttons = [but0, but1, but3, but2]
    startSignal()
    pot = Potentiometer(player)
    nfc = NFC(player)

    app.run(host='0.0.0.0')
