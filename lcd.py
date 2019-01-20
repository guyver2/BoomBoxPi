#!/usr/bin/python
import time
import Adafruit_CharLCD as LCD
import threading

# Raspberry Pi pin configuration:
lcd_rs        = 17
lcd_en        = 4
lcd_d4        = 27
lcd_d5        = 22
lcd_d6        = 23
lcd_d7        = 24
lcdBacklight = 19
lcdColumns = 16
lcdRows    = 2
enablePWM = False
invertPolarity = False
initialIntensity = 0.1


class LCDScreen():
    def __init__(self):
        self.lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                        lcd_d7, lcdColumns, lcdRows,
                                        lcdBacklight, invertPolarity, enablePWM)
        self.lcd.set_backlight(initialIntensity)
        self.lcd.show_cursor(False)
        self.lcd.blink(False)
        
        self.lcd.message("2|12 Au clair de \n50%|----->     |")
    
    def update(self, player):
        self.lcd.clear()
        message = self.buildMessage(player)
        self.lcd.message(message)
            
    def buildMessage(self, player):
        res = "None"
        if player.currentTrack != None:
            res =  player.currentPlaylist.name + " "
            res += str(player.currentPlaylist.trackID+1) + "/"
            res += str(len(player.currentPlaylist.tracks)) + " "
            res += player.currentTrack.title + " "
            res += "%d.%d"%self.toMinAndSec(player.getTrackPos()) + "/"
            res += str(player.currentTrack.length)
        return res
    
    def toMinAndSec(self, timeInMS):
        timeInSec = timeInMS / 1000
        mins = timeInSec / 60
        secs = timeInSec % 60
        return (mins, secs)
    
    def setIntensity(self, value):
        self.lcd.set_backlight(value)
        
