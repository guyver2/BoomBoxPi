import io
import fcntl
import time
import threading

i2c_address = 0x4D  # got it from i2cdetect -y 1
I2C_SLAVE_COMMAND = 0x0703
# set device address
FileHandle = io.open("/dev/i2c-1", "rb", buffering=0)
fcntl.ioctl(FileHandle, I2C_SLAVE_COMMAND, i2c_address)


class Potentiometer:
    def __init__(self, player):
        self.lock = False
        self.player = player
        self.value = None
        if player is not None:
            self.thread = threading.Thread(target=self.watchdog)
            self.thread.start()
            pass

    def lockUnlock(self):
        self.lock = not self.lock

    def watchdog(self):
        global FileHandle
        while self.player.alive:
            values = list(FileHandle.read(2))
            data = (values[0] * 256 + values[1]) / 4
            if self.value == None or abs(self.value - data) > 3:
                if not self.lock:
                    self.player.setVolume(data / 20)
                self.value = data
            time.sleep(0.05)


if __name__ == "__main__":
    while True:
        value = list(FileHandle.read(2))
        data = (value[0] * 256 + value[1]) / 4
        print(data)
        time.sleep(0.1)
