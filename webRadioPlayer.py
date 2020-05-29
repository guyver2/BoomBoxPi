import threading
import re
import subprocess
import alsaaudio


class WebRadioPlayer(object):

    def __init__(self):
        self.stream_url = None
        self.mpg123_process = None
        self.mixer = alsaaudio.Mixer("PCM")
        print(self.mixer.cardname(), self.mixer.mixer(), self.mixer.mixerid(),
              self.mixer.volumecap())
        self.volume = self.get_volume()
        self.muted = False

    def mute(self):
        self.muted = True
        self.set_volume(self.volume)

    def unmute(self):
        self.muted = False
        self.set_volume(self.volume)

    def get_volume(self):
        volume_left, volume_right = self.mixer.getvolume()
        return (volume_left + volume_right) // 2

    def set_volume(self, volume):
        self.volume = volume
        volume = 0 if self.muted else self.volume
        self.mixer.setvolume(int(volume), 0)
        self.mixer.setvolume(int(volume), 1)

    def play(self, stream_url):
        self.stream_url = stream_url
        cmd = ["mpg123", stream_url]
        self.mpg123_process = subprocess.Popen(cmd)

    def stop(self):
        if self.mpg123_process:
            self.mpg123_process.kill()
            self.mpg123_process = None

    def hard_stop(self):
        subprocess.Popen(['killall', 'mpg123'])


if __name__ == "__main__":
    import time
    import sys

    stream_url = "http://stream.srg-ssr.ch/m/couleur3/mp3_128"
    if len(sys.argv) != 2:
        print("using default station: couleur 3")
    else:
        stream_url = sys.argv[1]

    wrp = WebRadioPlayer()
    wrp.set_volume(10)
    wrp.play(stream_url)
    time.sleep(5)
    print("changing volume")
    wrp.set_volume(20)
    time.sleep(5)
    wrp.set_volume(30)
    time.sleep(5)
    wrp.set_volume(40)
    time.sleep(5)
    wrp.set_volume(50)
    input("press enter to quit")
    wrp.stop()
