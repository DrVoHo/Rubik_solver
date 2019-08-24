# button.py

import RPi.GPIO as GPIO
import time
from threading import Thread

# Button event constants
BUTTON_PRESSED = 1
BUTTON_RELEASED = 2
BUTTON_LONGPRESSED = 3
BUTTON_CLICKED = 4
BUTTON_DOUBLECLICKED = 5
BUTTON_LONGPRESS_DURATION = 2 # default (in s) the button must be pressed to be a long press
BUTTON_DOUBLECLICK_TIME = 1 # default time (in s) to wait for a double click event

# --------------- class ClickThread -------------------------------
class ClickThread(Thread):
    def __init__(self, button):
        Thread.__init__(self)
        self.start()
        self.button = button

    def run(self):
        if Button.DEBUG:
            print ("===>ClickThread started")
        self.isRunning = True
        startTime = time.time()
        while self.isRunning and (time.time() - startTime < BUTTON_DOUBLECLICK_TIME):
            time.sleep(0.1)
        if self.button.clickCount == 1 and not self.button.isLongPressEvent:
            if self.button.xButtonListener != None:
                self.button.xButtonListener(self.button, BUTTON_CLICKED)
            self.button.clickThread = None
        self.isRunning  = False
        if Button.DEBUG:
            print ("===>ClickThread terminated")

    def stop(self):
        self.isRunning = False

# --------------- class ButtonThread ------------------------------
class ButtonThread(Thread):
    def __init__(self, button):
        Thread.__init__(self)
        self.isRunning = False
        self.button = button

    def run(self):
        if Button.DEBUG:
            print ("===>ButtonThread started")
        self.isRunning = True
        startTime = time.time()
        while self.isRunning and (time.time() - startTime < BUTTON_LONGPRESS_DURATION):
            time.sleep(0.1)
        if self.isRunning:
            if self.button.buttonListener != None:
                self.button.buttonListener(self.button, BUTTON_LONGPRESSED)
        if Button.DEBUG:
            print ("===>ButtonThread terminated")

    def stop(self):
        self.isRunning = False

# --------------- class Button ------------------------------------
class Button():
    DEBUG = False
    def __init__(self, buttonPin):
        self.buttonListener = None
        self.xButtonListener = None
        self.buttonThread = None
        self.clickThread = None
        self.clickCount = 0
        self.isLongPressEvent = False
        self.buttonPin = buttonPin
        GPIO.setup(self.buttonPin, GPIO.IN, GPIO.PUD_UP)
        GPIO.add_event_detect(self.buttonPin, GPIO.BOTH, self.onButtonEvent)
    
    def onXButtonEvent(self, button, event):
        if event == BUTTON_PRESSED:
            if self.buttonListener != None:
                self.xButtonListener(button, BUTTON_PRESSED)
            self.isLongPressEvent = False
            if self.clickThread == None:
                self.clickCount = 0
                self.clickThread = ClickThread(self)
        elif event == BUTTON_RELEASED:
            if self.xButtonListener != None:
                self.xButtonListener(button, BUTTON_RELEASED)
            if self.isLongPressEvent and self.clickThread != None:
                self.clickThread.stop()
                self.clickThread = None
                return
            if self.clickThread != None and self.clickThread.isRunning:
                self.clickCount += 1
                if self.clickCount == 2:
                    self.clickThread.stop()
                    self.clickThread = None
                    if self.xButtonListener != None:
                        self.xButtonListener(button, BUTTON_DOUBLECLICKED)
            else:
                self.clickThread = None
        elif event == BUTTON_LONGPRESSED:
            self.isLongPressEvent = True
            if self.xButtonListener != None:
                self.xButtonListener(self, BUTTON_LONGPRESSED)

    def onButtonEvent(self, channel):
        # switch may bounce: down-up-up, down-up-down, down-down-up etc. in fast sequence
        if GPIO.input(self.buttonPin) == GPIO.LOW:
            if self.buttonThread == None: # down-down is suppressed
                if Button.DEBUG:
                    print ("->ButtonDown")
                self.buttonThread = ButtonThread(self)
                self.buttonThread.start()
                if self.buttonListener != None:
                    self.buttonListener(self, BUTTON_PRESSED)
        else:
            if self.buttonThread != None: # up-up is suppressed
                if Button.DEBUG:
                    print ("->ButtonUp")
                self.buttonThread.stop()
                self.buttonThread.join(200) # wait until finished
                self.buttonThread = None
                if self.buttonListener != None:
                    self.buttonListener(self, BUTTON_RELEASED)

    def addXButtonListener(self, listener):
        self.addButtonListener(self.onXButtonEvent)
        self.xButtonListener = listener

    def addButtonListener(self, listener):
        self.buttonListener = listener


