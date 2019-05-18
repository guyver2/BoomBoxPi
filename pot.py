import io
import fcntl
import time
import _thread

i2c_address = 0x4d # got it from i2cdetect -y 1
I2C_SLAVE_COMMAND=0x0703
# set device address
FileHandle =  io.open("/dev/i2c-1", "rb", buffering=0)
fcntl.ioctl(FileHandle, I2C_SLAVE_COMMAND, i2c_address)


class Potentiometer:
	def __init__(self, player):
		self.lock = False
		self.player = player
		self.value = None
		if player is not None:
			_thread.start_new_thread(Potentiometer.watchdog, (self,))

	def lockUnlock(self):
		self.lock = not self.lock

	def watchdog(self):
		global FileHandle
		while self.player.alive:
			values = list(FileHandle.read(2))
			data = (ord(values[0]) * 256 + ord(values[1])) / 4
			if self.value == None or abs(self.value - data) > 3:
				if not self.lock:
					self.player.setVolume(data/20)
				self.value = data
			time.sleep(0.05)
