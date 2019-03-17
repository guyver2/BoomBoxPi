import smbus
import time
import thread

bus = smbus.SMBus(1)  # RPi revision 2 (0 for revision 1)
i2c_address = 0x4d # got it from i2cdetect -y 1
control_byte = 0x01 # to read channel 0


class Potentiometer:
	def __init__(self, player):
		self.lock = False
		self.player = player
		self.value = None
		if player is not None:
			thread.start_new_thread(Potentiometer.watchdog, (self,))

	def lockUnlock(self):
		self.lock = not self.lock

	def watchdog(self):
		while self.player.alive:
            		data = int(bus.read_byte_data(i2c_address, control_byte))
			if self.value != data:
				if not self.lock:
					self.player.setVolume(data*3)
				self.value = data
			time.sleep(0.05)
