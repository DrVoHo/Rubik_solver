#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


from PIL import ImageFont
from PIL import Image



#start Display as soon as possible "Boot"
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)


HOME = "/home/pi/"

#font = ImageFont.truetype(HOME + 'scripts/font/VCR_OSD_MONO_1.001.ttf',20)
font = ImageFont.truetype(HOME + 'VCR_OSD_MONO_1.001.ttf',20)

with canvas(device) as draw:
    draw.text((15, 15), "Boot ",font = font, fill="white")

from picamera import PiCamera

import RPi.GPIO as GPIO
import os, math

import time

import random

from threading import Thread

from button import  Button, BUTTON_PRESSED,  BUTTON_DOUBLECLICKED      

import kociemba


#_______________Konstanten________________

GPIO.setmode(GPIO.BOARD)       

PLUS_BUTTON = 11    # an die gewählten GPIO anpassen
MINUS_BUTTON = 13   # an die gewählten GPIO anpassen  
ENTER_BUTTON = 15  # an die gewählten GPIO anpassen

LINKS_DREH = 36   # an die gewählten GPIO anpassen
LINKS_GRIP = 37   # an die gewählten GPIO anpassen
RECHTS_DREH = 18  # an die gewählten GPIO anpassen
RECHTS_GRIP = 16  # an die gewählten GPIO anpassen

C180 = 0   # 1 = 180° Drehbewegung (mind. 270 ° Servo); else = 90° (standard)

GRIPPER_MAX = 65
GRIPPER_MIN = 0
TURN_MAX = 270   # max Drehwinkel des Servox  - limit for setup
TURN_MIN = 0

SLEEP_GRIP = 0.3
SLEEP_LONG_FAKTOR = 2

OVERSHOOT = 5 #overshoot at turning

fPWM = 50   # Servo PWM Frequenz; 20 ms Dauer

TURN_MAX_left_grip = 180
SERVO_PWM_left_grip = 10  # difference of servotiming in percentage of duration 
SERVO_OFFSET_left_grip = 2 # lower servo position in percentage of duration

TURN_MAX_left_turn = 180
SERVO_PWM_left_turn = 10  # difference of servotiming in percentage of duration 
SERVO_OFFSET_left_turn = 2 # lower servo position in percentage of duration

TURN_MAX_right_grip = 180
SERVO_PWM_right_grip = 10  # difference of servotiming in percentage of duration 
SERVO_OFFSET_right_grip = 2 # lower servo position in percentage of duration

TURN_MAX_right_turn = 180
SERVO_PWM_right_turn = 10  # difference of servotiming in percentage of duration 
SERVO_OFFSET_right_turn = 2 # lower servo position in percentage of duration

SCRAMBLE_MAX = 20


IMG_BREITE = 1080 
IMG_HOEHE = 1080

top_row_pxl = 250  #values for cube detection
mid_row_pxl = 500
bot_row_pxl = 750
lft_col_pxl = 200
mid_col_pxl = 450
rgt_col_pxl = 700

wb_row_pxl = 980 #area for white balance
wb_col_pxl = 890

pxl_locs = [[(lft_col_pxl, top_row_pxl),(mid_col_pxl, top_row_pxl),(rgt_col_pxl, top_row_pxl)],
            [(lft_col_pxl, mid_row_pxl),(mid_col_pxl, mid_row_pxl),(rgt_col_pxl, mid_row_pxl)],
            [(lft_col_pxl, bot_row_pxl),(mid_col_pxl, bot_row_pxl),(rgt_col_pxl, bot_row_pxl)]]


TARGET_STANDARD = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"



#____________________globale Variablen___________________________________

state_machine = 0   # 0 = Anzeige Start / Solve
                    # 1 = Anzeige Setup
                    # 2 = Anzeige Muster
                    # 3 = Display Scramble                    
                    # 10 = links grip einstellen
                    # 20 = links dreh einstellen
                    # 30 = rechts grip einstellen
                    # 40 = rechts dreh einstellen
                    # 50 = Load einstellen
                    # 60 = SLEEP (delay) einstellen
                    # 65 = regrip (prior to move a layer)
                    # 70 = 74 Pattern
                    # 75 = eigenes Muster
                    # 76 = eigenes Muster starten
                    # 77 = eigenes Muster scannen
                    # 80 = scramble
                    # 98 = Display during scambling                    
                    # 99 = running
                    
timer_time = 0   #Laufvariable des Time Thread
  
l_pos = 90 #position of left Servo
r_pos = 90

links_grip_tune = 0 #adapted in setup
links_dreh_tune = 0
rechts_grip_tune = 0
rechts_dreh_tune = 0

LOAD = 30 #Load position; adapted in setup (cube is released) 
SLEEP = 0.5 #Delay for servos; adapted in setup
     
masterstring = ""  #long string of all servo moves
solve_string = ""  #result from solver
solve_array = []   #array of solver_string moves            

Target_string = TARGET_STANDARD
Own_pattern = TARGET_STANDARD

regrip_stat = 1

scramble_count = 0

message = ""

 #____________________________________________________timer__________________
 
def my_timer():
    global timer_time
    i=1
    while i == 1:
        timer_time += 0.1
        time.sleep(0.1)
         
#__________________________________________________________Servos________________________________________________
     

def setup_servos():
    global links_turn_servo 
    global links_grip_servo 
    global rechts_turn_servo
    global rechts_grip_servo
    
    GPIO.setup(LINKS_DREH, GPIO.OUT)
    GPIO.setup(LINKS_GRIP, GPIO.OUT)
    GPIO.setup(RECHTS_DREH, GPIO.OUT)
    GPIO.setup(RECHTS_GRIP, GPIO.OUT)
    
    links_turn_servo = GPIO.PWM(LINKS_DREH, fPWM) 
    links_grip_servo = GPIO.PWM(LINKS_GRIP, fPWM)
    rechts_turn_servo = GPIO.PWM(RECHTS_DREH, fPWM)
    rechts_grip_servo = GPIO.PWM(RECHTS_GRIP, fPWM)
    
    links_turn_servo.start(7)
    links_grip_servo.start(5)
    time.sleep(SLEEP)
    rechts_turn_servo.start(7)
    rechts_grip_servo.start(5)
    time.sleep(SLEEP)
    
      
def home_servos():
    global l_pos
    global r_pos
    setDirection_links_turn(90 + links_dreh_tune,1)
    setDirection_rechts_turn(90 + rechts_dreh_tune,1)
    time.sleep(SLEEP)
    regrip()    
    setDirection_links_grip(LOAD + links_grip_tune)
    setDirection_rechts_grip(LOAD + rechts_grip_tune)
    time.sleep(SLEEP)
    l_pos = 90
    r_pos = 90


def regrip():
    duty = SERVO_PWM_left_grip / TURN_MAX_left_grip * (LOAD + links_grip_tune) + SERVO_OFFSET_left_grip
    links_grip_servo.ChangeDutyCycle(duty)
    duty = SERVO_PWM_right_grip / TURN_MAX_right_grip * (LOAD + rechts_grip_tune) + SERVO_OFFSET_right_grip
    rechts_grip_servo.ChangeDutyCycle(duty)
    time.sleep(SLEEP/2)
    duty = SERVO_PWM_left_grip / TURN_MAX_left_grip * links_grip_tune + SERVO_OFFSET_left_grip
    links_grip_servo.ChangeDutyCycle(duty)
    duty = SERVO_PWM_right_grip / TURN_MAX_right_grip * rechts_grip_tune + SERVO_OFFSET_right_grip
    rechts_grip_servo.ChangeDutyCycle(duty)
    time.sleep(SLEEP/2)

def setDirection_links_turn(richtung, faktor): 
    duty = SERVO_PWM_left_turn / TURN_MAX_left_turn * (richtung  + OVERSHOOT) + SERVO_OFFSET_left_turn
    links_turn_servo.ChangeDutyCycle(duty)
    time.sleep(SLEEP*faktor) # allow to settle  
    
def setDirection_links_grip(richtung):
    duty = SERVO_PWM_left_grip / TURN_MAX_left_grip * richtung + SERVO_OFFSET_left_grip
    links_grip_servo.ChangeDutyCycle(duty)
    time.sleep(SLEEP_GRIP) # allow to settle 

    
def setDirection_rechts_turn(richtung,faktor):
    duty = SERVO_PWM_right_turn / TURN_MAX_right_turn * (richtung  + OVERSHOOT) + SERVO_OFFSET_right_turn
    rechts_turn_servo.ChangeDutyCycle(duty)
    time.sleep(SLEEP*faktor) # allow to settle 
 
    
def setDirection_rechts_grip(richtung):
    duty = SERVO_PWM_right_grip / TURN_MAX_right_grip * richtung + SERVO_OFFSET_right_grip
    rechts_grip_servo.ChangeDutyCycle(duty)
    time.sleep(SLEEP_GRIP) # allow to settle 



# L: links
# R: rechts
# M: Ebene drehen
# T: Wuerfel drehen
# p: plus (Uhrzeigersinn)
# m: minus
    
#A: links Greifer zu
#a: links Greifer auf
#B: Rechts Greifer zu
#b: Rechts Greifer auf
#M: Links 0
#N: Links 90
#O: Links 180
#X: Rechts 0
#Y: Rechts 90
#Z: Rechts 180
#R: Regrip
#t: Zähler count down

# convert macro moves into single action moves of servos
    
def LMp():  #dreht Ebene (move)
    if C180 == 1:
        return "OtaNA"
    else:
        return "aMANt"

def LMm():
    return "MtaNA"

def LMpp():
    if C180 == 1:
        return "aMAOtaNA" 
    else:
        return "aMANaMANt" 
    
def LTp():
    if C180 == 1:
        return "bOBaNA"
    else:
        return "aMAbNB"

def LTm():
    return "bMBaNA"

def LTpp():
    if C180 == 1:
        return "aMAbOBaNA" 
    else:
        return "aMAbNBaMAbNB"  
          
def RMp():
    if C180 == 1:
        return "ZtbYB"
    else:
        return "bXBYt"

def RMm():
    return "XtbYB"

def RMpp():
    if C180 == 1:
        return "bXBZtbYB"
    else:
        return "bXBYbXBYt"

def RTp():
    if C180 == 1:
        return "aZAbYB"
    else:
        return "bXBaYA"
    
def RTm():
    return "aXAbYB"
    
def RTpp():
    if C180 == 1:
        return "bXBaZAbYB" 
    else:
        return "bXBaYAbXBaYA"

    
#_______________________________________________________solve_moves______________________________________________


def single_action(action):
    global moves
    global l_pos
    global r_pos
    global regrip_stat
    if action =="A":
        setDirection_links_grip(links_grip_tune)
        
    elif action == "a":
        setDirection_links_grip(GRIPPER_MAX)
        
    elif action == "B":
        setDirection_rechts_grip(rechts_grip_tune)
        
    elif action =="b":
        setDirection_rechts_grip(GRIPPER_MAX)
        
    elif action == "M":
        if l_pos != 0:
            if l_pos == 90:
                sleep = 1
            else:
                sleep = SLEEP_LONG_FAKTOR
            setDirection_links_turn(0 + links_dreh_tune, sleep)
            l_pos = 0
            
    elif action == "N":
        if l_pos != 90:
            setDirection_links_turn(90 + links_dreh_tune, 1)
            l_pos = 90
            
    elif action == "O":
        if l_pos != 180:
            if l_pos == 90:
                sleep = 1
            else:
                sleep = SLEEP_LONG_FAKTOR
            setDirection_links_turn(180 + links_dreh_tune, sleep)
            l_pos = 180
            
    elif action == "X":
        if r_pos !=0:
            if r_pos == 90:
                sleep = 1
            else:
                sleep = SLEEP_LONG_FAKTOR
            setDirection_rechts_turn(0 + rechts_dreh_tune, sleep)
            r_pos = 0
            
    elif action == "Y":
        if r_pos !=90:
            setDirection_rechts_turn(90 + rechts_dreh_tune, 1)
            r_pos = 90
            
    elif action == "Z":
        if r_pos != 180:
            if r_pos == 90:
                sleep = 1
            else:
                sleep = SLEEP_LONG_FAKTOR
            setDirection_rechts_turn(180 + rechts_dreh_tune, sleep)
            r_pos = 180
            
    elif action == "R":
        if regrip_stat == 1:
            regrip()
        
    elif action == "t":
        moves -= 1


def move_cube(action):
    
    if action == "U":
        a1 = RTpp()
        a2 =LMp()
        correct_right()
        correct_right()
        dummy = a1 +  "R" +a2
    elif action == "U2":
        a1 = RTpp()
        a2 = LMpp()
        correct_right()
        correct_right()
        dummy =  a1 +  "R" + a2
    elif action == "U'":
        a1 = RTpp()
        a2 = LMm()
        correct_right()
        correct_right()
        dummy = a1 +  "R" + a2
    elif action == "R":
        a1 = RMp()
        dummy =  "R" + a1
    elif action == "R2":
        a1 = RMpp()
        dummy =  "R" + a1
    elif action == "R'":
        a1 = RMm()
        dummy =  "R" + a1
    elif action == "L":
        a1 = LTpp()
        a2 = RMp()
        correct_left()
        dummy = a1 +  "R" + a2
    elif action == "L2":
        a1 = LTpp()
        a2 = RMpp()
        correct_left()
        dummy = a1 +  "R" + a2
    elif action == "L'":
        a1 = LTpp()
        a2 = RMm()
        correct_left()
        dummy = a1 +  "R" +a2
    elif action == "F":
        a1 = RTm()
        a2 = LMp()
        correct_right()
        correct_right()
        correct_right()
        dummy = a1 +  "R" + a2
    elif action == "F2":
        a1 = RTm()
        a2 = LMpp()
        correct_right()
        correct_right()
        correct_right()
        dummy = a1 +  "R" + a2
    elif action == "F'":
        a1 = RTm()
        a2 = LMm()
        correct_right()
        correct_right()
        correct_right()
        dummy = a1 +  "R" +a2
    elif action == "B":
        a1 = RTp()
        a2 = LMp()
        correct_right()
        dummy = a1 +  "R" +a2
    elif action == "B2":
        a1 = RTp()
        a2 = LMpp()
        correct_right()
        dummy = a1 +  "R" +a2
    elif action == "B'":
        a1 = RTp()
        a2 = LMm()
        correct_right()
        dummy = a1 +  "R" + a2
    elif action == "D":
        a1 = LMp()
        dummy =  "R" + a1
    elif action == "D2":
        a1 = LMpp()
        dummy =  "R" + a1
    elif action == "D'":
        a1 = LMm()
        dummy =  "R" + a1
    else:
        print("finished")
        dummy = "finished"
    return dummy

def create_master_string():
    global solve_array
    global solve_sequenze
    
    solve_sequenze =""   
    
    for y in range(len(solve_array)):
        
        dummy = move_cube(solve_array[y])
        solve_sequenze = solve_sequenze + dummy  
      
    solve_sequenze = solve_sequenze.replace("MtaNAaMAbOBaNA", "MtbOBaNA")  #entfernt unnötige Greifer Drehung 180°
    solve_sequenze = solve_sequenze.replace("XtbYBbXBaZAbYB", "XtaZAbYB")  #entfernt unnötige Greifer Drehung 180°
    solve_sequenze = solve_sequenze.replace("OtaNAaMA","OtaMA")            #entfernt Zwischenstop Greifer Drehung   180°  
    solve_sequenze = solve_sequenze.replace("ZtbYBbXB","ZtbXB")            #entfernt Zwischenstop Greifer Drehung 180°
    solve_sequenze = solve_sequenze.replace("OtaMAbOBaNA","OtbMBaNA")      #entfernt unnötige 180° Greifer Drehung 180°
    solve_sequenze = solve_sequenze.replace("ZtbXBaZAbYB","ZtaXAbYB")      #entfernt unnötige 180° Greifer Drehung 180°
    solve_sequenze = solve_sequenze.replace("Aa","")                       #entfernt unnötiges Greifer auf/zu
    solve_sequenze = solve_sequenze.replace("Bb","")                       #entfernt unnötiges Greifer auf/zu
    solve_sequenze = solve_sequenze.replace("MtaNM","Mt")                  #entfernt unnötige Greifer Drehung 90°   
    solve_sequenze = solve_sequenze.replace("XtbYX","Xt")                  #entfernt unnötige Greifer Drehung 90°   


    
#______________________________________________________Drehkorrektur_______________________________________________

def correct_right(): #90° turn
    for x in range(len(solve_array)):
        solve_array[x] = solve_array[x].replace("U","X")    
        solve_array[x] = solve_array[x].replace("F","U")
        solve_array[x] = solve_array[x].replace("D","F") 
        solve_array[x] = solve_array[x].replace("B","D")
        solve_array[x] = solve_array[x].replace("X","B")      

def correct_left():  #180° turn
    for x in range(len(solve_array)):
        solve_array[x] = solve_array[x].replace("F","X")    
        solve_array[x] = solve_array[x].replace("B","F")  
        solve_array[x] = solve_array[x].replace("X","B")
        
        solve_array[x] = solve_array[x].replace("L","X") 
        solve_array[x] = solve_array[x].replace("R","L")
        solve_array[x] = solve_array[x].replace("X","R")   


#__________________________________________________________button__________________________________________________


def setup_button():
    global plus 
    global minus
    global enter
    GPIO.setup(PLUS_BUTTON, GPIO.IN, GPIO.PUD_UP)
    GPIO.setup(MINUS_BUTTON, GPIO.IN, GPIO.PUD_UP)
    GPIO.setup(ENTER_BUTTON, GPIO.IN, GPIO.PUD_UP)
    plus = Button(PLUS_BUTTON) 
    minus = Button(MINUS_BUTTON)
    enter = Button(ENTER_BUTTON)
    plus.addXButtonListener(onButtonEvent_plus)
    minus.addXButtonListener(onButtonEvent_minus)
    enter.addXButtonListener(onButtonEvent_enter)


def onButtonEvent_plus(plus, event):
    global state_machine
    global links_grip_tune
    global links_dreh_tune
    global rechts_grip_tune
    global rechts_dreh_tune
    global LOAD
    global SLEEP
    global message
    global regrip_stat
    global scramble_count    
    if event == BUTTON_PRESSED:
        dummy = state_machine
        if dummy == 0:
            state_machine = 1
        elif dummy == 1:
            state_machine = 2
        elif dummy == 2:
            state_machine = 3 
        elif dummy == 3:
            state_machine = 0
            message = "Start"
        elif state_machine == 10:  # links grip wird eingestellt
            links_grip_tune = links_grip_tune + 2
            if links_grip_tune > GRIPPER_MAX:
                links_grip_tune = GRIPPER_MAX
            setDirection_links_grip(links_grip_tune)
        elif state_machine == 20: # links dreh wird eingestellt
            links_dreh_tune = links_dreh_tune + 2
            if links_dreh_tune + 180 > TURN_MAX:
                links_dreh_tune = TURN_MAX-180
            setDirection_links_turn(90 + links_dreh_tune,0.5)
        elif state_machine == 30:  #rechts grip wird eingestellt
            rechts_grip_tune = rechts_grip_tune + 2
            if rechts_grip_tune > GRIPPER_MAX:
                rechts_grip_tune = GRIPPER_MAX
            setDirection_rechts_grip(rechts_grip_tune)
        elif state_machine == 40:  #rechts dreh wird eingestellt
            rechts_dreh_tune = rechts_dreh_tune + 2
            if rechts_dreh_tune + 180 > TURN_MAX:
                rechts_dreh_tune = TURN_MAX-180
            setDirection_rechts_turn(90 + rechts_dreh_tune,0.5) 
        elif state_machine == 50:  #Load wird eingestellt
            LOAD = LOAD +2 
            if LOAD > GRIPPER_MAX:
                LOAD = GRIPPER_MAX
            setDirection_links_grip(LOAD + links_grip_tune)
            setDirection_rechts_grip(LOAD + rechts_grip_tune) 
        elif state_machine == 60:  # SLEEP wird eingestellt
            SLEEP = SLEEP + 0.05
            if SLEEP > 1:
                SLEEP = 1
        elif state_machine == 65:
            if regrip_stat == 1:
                regrip_stat = 0
            else:
                regrip_stat = 1
        elif dummy == 70:
            state_machine =71
            message = "Muster"
        elif dummy == 71:
            state_machine = 72
            message = "Muster"
        elif dummy == 72:
            state_machine = 73
            message = "Muster"
        elif dummy == 73:
            state_machine = 74
            message = "Muster"
        elif dummy == 74:
            state_machine = 75
            message = "Muster"
        elif dummy == 75:
            state_machine = 70
            message = "Muster"
        elif dummy == 76:
            state_machine = 77
            message = "Individuell"
        elif dummy == 77:
            state_machine = 76
            message = "Individuell"   
        elif dummy == 80:
            if scramble_count == SCRAMBLE_MAX:
                scramble_count = 0
            else:
                scramble_count = scramble_count +1



def onButtonEvent_minus(minus, event):
    global state_machine
    global links_grip_tune
    global links_dreh_tune
    global rechts_grip_tune
    global rechts_dreh_tune
    global LOAD
    global SLEEP
    global message
    global regrip_stat
    global scramble_count
    if event == BUTTON_PRESSED:
        dummy = state_machine
        if dummy == 0:
            state_machine = 3
        elif dummy == 3:
            state_machine = 2
        elif dummy == 2:
            state_machine = 1
        elif dummy == 1:
            state_machine = 0
            message = "Start"
        elif state_machine == 10:  # links grip wird eingestellt
            links_grip_tune = links_grip_tune - 2
            if links_grip_tune < 0:
                links_grip_tune = 0
            setDirection_links_grip(links_grip_tune)
        elif state_machine == 20: # links dreh wird eingestellt
            links_dreh_tune = links_dreh_tune - 2
            if links_dreh_tune  < 0:
                links_dreh_tune = 0
            setDirection_links_turn(90 + links_dreh_tune,0.5)
        elif state_machine == 30:  #rechts grip wird eingestellt
            rechts_grip_tune = rechts_grip_tune - 2
            if rechts_grip_tune < 0:
                rechts_grip_tune = 0
            setDirection_rechts_grip(rechts_grip_tune)
        elif state_machine == 40:  #rechts dreh wird eingestellt
            rechts_dreh_tune = rechts_dreh_tune - 2
            if rechts_dreh_tune < 0:
                rechts_dreh_tune = 0
            setDirection_rechts_turn(90 + rechts_dreh_tune,0.5)  
        elif state_machine == 50:  #Load wird eingestellt
            LOAD = LOAD - 2
            if LOAD < 0:
                LOAD = 0
            setDirection_links_grip(LOAD + links_grip_tune)
            setDirection_rechts_grip(LOAD + rechts_grip_tune)  
        elif state_machine == 60:  # SLEEP wird eingestellt
            SLEEP = SLEEP - 0.05
            if SLEEP < 0:
                SLEEP = 0
        elif state_machine == 65:
            if regrip_stat == 1:
                regrip_stat = 0
            else:
                regrip_stat = 1                
        elif dummy == 70:
            state_machine = 75
            message = "Muster"
        elif dummy == 75:
            state_machine = 74
            message = "Muster"
        elif dummy == 74:
            state_machine = 73
            message = "Muster"
        elif dummy == 73:
            state_machine = 72
            message = "Muster"
        elif dummy == 72:
            state_machine = 71
            message = "Muster"
        elif dummy == 71:
            state_machine = 70
            message = "Muster"
        elif dummy == 76:
            state_machine = 77
            message = "Individuell"
        elif dummy == 77:
            state_machine = 76
            message = "Individuell"
        elif dummy == 80:
            if scramble_count == 0:
                scramble_count = SCRAMBLE_MAX
            else:
                scramble_count = scramble_count -1                 

def onButtonEvent_enter(enter, event):
    global state_machine
    global message
    global Target_string
    global Own_pattern
    global now
    global regrip_stat
    
    if event == BUTTON_PRESSED:
        dummy = state_machine
        if dummy == 0:
            state_machine = 99
            regrip()
            # hier startet die Analyse
        elif dummy == 1:
            setDirection_links_turn(90 + links_dreh_tune,0.5)
            setDirection_links_grip(links_grip_tune)
            setDirection_rechts_turn(90 + rechts_dreh_tune,0.5)
            setDirection_rechts_grip(LOAD + rechts_grip_tune)
            state_machine = 10
        elif dummy ==2:
            state_machine = 70
        elif dummy == 3:
            state_machine = 80
        elif dummy == 10:
            setDirection_links_grip(LOAD + links_grip_tune)   
            state_machine = 20
        elif dummy == 20:
            state_machine = 30
            setDirection_rechts_grip(rechts_grip_tune)           
        elif dummy == 30:
            setDirection_rechts_grip(LOAD + rechts_grip_tune)            
            state_machine = 40
        elif dummy == 40:
            state_machine = 50
            setDirection_links_grip(LOAD + links_grip_tune)
            setDirection_rechts_grip(LOAD + rechts_grip_tune)        
        elif dummy == 50:
            state_machine = 60
        elif dummy == 60:
            state_machine = 65
        elif dummy == 65:
            state_machine = 0
            f=open(HOME + "tune_values.txt",'w+')
            f.write(str(links_grip_tune) + "\n")
            f.write(str(links_dreh_tune) + "\n")
            f.write(str(rechts_grip_tune) + "\n")
            f.write(str(rechts_dreh_tune) + "\n")
            f.write(str(LOAD) + "\n")
            f.write(str(SLEEP)+ "\n")
            f.write(str(regrip_stat)+ "\n")
            f.close()
            message = "Start"
            home_servos()            
        elif dummy == 70:
            Target_string = TARGET_STANDARD #default
            state_machine = 99
            now = 0
            regrip()
        elif dummy == 71:
            Target_string = "UBULURUFURURFRBRDRFUFLFRFDFDFDLDRDBDLULBLFLDLBUBRBLBDB" # super flip
            state_machine = 99
            now = 0
            regrip()
        elif dummy == 72:
            Target_string = "LUBUUBBBBDDDRRDFRDRRRRFFRFDFDRFDDFFFBLULLUUUULBULBBLLL" # cube in cube
            state_machine = 99
            now = 0
            regrip()
        elif dummy == 73:
            Target_string = "DDDUUUDDDBRBRRBBBBLLLLFFLFLUDUUDUUDUFLFLLFFFFRRRRBBRBR" # Snake
            state_machine = 99
            now = 0
            regrip()
        elif dummy == 74:
            Target_string = "LLULURURRFFRFRDRDDFUULFULLFFFDFDBDBBBBLBLDLDDBUURBURRB" # Pyramid
            state_machine = 99
            now = 0
            regrip()
        elif dummy == 75:
            state_machine = 76
        elif dummy == 76:
            Target_string = Own_pattern
            state_machine = 99
            now = 0
            regrip()
        elif dummy == 77:
            try:
                Own_pattern = scan_cube()
                state_machine = 76
                now = 0
                message = "Start"
                home_servos()
            except:
                message = "scan Fehler"
                now = 0
                home_servos()
        elif dummy == 80:
            if scramble_count == 0:
                state_machine = 0
                message = "Start"
            else:
                state_machine = 98
                now = 0
                scramble()
                state_machine = 0
                
    elif event == BUTTON_DOUBLECLICKED:
        if state_machine == 0:
            os.exit()
        if state_machine == 99 or state_machine == 98:
            state_machine = 0
		   
#______________________________________________________________________Display__________________________________________



def Anzeige():
    global now
    i=0
#    font = ImageFont.truetype(HOME + 'scripts/font/VCR_OSD_MONO_1.001.ttf',20)

    with canvas(device) as draw:
        draw.text((5, 0), "Boot ",font = font, fill="white")

    while i<100:
        dummy = state_machine
        if dummy == 0:
            m,s = divmod(now,60)
            h,m = divmod(m,60)       
            with canvas(device) as draw:
                draw.text((5, 0), message,font = font, fill="white")
                draw.text((5, 40), "Zeit " + "%02d:%02d" % (m,s), font = font, fill="white")
            time.sleep(0.1)
        elif dummy ==1:
            with canvas(device) as draw:
                draw.text((5, 20), "Setup ",font = font, fill="white")
            time.sleep(0.1)
        elif state_machine ==2:
            with canvas(device) as draw:
                draw.text((5, 20), "Muster ",font = font, fill="white")
            time.sleep(0.1)            
        elif state_machine ==3:
            with canvas(device) as draw:
                draw.text((5, 20), "Verdrehen ",font = font, fill="white")
            time.sleep(0.1)                        
        elif state_machine == 10:
            with canvas(device) as draw:
                draw.text((5, 0), "L. Grip " , font = font, fill="white")
                draw.text((5, 40), str(links_grip_tune), font = font, fill="white")
            time.sleep(0.1)
        elif state_machine == 20:
            with canvas(device) as draw:
                draw.text((5, 0), "L. Dreh ", font = font, fill="white")
                draw.text((5, 40), str(links_dreh_tune), font = font, fill="white")
            time.sleep(0.1)
        elif state_machine == 30:
            with canvas(device) as draw:
                draw.text((5, 0), "R. Grip ", font = font, fill="white")
                draw.text((5, 40), str(rechts_grip_tune), font = font, fill="white")
            time.sleep(0.1)
        elif state_machine == 40:
            with canvas(device) as draw:
                draw.text((5, 0), "R. Dreh " , font = font, fill="white")
                draw.text((5, 40), str(rechts_dreh_tune), font = font, fill="white")
            time.sleep(0.1)
        elif state_machine == 50:
            with canvas(device) as draw:
                draw.text((5, 0), "Load " , font = font, fill="white")
                draw.text((5, 40), str(LOAD), font = font, fill="white")
            time.sleep(0.1)
        elif state_machine == 60:
            with canvas(device) as draw:
                draw.text((5, 0), "Delay " , font = font, fill="white")
                draw.text((5, 40), "%4.2f " % (SLEEP), font = font, fill="white")
            time.sleep(0.1)
        elif state_machine == 65:
            with canvas(device) as draw:
                draw.text((5, 0), "Regrip " , font = font, fill="white")
                draw.text((5, 40), str(regrip_stat), font = font, fill="white")
            time.sleep(0.1)            
        elif state_machine == 70:
            with canvas(device) as draw:
                draw.text((5, 0), message , font = font, fill="white")
                draw.text((5, 40), "Standard", font = font, fill="white")
            time.sleep(0.1) 
        elif state_machine == 71:
            with canvas(device) as draw:
                draw.text((5, 0), message , font = font, fill="white")
                draw.text((5, 40), "Super Flip", font = font, fill="white")
            time.sleep(0.1) 
        elif state_machine == 72:
            with canvas(device) as draw:
                draw.text((5, 0), message , font = font, fill="white")
                draw.text((5, 40), "Cube in C.", font = font, fill="white")
            time.sleep(0.1) 
        elif state_machine == 73:
            with canvas(device) as draw:
                draw.text((5, 0), message , font = font, fill="white")
                draw.text((5, 40), "Schlange", font = font, fill="white")
            time.sleep(0.1) 
        elif state_machine == 74:
            with canvas(device) as draw:
                draw.text((5, 0), message , font = font, fill="white")
                draw.text((5, 40), "Pyramide", font = font, fill="white")
            time.sleep(0.1)             
        elif state_machine == 75:
            with canvas(device) as draw:
                draw.text((5, 0), message , font = font, fill="white")
                draw.text((5, 40), "Individuell", font = font, fill="white")
            time.sleep(0.1)             
        elif state_machine == 76:
            with canvas(device) as draw:
                draw.text((5, 0), "Individuell" , font = font, fill="white")
                draw.text((5, 40), "Starten", font = font, fill="white")
            time.sleep(0.1)             
        elif state_machine == 77:
            with canvas(device) as draw:
                if message != "scan Fehler":
                    draw.text((5, 0), "Individuell" , font = font, fill="white")
                    draw.text((5, 40), "Scannen", font = font, fill="white")
                else:
                    draw.text((5, 0), "Individuell" , font = font, fill="white")
                    draw.text((5, 40), message, font = font, fill="white")                    
            time.sleep(0.1)             
        elif state_machine == 80:
            with canvas(device) as draw:
                draw.text((5, 0), "Verdrehen" , font = font, fill="white")
                draw.text((5, 40), "Anzahl :" + str(scramble_count), font = font, fill="white")
            time.sleep(0.1)             

        elif state_machine == 98:
            if isRunning:
                now = timer_time
            m,s = divmod(now,60)
            h,m = divmod(m,60)       
            with canvas(device) as draw:
                draw.text((5, 0), "Verdrehen", font = font, fill="white")
                draw.text((5, 40), message , font = font, fill="white")
            time.sleep(0.2)


             
        elif state_machine == 99:
            if isRunning:
                now = timer_time
            m,s = divmod(now,60)
            h,m = divmod(m,60)       
            with canvas(device) as draw:
                draw.text((5, 0), message, font = font, fill="white")
                draw.text((5, 40), "Zeit " + "%02d:%02d" % (m,s), font = font, fill="white")
            time.sleep(0.2)
                    
#__________________________________________________________________Wxrfel einlesen_____________________________________



#0 = U
#1 = R
#2 = F
#3 = D
#4 = L
#5 = B

def get_cube():


    regrip()

    camera.capture(HOME + 'Cube/face1.jpg')

#    RTp()

    single_action("b")
    single_action("X")
    single_action("B")
    single_action("a")
    single_action("Y")
    single_action("A")

    regrip()

    camera.capture(HOME + 'Cube/face2.jpg')    


#    RTp()
    single_action("b")
    single_action("X")
    single_action("B")
    single_action("a")
    single_action("Y")
    single_action("A")

    regrip()

    camera.capture(HOME + 'Cube/face4.jpg')

#    RTp()
    single_action("b")
    single_action("X")
    single_action("B")
    single_action("a")
    single_action("Y")
    single_action("A")

    regrip()

    camera.capture(HOME + 'Cube/face5.jpg')

#    LTm()

        
    single_action("b")
    single_action("M")
    single_action("B")
    single_action("a")
    single_action("N")
    single_action("A")    

#    RTp()

    single_action("b")
    single_action("X")
    single_action("B")
    single_action("a")
    single_action("Y")
    single_action("A")
    
    regrip()

    camera.capture(HOME + 'Cube/face3.jpg')

#    RTpp()
    
    if C180 == 1:
        
        single_action("b")
        single_action("X")
        single_action("B")
        single_action("a")
        single_action("Z")
        single_action("A")
        single_action("b")
        single_action("Y")
        single_action("B")

    else:

        single_action("b")
        single_action("X")
        single_action("B")
        single_action("a")
        single_action("Y")
        single_action("A")
    
        single_action("b")
        single_action("X")
        single_action("B")
        single_action("a")
        single_action("Y")
        single_action("A")

    regrip()

    camera.capture(HOME + 'Cube/face0.jpg')

#_______________________________________________________________Image_autokorrektur___________________________________



def pix_average(im, x,y):
    r,g,b = 0,0,0
    for i in range (0,10):
        for j in range (0,10):
            r1,g1,b1 = im.getpixel((x-5+i,y-5+j))
            r += r1
            g += g1
            b += b1
    r = r/100
    g = g/100
    b = b/100

    return r, g, b


#________________________________________________________________Farben_ermitteln________________________________________________________


#0 = U
#1 = R
#2 = F
#3 = D
#4 = L
#5 = B


def get_sticker():
    global solve_string
    col_sticker = []
    for i in range(54):
        col_sticker.append('') 

#read center piece and set as color of the side

    im = Image.open(HOME + "Cube/face1.jpg")
    im = im.convert('RGB')
    base_R_r, base_R_g, base_R_b = pix_average(im,pxl_locs[1][1][0],pxl_locs[1][1][1])
    wb_r, wb_g, wb_b = pix_average(im,wb_col_pxl,wb_row_pxl)  # manual white ballance correction
    print("%6.2f %6.2f %6.2f   " % (wb_r, wb_g, wb_b) + " R")
    base_R_r = base_R_r / wb_r * 255
    base_R_g = base_R_g / wb_g * 255
    base_R_b = base_R_b / wb_b * 255
    
    im = Image.open(HOME + "Cube/face5.jpg")
    im = im.convert('RGB')
    base_B_r, base_B_g, base_B_b = pix_average(im,pxl_locs[1][1][0],pxl_locs[1][1][1])
    wb_r, wb_g, wb_b = pix_average(im,wb_col_pxl,wb_row_pxl)
    print("%6.2f %6.2f %6.2f   " % (wb_r, wb_g, wb_b) + " B")
    base_B_r = base_B_r / wb_r * 255
    base_B_g = base_B_g / wb_g * 255
    base_B_b = base_B_b / wb_b * 255
      
    im = Image.open(HOME + "Cube/face0.jpg")
    im = im.convert('RGB')
    base_U_r, base_U_g, base_U_b = pix_average(im,pxl_locs[1][1][0],pxl_locs[1][1][1])
    wb_r, wb_g, wb_b = pix_average(im,wb_col_pxl,wb_row_pxl)
    print("%6.2f %6.2f %6.2f   " % (wb_r, wb_g, wb_b) + " U")
    base_U_r = base_U_r / wb_r * 255
    base_U_g = base_U_g / wb_g * 255
    base_U_b = base_U_b / wb_b * 255
    
    im = Image.open(HOME + "Cube/face3.jpg")
    im = im.convert('RGB')
    base_D_r, base_D_g, base_D_b = pix_average(im,pxl_locs[1][1][0],pxl_locs[1][1][1])
    wb_r, wb_g, wb_b = pix_average(im,wb_col_pxl,wb_row_pxl)
    print("%6.2f %6.2f %6.2f   " % (wb_r, wb_g, wb_b) + " D")
    base_D_r = base_D_r / wb_r * 255
    base_D_g = base_D_g / wb_g * 255
    base_D_b = base_D_b / wb_b * 255
    
    im = Image.open(HOME + "Cube/face2.jpg")
    im = im.convert('RGB')
    base_F_r, base_F_g, base_F_b = pix_average(im,pxl_locs[1][1][0],pxl_locs[1][1][1])
    wb_r, wb_g, wb_b = pix_average(im,wb_col_pxl,wb_row_pxl)
    print("%6.2f %6.2f %6.2f   " % (wb_r, wb_g, wb_b) + " F")
    base_F_r = base_F_r / wb_r * 255
    base_F_g = base_F_g / wb_g * 255
    base_F_b = base_F_b / wb_b * 255
    
    im = Image.open(HOME + "Cube/face4.jpg")
    im = im.convert('RGB')
    base_L_r, base_L_g, base_L_b = pix_average(im,pxl_locs[1][1][0],pxl_locs[1][1][1])
    wb_r, wb_g, wb_b = pix_average(im,wb_col_pxl,wb_row_pxl)
    print("%6.2f %6.2f %6.2f   " % (wb_r, wb_g, wb_b) + " L")
    base_L_r = base_L_r / wb_r * 255
    base_L_g = base_L_g / wb_g * 255
    base_L_b = base_L_b / wb_b * 255    
    
      
    masterstring = ""
    for img_iter in range(0, 6):
        img_path = HOME + "Cube/face" + str(img_iter) + ".jpg"
        im = Image.open(img_path)
        im = im.convert('RGB')
        wb_r, wb_g, wb_b = pix_average(im,wb_col_pxl,wb_row_pxl)
        for x_iter in range(0,3): #iterate over all nine color locations on each face
            for y_iter in range(0,3):
                r, g, b = pix_average(im, pxl_locs[y_iter][x_iter][0],pxl_locs[y_iter][x_iter][1]) #get pixel value
                #find euclidian distances
                r = r / wb_r * 255
                g = g / wb_g * 255
                b = b / wb_b * 255

                dist_R = math.pow(r - base_R_r, 2) + math.pow(g - base_R_g, 2) + math.pow(b - base_R_b, 2)
                dist_B = math.pow(r - base_B_r, 2) + math.pow(g - base_B_g, 2) + math.pow(b - base_B_b, 2)
                dist_U = math.pow(r - base_U_r, 2) + math.pow(g - base_U_g, 2) + math.pow(b - base_U_b, 2)
                dist_D = math.pow(r - base_D_r, 2) + math.pow(g - base_D_g, 2) + math.pow(b - base_D_b, 2)
                dist_F = math.pow(r - base_F_r, 2) + math.pow(g - base_F_g, 2) + math.pow(b - base_F_b, 2)
                dist_L = math.pow(r - base_L_r, 2) + math.pow(g - base_L_g, 2) + math.pow(b - base_L_b, 2)
                dist_min = min(dist_R, dist_B, dist_U, dist_D, dist_F, dist_L) #find minimum distance value

                #figure out which color has that minimum value

                if(dist_min == dist_R):
                    color = 'R'
                elif(dist_min == dist_B):
                    color = 'B'
                elif(dist_min == dist_U):
                    color = 'U'
                elif(dist_min == dist_D):
                    color = 'D'
                elif(dist_min == dist_F):
                    color = 'F'
                else:
                    color = 'L'
                print("%6.2f %6.2f %6.2f %6.2f %6.2f %6.2f  " % (dist_R,dist_B,dist_U,dist_D,dist_F,dist_L) + color)
                #set cubie face as that color

                col_sticker[img_iter * 9 + 3*y_iter + x_iter] = color
        
#Korrektur oben      //sticker are not in correct order due to movements at reading the cube
    dummy_1 = col_sticker[0]   
    dummy_2 = col_sticker[1]
    col_sticker[0] = col_sticker[6]
    col_sticker[1] = col_sticker[3]
    col_sticker[6] = col_sticker[8]
    col_sticker[3] = col_sticker[7]
    col_sticker[8] = col_sticker[2]
    col_sticker[7] = col_sticker[5]
    col_sticker[2] = dummy_1
    col_sticker[5] = dummy_2  
 
# Korrektur unten
    dummy_1 = col_sticker[27]   
    dummy_2 = col_sticker[28]
    col_sticker[27] = col_sticker[33]
    col_sticker[28] = col_sticker[30]
    col_sticker[33] = col_sticker[35]
    col_sticker[30] = col_sticker[34]
    col_sticker[35] = col_sticker[29]
    col_sticker[34] = col_sticker[32]
    col_sticker[29] = dummy_1
    col_sticker[32] = dummy_2    
 
    print (masterstring)    
    for i in range (54):
        masterstring = masterstring + col_sticker[i]

    print(masterstring)
    return masterstring



#____________________________________________________________________Main_________________________________________________

def setup():
    global links_grip_tune
    global links_dreh_tune
    global rechts_grip_tune
    global rechts_dreh_tune
    global state_machine
    global LOAD
    global SLEEP
    global Own_pattern
    global regrip_stat
    
    setup_button()
    setup_servos()

    if not os.path.exists(HOME + "Cube"):
        os.makedirs(HOME + "Cube")
        os.chmod(HOME + "Cube",0o777)
        
    if os.path.exists(HOME + "Own_pattern.txt"):
        f=open(HOME + "Own_pattern.txt", 'r')
        dummy  = f.readline()
        Own_pattern = dummy
        f.close()
    print(Own_pattern)
    
    if os.path.exists(HOME + "tune_values.txt"):
        f=open(HOME + "tune_values.txt", 'r')
        print("tune values found")
        dummy  = f.readline()
        links_grip_tune = int(dummy)
        dummy  = f.readline()
        links_dreh_tune = int(dummy)
        dummy  = f.readline()
        rechts_grip_tune  = int(dummy)
        dummy  = f.readline()
        rechts_dreh_tune = int(dummy)
        dummy  = f.readline()
        LOAD = int(dummy)
        dummy = f.readline()
        SLEEP = float(dummy)
        dummy = f.readline()
        regrip_stat = int(dummy)
        f.close() 
        return True        
    else:
        links_grip_tune = 0
        links_dreh_tune = 0
        rechts_grip_tune = 0
        rechts_dreh_tune = 0
        LOAD = 30
        f=open(HOME + "tune_values.txt",'w+')
        f.write(str(links_grip_tune) + "\n")
        f.write(str(links_dreh_tune) + "\n")
        f.write(str(rechts_grip_tune) + "\n")
        f.write(str(rechts_dreh_tune) + "\n")
        f.write(str(LOAD) + "\n")
        f.write(str(SLEEP)+ "\n")
        f.write(str(regrip_stat)+ "\n")
        f.close()
        print("Default gesichert")
        return False  #beim ersten Durchgang werden alle Servos auf 0 gestellt damit die Arme richtig montiert werden kxnnen


        
#_________________________________________Scan_cube_Own_Pattern________________________________

def scan_cube():
    global message
    message = "Einlesen"
    
    get_cube() 
    
    message = "Analyse"
    
    solution = get_sticker()

    try:
        solve_string = kociemba.solve(solution)  # only to test if scanned pattern is valid
        f=open(HOME + "Own_pattern.txt",'w+')
        f.write(solution + "\n")
        f.close()
        return solution
    except:

        raise  

#____________________________________________scramble______________________________________________
        
def scramble():
    global moves
    global solve_array
    global solve_sequenze
    global message
    global now
#    pos_moves = ["U","U2","U'","F","F2","F'","R","R2","R'","L","L2","L'","B","B2","B'","D","D2","D'"]
    pos_moves = [["U","U2","U'"],["F","F2","F'"],["R","R2","R'"],["L","L2","L'"],["B","B2","B'"],["D","D2","D'"]]
    scramble_string="" 
    layer = 0
    last_layer = 0
    for x in range (scramble_count):
        while layer == last_layer:
            layer = random.randint(0,5)
        last_layer = layer
        scramble_string = scramble_string + " " + pos_moves[layer][random.randint(0,2)]
    
    solve_array = scramble_string.split(" ")

    moves=len(solve_array)-1
    
    create_master_string()    
    
    regrip()
    
    for x in solve_sequenze:
        single_action(x)
        message = "Rest: " + str(moves)
        if state_machine == 0:  #DOUBLECLICK auf rechtsbutton

            break        
    message = "Start"
    now = 0
    home_servos()


#__________________________________________Main_______________________________________________

camera = PiCamera()
camera.resolution = (IMG_BREITE, IMG_HOEHE)
camera.exposure_mode = 'auto'
camera.start_preview()
time.sleep(2)

setup()

now = 0
move_count = 0

t = Thread(target=Anzeige)
t.start()

s = Thread(target=my_timer)
s.start()

#
isRunning = False



timer_time = 0
message = "Start "

state_machine = 0
endless = 1

#dummy = ""

while endless == 1:
    home_servos()

    solve_sequenze=""
   
    while state_machine != 99:   #warten bis "start"
        i=1
    
    setDirection_links_grip(links_grip_tune)
    setDirection_rechts_grip(rechts_grip_tune)

    now=0
    isRunning = True
    timer_time = 0
    message = "Einlesen"
    
    get_cube() 
    
    message = "Analyse"
    
    solution = get_sticker()

#    else:
    try:
        if Target_string == TARGET_STANDARD:
            solve_string = kociemba.solve(solution)
        else:
            solve_string = kociemba.solve(solution,Target_string)
    except:
        message = "Farbfehler!"
        state_machine=0
        print(solve_string)
        continue

    print (Target_string)
    print (solve_string)    
    solve_array = solve_string.split(" ")
    
    
    correct_left()

    moves=len(solve_array)
    
    create_master_string()

    for x in solve_sequenze:
        single_action(x)
        message = "Rest: " + str(moves)
        if state_machine == 0:  #DOUBLECLICK auf rechtsbutton
            message = "Start"
            now = 0
            break

    isRunning=False  
    state_machine = 0
    message ="Moves: " + str (len(solve_array))


home_servos()     
GPIO.cleanup()
camera.close()
print ("all done")