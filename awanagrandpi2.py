import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
import time


# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)


# initialize variables

timer_triger = 18
red_triger = 16
green_triger = 12
blue_triger = 10
yellow_triger = 8

# Lane start and stop data !! MOVE TO CLASS / RENAME TO REPRESENT DATA !!


lane_data = {
    "red_time": 0,
    "blue_time": 0,
    "green_time": 0,
    "yellow_time": 0,
    "timer_start": 0
}

race_times = {
    "red_time": 0,
    "blue_time": 0,
    "green_time": 0,
    "yellow_time": 0

}


# lane callbacks


def red_callback(channel):
    milliseconds = int(round(time.time() * 1000))
    lane_data["red_time"] = milliseconds
    print("red crossed!")
    time.sleep(0.01)


def blue_callback(channel):
    milliseconds = int(round(time.time() * 1000))
    lane_data["blue_time"] = milliseconds
    print("blue crossed!")
    time.sleep(0.01)


def green_callback(channel):
    milliseconds = int(round(time.time() * 1000))
    lane_data["green_time"] = milliseconds
    print("green crossed!")
    time.sleep(0.01)


def yellow_callback(channel):
    milliseconds = int(round(time.time() * 1000))
    lane_data["yellow_time"] = milliseconds
    print("yellow crossed!")
    time.sleep(0.01)

def timer_start(channel):
    milliseconds = int(round(time.time() * 1000))
    lane_data["timer_start"] = milliseconds
    print("timer started!")
    time.sleep(0.01)




# debug


# main loop
def main():

    race_ID = input("race ID: ") # race ID !! MOVE TO CLASS !!
    lanes = ["red_time", "blue_time", "green_time", "yellow_time"] # lane list !! MOVE TO CLASS !!


    # Lane triggers


    # timer
    GPIO.setup(timer_triger, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(timer_triger, GPIO.RISING, callback=timer_start)

    # red lane
    GPIO.setup(red_triger, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(red_triger, GPIO.RISING,  callback=red_callback) 

    # green lane
    GPIO.setup(green_triger, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(green_triger, GPIO.RISING,  callback=green_callback) 

    # blue lane
    GPIO.setup(blue_triger, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
    GPIO.add_event_detect(blue_triger, GPIO.RISING,  callback=blue_callback) 

    # yellow lane
    GPIO.setup(yellow_triger, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(yellow_triger, GPIO.RISING,  callback=yellow_callback) 

    wait = input("waiting for race...\r\n") # prevent main() from exiting


    # calc race times
    for i in lanes:
        race_times[i] = (lane_data[i] - lane_data["timer_start"]) / 1000


    print("RACE ", race_ID)
    print("red time: ", race_times["red_time"])
    print("blue time: ", race_times["blue_time"])
    print("green time: ", race_times["green_time"])
    print("yellow time: ", race_times["yellow_time"])


    #TODO sent data to database (either sqlite3 or mongoDB)
    #TODO add command line arguments to determine number of lanes
    #TODO add support for racer name to lane

if __name__ == "__main__":
    main()




    
    
GPIO.cleanup()  # Clean up



