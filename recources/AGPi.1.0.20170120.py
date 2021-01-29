#!/usr/bin/python3
# Program: AwanaGrandPi.py
# Purpose: To determine the order in which cars cross the finish line.
# Author: David M. Peterson
# Date: October 20th, 2014
# Revision: Janyary 20, 2017
# Language: Python 3.2

# Import Modules.
import curses
import traceback
import string
import os
import sys
import time                       # Import Time Library
import RPi.GPIO as GPIO           # Import GPIO library
import operator                   # Used in the sorting of the race.


#-- Define the appearance of some interface elements
hotkey_attr = curses.A_BOLD | curses.A_UNDERLINE | curses.A_REVERSE
menu_attr = curses.A_NORMAL

#-- Define additional constants
EXIT = 0
CONTINUE = 1
MPH = 0                          # Constantant Unit Miles Per Hour.
FPS = 1                          # Constantant Unit Feet Per Sec.
FPS_TO_MPH = 0.682               # Conversion Factor FPS to MPH
CAR_SCALE = 207.0 / 7.0          # Model Scale for Computing Speed NASCAR Specs
PERCISSION = 3                   # To what percission to display results.
START_GPIO = 4                   # General Purpose I/O for Start Lane Sensor
RED_GPIO = 18                    # General Purpose I/O for Red Lane Sensor
BLUE_GPIO = 23                   # General Purpose I/O for Blue Lane Sensor
GREEN_GPIO = 24                  # General Purpose I/O for Green Lane Sensor
YELLOW_GPIO = 25                 # General Purpose I/O for Yellow Lane Sensor
LIGHTS_GPIO = 07                 # General Purpose I/O for turning on/off IR.
KEY_UP = 65                      # Used in getch for moving up-done in pads.
KEY_DOWN = 66
KEY_RIGHT = 67
KEY_LEFT = 68

# Prep for Class Lane 
red = type
blue = type
Green = type
Yellow = type
# Constants and Variables for Lane Classes.
COLOUR = 0                      # The Colour is index 0 in the list below
POSITION = 1                    # The screen position is index 1 in list below
lanes = [["red","6"], ["blue", "7"], ["green", "8"], ["yellow", "9"]]

length_of_lane = 41.54           # Distance of Track in feet
start_time = 0.0                 # Start of race time
cars_in_the_race = 4             # Number of cars in each race
cars_across_the_line = 0         # The number of cars to cross the finish ln
race_id = ""
show_time = True                 # Boolean to determine if time and speed is disp.
unit_of_measure = MPH            # Boolean to determine which unit of measure MPH/FPS
race_cars = {}                   # Dictionary of all the race cars: Key is the Car ID
base_file_name = "AGPi"          # Starting base name for storing car and race Info
screen = None                    # Give screen module scope

# Classes and related functions
#
# Parse a delimited string returning a list of items.
# Delimiter defaults to a comma.
#
def parse(item, delimiter = ","):
    a = ""
    details = []
    for x in item:
        if x != delimiter:
            a = a + x
        else:
            details.append(a)
            a = ""
    return details
#
# This is the class for each Awana Car describing the registration number
# owner, top speed and points for the race. The number of points is for
# future use.
#
class Awana_Car:
#   Initialize the Class
    def __init__(self, reg_num = "", owners_name = ""):
        if reg_num == "":
            self.reg_num = "000"
            self.owners_name = "No Name"
            self.top_speed = 0.0
            self.points = 0                   # Number of points for heats 
        elif owners_name != "": # Reg and Name Passed
            self.reg_num = reg_num            # Registration Nmber of Car.
            self.owners_name = owners_name    # Name of owner of Car.
            self.top_speed = 0.0              # Top speed of all races.
            self.points = 0                   # Number of points for heats
        else:                   # File info Passed
            details = parse(reg_num)          # parse the str from file.
            self.reg_num = details[0]         # First item should be Reg_num.
            self.owners_name = details[1]     # Second Item Owners Name
            self.top_speed = float(details[2])# Third Item Top Speed
            self.points = 0                   # Number of points for heats
    def set_reg_num(self, reg_num):
        self.reg_num = reg_num

    def get_reg_num(self):
        return self.reg_num

    def set_owners_name(self, owners_name):
        self.owners_name = owners_name

    def get_owners_name(self):
        return self.owners_name

    def set_top_speed(self, new_speed):
        if self.top_speed < new_speed:
            self.top_speed = new_speed

    def get_top_speed(self):
        return self.top_speed

    def add_to_points(self, points):
        self.points += points

    def get_points(self):
        return self.points

    def get_writeable_info(self):
        return self.get_reg_num() + "," + \
               self.get_owners_name() + "," + \
               str(self.get_top_speed()) + ",\n"
        
                            
class Lane:
#   Initialize the Class
    def __init__(self, lane_name = "None", lane_num = 0, channel = 0):
        # Define Local Variables
        self.name = lane_name               # Name of lane
        self.lane_num = lane_num            # Length of lane name is 2 greater than lane.
        self.gpio_channel = channel         # GPIO channel number for internal use.
        self.end_time = 0.0                 # end time of clock in seconds
        self.awana_car = Awana_Car()        # Set which car is on this lane
        GPIO.setup(channel, GPIO.IN)        # Set up the GPIO Channel

#
#   General Functions
#
    def get_lane_name(self):
        return self.name

    def get_lane_num(self):
        return self.lane_num
    
    def set_end_time(self, t):
        self.end_time = t

    def get_end_time(self):
        return round(self.end_time, PERCISSION)

    def get_total_time(self):
        return round(self.end_time - start_time, PERCISSION)

    def get_speed(self, unit = FPS):         # Options 0: MPH, 1: FPS.
        total_time = (self.end_time - start_time)
        speed = -1.0
        if total_time > 0.0:
            speed =  length_of_lane / total_time
            if unit == MPH:
                return round(speed * FPS_TO_MPH * CAR_SCALE, PERCISSION)
            if unit == FPS:
                return round(speed * CAR_SCALE, PERCISSION)
        else:
            return(speed)

    def lane_ready(self):
        return GPIO.input(self.gpio_channel)

    def reset_end_time(self):
        self.end_time = 0.0

    def set_awana_car(self, awana_car):
        self.awana_car = awana_car
        if self.get_owners_name() != "No Name":
            screen.addstr(self.lane_num + 5, 39 - \
                          len(self.get_owners_name()), \
                          self.get_owners_name())
        else:
            screen.addstr(self.lane_num + 5, 10, " " * 30)

    def get_owners_name(self):
        return self.awana_car.get_owners_name()

    def get_reg_num(self):
        return self.awana_car.get_reg_num()

    def set_top_speed(self):
        self.awana_car.set_top_speed(self.set_top_speed())
        
#
#   GPIO Call Back Functions
#
    def gpio_set_end_time(self, channel):
        cross_the_line = time.time()
        global cars_across_the_line
        if self.end_time == 0.0 and start_time != 0.0:
            self.end_time = cross_the_line
            cars_across_the_line += 1
#
#   Destruct the Class for proper cleam up of GPIO
#
    def __del__(self):
        #GPIO Clean Up Processes.
        #GPIO.remove_event_detect(self.gpio_channel)
        #GPIO.cleanup(self.gpio_channel)
        pass
# End of Class Lane Description

#Generl Purpose funtctions

# Display a message in the center of the screen and wait for an answer.
def display_mssg(msg = "Press [ENTER] to continue.", answer = ""):
    if len(msg) < 79:
        start_x_position = int((curses.COLS - len(msg) - 2) / 2)
        start_y_position = int((curses.LINES - 2) / 2)
    else:
        length_win
    mssg_win = curses.newwin(3, len(msg) + 2, start_y_position , start_x_position)
    mssg_win.box()
    mssg_win.addstr(1, 1, msg)
    c = mssg_win.getch()
    if answer != "":
        while (answer.find(chr(c)) < 0):
            c = mssg_win.getch()
    mssg_win.erase()
    mssg_win.refresh()
    return c

# For some odd reason window.getstr(x, y, l) is returning a byte string
# instead of pure string, this converse byte string to string.
def byte_to_str(byte):
    a = str(byte)
    return a[2:len(a)-1] 

# check to make sure value is of type float or int.
def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def is_int(value):
    try:
        int(value)
        return True
    except:
        return False
#
# Functions for timing race

# Give the ability to turn on/off the IR transmitter to reduce total power
# used by the AGPi system. Will be useful where a battery is needed to run
# the AGPi hardware.
def lights_on():
    GPIO.output(LIGHTS_GPIO, GPIO.HIGH)

def lights_off():
    GPIO.output(LIGHTS_GPIO, GPIO.LOW)

# This will be called when the GPIO senses the pin assgined to the start
# mechanism going from a high to low state.
def set_the_start_time(channel):
    bar_drops = time.time()
    global start_time
    if start_time == 0.0:
        start_time = bar_drops

# Event dectection for the start bar and lane sensors will be turned on/off
# for each race to reduce CPU processing time and to eliminate false
# indicators from the GPIO's
def start_event_detect():
    global START_GPIO, red, blue, green, yellow
    GPIO.add_event_detect(START_GPIO, GPIO.RAISING,
                          callback=set_the_start_time,
                          bouncetime = 300)
    for i in lanes:
        eval("GPIO.add_event_detect(" + i[COLOUR] +
             ".gpio_channel, GPIO.RAISING, callback=" + i[COLOUR] +
             ".gpio_set_end_time, bouncetime = 100)")

def stop_event_detect():
    global START_GPIO, red, blue, green, yellow
    GPIO.remove_event_detect(START_GPIO)
    for i in lanes:
        eval("GPIO.remove_event_detect(" + i[COLOUR] + ".gpio_channel)")

# During the race show the the cars as they cross the line
def show_temp_results():
#    global red, blue, green, yellow
    for i in lanes:
        if eval(i[COLOUR] + ".get_end_time() > 0.0"):
            eval("screen.addstr(" + i[POSITION] + ", 55, 'Cross')")

# Get the final results for the race and sort first place to last.
def get_race_results(unit = FPS):
    global red, blue, green, yellow
    # the list of order includes lane, total time, and speed
    # of each of the lanes.
    order = []
    for i in lanes:
        if eval(i[COLOUR] + ".get_total_time() > 0.0"):
            eval("order.append((" +
                 i[COLOUR] + ".get_lane_name(), " +
                 i[COLOUR] + ".get_total_time(), " +
                 i[COLOUR] + ".get_speed(unit)))")
    # Sort the list of order using the total time.
    try:
        order = sorted(order, key=operator.itemgetter(1), reverse=False)
        screen.addstr(5, 55, "Clean Race    ")
        return order
    except TypeError:
        screen.addstr(5, 55, "Faulty Race")
        return order #[(1,1,1), (1,1,1),(1,1,1),(1,1,1)]
        
def reset_the_race():
    global cars_across_the_line, start_time, red, blue, green, yellow
    cars_across_the_line = 0
    start_time = 0.0
    for i in lanes:
        eval(i[COLOUR] + ".reset_end_time()")

def start_the_race(cars_in_race = 4):
    global red, blue, green, yellow
    reset_the_race()
    lights_on()
    start_event_detect()
    while start_time == 0.0:
        pass
    screen.addstr(5, 55, "Ready, Set, Go") # Displayed when start bar drops
    while cars_across_the_line < cars_in_race:
        screen.addstr(1, 55, "/" + str(cars_across_the_line))
        show_temp_results()     # Displays which lanes have activated.
        screen.refresh()
        pass                    # A do nothing command, Waiting on Cars.
    lights_off()
    stop_event_detect()
    show_temp_results()
    screen.refresh()

def set_up_lanes_and_GPIO():
    global red, blue, green, yellow
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LIGHTS_GPIO, GPIO.OUT)
    GPIO.setup(START_GPIO, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    red = Lane("red", 1, RED_GPIO)
    blue = Lane("blue", 2, BLUE_GPIO)
    green = Lane("green", 3, GREEN_GPIO)
    yellow = Lane("yellow", 4, YELLOW_GPIO)

def clean_up_lanes_and_GPIO():
    global red, blue, green, yellow
    del red, blue, green, yellow
    GPIO.cleanup()

#
# User Interface Functions
# Text Based Using Curses.
#

#-- Create the topbar menu
def topbar_menu(menus):
    title = "Awana Grand Pi 1.0"
    left = 2
    for menu in menus:
        menu_name = menu[0]
        menu_hotkey = menu_name[0]
        menu_no_hot = menu_name[1:]
        screen.addstr(1, left, menu_hotkey, hotkey_attr)
        screen.addstr(1, left+1, menu_no_hot, menu_attr)
        left = left + len(menu_name) + 3
        # Add key handlers for this hotkey
        topbar_key_handler((str.upper(menu_hotkey), menu[1]))
        topbar_key_handler((str.lower(menu_hotkey), menu[1]))
    # Little aesthetic thing to display application title
    screen.addstr(1, curses.COLS - len(title) - 3, title, curses.A_STANDOUT) 
    screen.refresh()

#--  Key handler both loads and processes keys strokes
def topbar_key_handler(key_assign = None, key_dict = {}):
    screen.addstr(1, 40, "Lanes in Use: " + str(cars_in_the_race) + "  ")
    screen.refresh()
    if key_assign:
        key_dict[ord(key_assign[0])] = key_assign[1]
    else:
        screen.refresh()
        c = screen.getch()
        if c in (curses.KEY_END, ord('!')):
            return 0
        elif c not in key_dict.keys():
            curses.beep()
            return 1
        else:
            return eval(key_dict[c])

#-- Handlers for the topbar menus
def save_car_to_file(car):
    my_file = open(base_file_name + "cars.txt", "a")
    my_file.write(car.get_writeable_info())
    my_file.close()

def get_cars_from_file():
    global race_cars
    got_a_car = True
    try:
        my_file = open(base_file_name + "cars.txt", "r")
    except:
        return False
    try:
        while got_a_car:
            items = my_file.readline()
            if items != "":
                new_car = Awana_Car(items)
                race_cars[new_car.get_reg_num()] = new_car
            else:
                got_a_car = False
        return True
    except:
        return True

def list_the_cars():
    global race_cars
    lines = curses.LINES
    sortedkeys = []
    for x in race_cars: sortedkeys.append(x)
    sortedkeys.sort()
    y = -1
    car_pad = curses.newpad(len(race_cars)+1, 32) # adding 1 gives min length
    for key_id in sortedkeys:
        y += 1
        car_pad.addstr(y, 0, " " + race_cars[key_id].get_reg_num() + " " +
                        race_cars[key_id].get_owners_name())
    y = 0
    car_pad.refresh(y,0, 8,1, lines - 2,33)
    c = car_pad.getch()
    while c not in (ord('q'), ord('Q')):
        if c == KEY_UP: y -= 1
        if c == KEY_DOWN: y += 1
        if y >= len(race_cars) - (lines - 10):
            y = len(race_cars) - (lines - 9)
        if y < 0: y = 0
        car_pad.refresh(y,0, 8,1, lines - 2,33)
        c = car_pad.getch()
    car_pad.erase()
        
def cars_func():
    global race_cars
    car_id = ""
    owners_name = ""
    s = curses.newwin(6,25,2,1)
    s.box()
    s.addstr(1, 2, "A", hotkey_attr)
    s.addstr(1, 3, "dd a Racer", menu_attr)
    s.addstr(2, 2, "L", hotkey_attr)
    s.addstr(2, 3, "ist Racers", menu_attr)
    s.addstr(3, 2, "G", hotkey_attr)
    s.addstr(3, 3, "et Cars From File", menu_attr)
    s.addstr(1,2, "", hotkey_attr) #Reset Cursor Locaton
    s.refresh()
    c = s.getch()
    if c in (ord('A'), ord('a')):
        s1 = curses.newwin(6,35,3,3)
        s1.box()
        curses.echo(); curses.curs_set(1)
        s1.addstr(1, 1, "Add New Race Car Owner:")
        correct = False
        while not correct:
            s1.addstr(2, 1, "     Car ID:" + " " * 20)
            s1.addstr(3, 1, "Owners Name:" + " " * 20)
            s1.addstr(4, 1, " " * 20)
            s1.refresh()
            car_id = byte_to_str(s1.getstr(2, 14, 3))
            owners_name = byte_to_str(s1.getstr(3, 14, 20))
            s1.addstr(4, 1, "OK (Y/N)")
            c = s1.getch()
            if c in (ord('N'), ord('n')):
                correct = False
            else:
                correct = True
        race_cars[car_id] = Awana_Car(car_id, owners_name)
        save_car_to_file(race_cars[car_id])
        curses.noecho(); curses.curs_set(0)
        s1.erase()
    elif c in (ord('L'), ord('l')):
        list_the_cars()
    elif c in (ord('G'), ord('g')):
        if get_cars_from_file():
            list_the_cars()
    else:
        curses.beep()
        curses.flash()
    s.erase()
    
    return CONTINUE

def draw_place_box(lane, place, name = "No Name"):
    lane_attr = curses.A_BOLD
    delta = int((curses.COLS - 2) / 4)
    if name != "No Name":
        screen.addstr(11, place * delta - (delta - 1), name)
    for x in range(0,(curses.LINES - 13)):
      screen.addstr(12 + x, place * delta - (delta - 1), 
		    chr(48 + lane) * (delta - 1), 
		    curses.color_pair(lane))

def clear_place_box():
    for x in range(0,(curses.LINES - 12)):
        screen.addstr(11 + x, 1, " " * (curses.COLS - 3), 
		    curses.color_pair(0))

def clear_race_cars():
    for x in range(1,5):
        screen.addstr(5 + x, 10, " " * 30)

def clear_time_speed():
    for x in range(0, 5):
        screen.addstr(x + 5, 55, " " * 23)
        
def check_for_ready():
    lights_on()
    if GPIO.input(START_GPIO):
        screen.addstr(5, 48, " " * 5)
    else:
        screen.addstr(5, 48, "Ready")            
    for x in lanes:
        if  eval(x[0]+ ".lane_ready()"):
            screen.addstr(int(x[1]), 48, "Ready")
        else:
            screen.addstr(int(x[1]), 48, " " * 5)            
    screen.refresh()
    lights_off()
    
def get_racers():
    global race_id
    screen.addstr(5, 25, "Enter Owner ID:")
    curses.echo(); curses.curs_set(1)
    screen.addstr(3, 35, "   ") # Clear Race ID.
    race_id = byte_to_str(screen.getstr(3, 35, 3))  # Get Race ID
    for x in lanes:
        car = byte_to_str(screen.getstr(int(x[1]), 36, 3))
        while (car not in race_cars) and len(car) > 0:
            screen.addstr(int(x[1]), 10, " " * 30)
            display_mssg("Car not found. Press {ENTER} to try again!")
            car = byte_to_str(screen.getstr(int(x[1]), 36, 3))
        if car in race_cars:
            eval(x[0] + ".set_awana_car(race_cars[car])")
        else:
            eval(x[0] + ".set_awana_car(Awana_Car())")
    curses.noecho(); curses.curs_set(0)
    screen.addstr(5, 25, " " * 15)

def race_func():
    global cars_in_the_race
    s = curses.newwin(5, 15, 2, 9)
    s.box()
    s.addstr(1, 2, "R", hotkey_attr)
    s.addstr(1, 3, "eset Lanes", menu_attr)
    s.addstr(2, 2, "B", hotkey_attr)
    s.addstr(2, 3, "egin Race", menu_attr)
    s.addstr(3, 2, "L", hotkey_attr)
    s.addstr(3, 3, "anes in Use", menu_attr)
    s.addstr(1,2, "", hotkey_attr) #Reset Cursor Locaton
    screen.addstr(1, 40, "Lanes in Use: " + str(cars_in_the_race))
    screen.refresh(); s.refresh()
    c = s.getch()
    if c in (ord('R'), ord('r')):
        c = display_mssg("Clearing Lanes [Y/N]:", "YNyn")
        if c in (ord('Y'), ord('y')):
            clear_place_box()
            clear_race_cars()
            clear_time_speed()
            check_for_ready()
            get_racers()
        else:
            display_mssg("Abort Lane Reset!")
    elif c in (ord('B'), ord('b')):
        c = display_mssg("Begin the race [Y/N]?", "YNyn")
        if c in (ord('Y'), ord('y')):
            clear_place_box()
            clear_time_speed()
            screen.refresh()
            s.clear(); s.refresh(); s.box()
            s.addstr(1, 1, "On Your Mark")
            s.addstr(2, 1, "Get Set")
            s.addstr(3, 1, "Go")
            s.refresh()
            start_the_race(cars_in_the_race)
            clear_time_speed()
            order = get_race_results(unit_of_measure)
            pos = 0
            writable = ""
            for x in order:
                # The if statement checks to see if the lane was used
                # if the lane was used the total time [1] will be
                # greater than 0.0.
                if x[1] > 0.0:
                    # set information for writing to file
                    # Lane Color, Reg ID, and Time
                    writable = writable + x[0] + "," + \
                               eval(x[0] + ".get_reg_num()") + "," + \
                               str(x[1]) + ","
                    # Advance the postition on the screen to draw the
                    # colored box for the current lane/place being
                    #processed.
                    pos += 1
                    name = eval(x[0] + ".get_owners_name()")
                    draw_place_box(eval(x[0] + ".get_lane_num()"), pos, name)
                    # In some races we may not want to show time and speed.
                    # This may confuse the children if they see that had
                    # the fastest overall time, but did not win in the over
                    # all contest due to their total performance.
                    try:
                        if show_time == True:
                            lane = eval(x[0] + ".get_lane_num()")
                            screen.addstr(lane + 5, 55, str(round(x[1], PERCISSION)))     # time
                            screen.addstr(lane + 5, 64, str(round(x[2], PERCISSION)))   # speed
                    except:
                        pass
            # Save the race results if there is a race ID.
            c = display_mssg("Certify the Race [Y/N]?", "YNyn")
            if race_id != "" and c in ((ord('Y'), ord('y'))):
                writable = race_id + "," + writable + "\n"
                my_file = open(base_file_name + "Heats.txt", "a")
                my_file.write(writable)
                my_file.close()
        else:
            display_mssg("Race Aborted!")    
        # Chose the number of lanes used for the next race.                    
    elif c in (ord('L'), ord('l')):
        s.clear(); s.refresh(); s.box()
        s.addstr(1, 1, "Enter # of")
        s.addstr(2, 1, "Cars in")
        s.addstr(3, 1, "the Race:")
        s.refresh()
        c = 0
        while c < 49 or c > 52:
            c = s.getch()
        cars_in_the_race = c - 48
    else:
      curses.beep()
      curses.flash()
    s.erase()
    return CONTINUE

# Toggle on and off the header for time and speed
def show_time_header():
    u_o_m = "MPH"                   # A string Unit_of_Measure
    if unit_of_measure == FPS:
        u_o_m = "FPS"
    if show_time == True:
        screen.addstr(3, 55, "Sec      " + u_o_m)
        screen.addstr(4, 55, "Time     Speed")
    else:
        screen.addstr(3, 55, " " * 14)
        screen.addstr(4, 55, " " * 14)
        clear_time_speed()
    screen.refresh()

def option_func():
    global show_time, unit_of_measure, length_of_lane, CAR_SCALE
    global base_file_name, PERCISSION
    s = curses.newwin(9, 23, 2, 16)
    s.box()
    s.addstr(1, 2, "S", hotkey_attr)
    s.addstr(1, 3, "how Speed On/Off", menu_attr)
    s.addstr(2, 2, "U", hotkey_attr)
    s.addstr(2, 3, "nit FPS/MPH", menu_attr)
    s.addstr(3, 2, "L", hotkey_attr)
    s.addstr(3, 3, "ane Length:", menu_attr)
    s.addstr(3, 15, str(round(length_of_lane, 4)))
    s.addstr(4, 2, "C", hotkey_attr)
    s.addstr(4, 3, "ar scale:", menu_attr)
    s.addstr(4, 13, str(round(CAR_SCALE, 4)))
    s.addstr(5, 2, "T", hotkey_attr)
    s.addstr(5, 3, "est & Calibate", menu_attr)
    s.addstr(6, 2, "F", hotkey_attr)
    s.addstr(6, 3, "ile name: ")
    s.addstr(6, 13, base_file_name)
    s.addstr(7, 2, "P", hotkey_attr)
    s.addstr(7, 3, "ercission: ", menu_attr)
    s.addstr(7, 14, str(PERCISSION))
    s.addstr(1,2, "", hotkey_attr) #Reset Cursor Locaton
    s.refresh()
    c = s.getch()
    # Toggle between showing time/speed and no time/speed
    if c in (ord('S'), ord('s')):
        if show_time == True:
            show_time = False
        else:
            show_time = True
        show_time_header()
    # Toggle between FPS and MPH
    elif c in (ord('U'), ord('u')):
        if unit_of_measure == MPH:
            unit_of_measure = FPS
        else:
            unit_of_measure = MPH
        show_time_header()
    # Set a new length for the lane. This is a 6 position field.
    # Average lenth is between 20 and 40 ft. Number of feet should
    # be a decimal. ie. 30.25 would be eq to 30 ft 3 in.
    elif c in (ord('L'), ord('l')):
        curses.echo(); curses.curs_set(1)
        lol = "NotDigit"
        while not is_float(lol):
            lol = s.getstr(3, 15, 6)
        length_of_lane = float(lol)
        curses.noecho(); curses.curs_set(0)
    # Set a new scale for the car, the standard lenth of a NASCAR is
    # 207 inches, the standard lenth of a AWANA Grand Prix car is 7 inches.
    elif c in (ord('C'), ord('c')):
        curses.echo(); curses.curs_set(1)
        sc = "NotDigit"
        while not is_float(sc):
            sc = s.getstr(4, 13, 6)
        CAR_SCALE = float(sc)
        curses.noecho(); curses.curs_set(0)
    # Used to continually loop through the check_for_ready function
    # so that the IR Transmitter and IR Rcvrs can be aligned. Once
    # alignment is complete any key press will exit loop and continue
    # with the program.
    elif c in (ord('T'), ord('t')):
        clear_place_box()
        clear_time_speed()
#        for x in range(0, 4):
#            screen.addstr(x + 6, 55, " " * 15)
        screen.addstr(12, 25, "Press any key to continue.")
        s.timeout(0) # With s.timeout set to 0 s.getch will check and move on.
        while s.getch() == -1:
            check_for_ready()
            s.refresh()
        s.timeout(-1) # Reset s.timeout for further reading.
        screen.addstr(12, 25, " " * 26)
    elif c in (ord('F'), ord('f')):
        curses.echo(); curses.curs_set(1)
        base_file_name = byte_to_str(s.getstr(6, 13, 8))
        curses.noecho(); curses.curs_set(0)
    elif c in (ord('P'), ord('p')):
        curses.echo(); curses.curs_set(1)
        sc = "NotDigit"
        while not is_int(sc):
            sc = s.getstr(7, 14, 1)
        sc = int(sc)
        if sc in range(1, 6):
            PERCISSION = sc
        else:
            display_mssg("Min Percession = 1 / Max Percission = 5")
        curses.noecho(); curses.curs_set(0)
    else:
        curses.beep()
        curses.flash()
    s.erase()
    return CONTINUE

def help_func(): 
    s = curses.newwin(22, 79, 2, 1)
    s.box()
    s_pad = curses.newpad(100, 76)
    line_in_pad = 0
    y = 0
    fh_help = open('AwanaGrandPiHelp.txt')
    for line in fh_help.readlines():
        s_pad.addstr(line_in_pad, 0, str.rstrip(line))
        line_in_pad += 1
    fh_help.close()
    c = 0
    while c not in (ord('Q'), ord('q')):
        if c == KEY_UP: y -= 1
        if c == KEY_DOWN: y += 1
        if y < 0: y = 0
        if y > (line_in_pad - 19): y = line_in_pad  - 19
        s_pad.refresh(y, 0, 3, 2, 24, 76)
        c = s_pad.getch()
    s_pad.erase()
    s.erase()
    return CONTINUE

def exit_func():
    c = display_mssg("Do you wish to exit [Y/N]?", "YyNn")
    if c in (ord('Y'), ord('y')):
        return EXIT
    else:
        return CONTINUE


#-- Top level function call (everything except [curses] setup/cleanup)
def main(stdscr):
    # Frame the interface area at fixed VT100 size
    global screen
    #screen = stdscr.subwin(curses.LINES - 1, curses.COLS - 1, 0, 0)
    screen = stdscr.subwin(curses.LINES, curses.COLS, 0, 0)
    screen.box()
    screen.hline(2, 1, curses.ACS_HLINE, curses.COLS - 3)
    screen.refresh()

    # Define the topbar menus
    cars_menu = ("Cars", "cars_func()")
    race_menu = ("Race", "race_func()")
    option_menu = ("Option", "option_func()")
    help_menu = ("Help", "help_func()")
    exit_menu = ("Exit", "exit_func()")

    # Add the topbar menus to screen object
    topbar_menu((cars_menu, race_menu, option_menu,
                 help_menu, exit_menu))

    # Draw the onscreen field titles
    show_time_header()
    screen.addstr(3, 26, "Race ID:")
    screen.addstr(4, 40, "  Lane  Status")
    screen.addstr(5, 40, " Start:")
    screen.addstr(6, 40, "   Red:")
    screen.addstr(7, 40, "  Blue:")
    screen.addstr(8, 40, " Green:")
    screen.addstr(9, 40, "Yellow:")
    # Enter the topbar menu loop
    while topbar_key_handler():
      pass
    screen.erase()
    screen.refresh()

if __name__=='__main__':
    try:
        # Initialize Rasberry Pi
        set_up_lanes_and_GPIO()
        
        # Initialize curses
        stdscr=curses.initscr()
        curses.start_color()
        curses.init_color(1, 1000,    0,    0) # RED
        curses.init_color(4,    0,    0, 1000) # BLUE
        curses.init_color(2,    0,  600,    0) # GREEN
        curses.init_color(3,  980,  980,    0) # YELLOW
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_RED)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLUE)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_GREEN)
        curses.init_pair(4, curses.COLOR_YELLOW,curses.COLOR_YELLOW)

        # Turn off echoing of keys, and enter cbreak mode,
        # where no buffering is performed on keyboard input
        # Turn off the cursor
        curses.noecho() ; curses.cbreak(); curses.curs_set(0)

        # In keypad mode, escape sequences for special keys
        # (like the cursor keys) will be interpreted and
        # a special value like curses.KEY_LEFT will be returned
        stdscr.keypad(1)
        main(stdscr)                    # Enter the main loop

        # Set everything back to normal
        stdscr.keypad(0)
        curses.echo() ; curses.nocbreak(); curses.curs_set(1)
        curses.endwin()                 # Terminate curses

        # Clean Up the GPIOs
        clean_up_lanes_and_GPIO()
        # If all goes well the program exits here.

    except:
        # In the event of an error, restore the terminal
        # to a sane state.
        stdscr.keypad(0)
        clean_up_lanes_and_GPIO()
        curses.echo() ; curses.nocbreak(); curses.curs_set(1)
        curses.endwin()
        traceback.print_exc()           # Print the exception
        # If there is an error the program exits here.
