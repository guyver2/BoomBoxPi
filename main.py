from flask import Flask
from flask import render_template, request
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
else:
    from fake import Button, Potentiometer


app = Flask(__name__)

player = None
lock = False
buttons = []
pot = None

@app.route("/", methods=['GET', 'POST'])
def index():
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

    return render_template('index.html', now_playing=np, volume=volume)



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

    if RPI_MODE:
        but0 = Button(24, 13, 0, player)
        but1 = Button(22, 5, 1, player)
        but2 = Button(23, 12, 2, player)
        but3 = Button(6, 27, 3, player)
        buttons = [but0, but1, but3, but2]
        startSignal()
        pot = Potentiometer(player)
    
    app.run(host='0.0.0.0')
