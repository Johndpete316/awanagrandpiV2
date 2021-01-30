import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
import awanagrandpi_database
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
    "red": 0,
    "blue": 0,
    "green": 0,
    "yellow": 0,
    "timer_start": 0
}

race_times = {
    "red": 0,
    "blue": 0,
    "green": 0,
    "yellow": 0

}


# lane callbacks


def red_callback(channel):
    milliseconds = int(round(time.time() * 1000))
    lane_data["red"] = milliseconds
    print("red crossed!")
    time.sleep(0.01)


def blue_callback(channel):
    milliseconds = int(round(time.time() * 1000))
    lane_data["blue"] = milliseconds
    print("blue crossed!")
    time.sleep(0.05)


def green_callback(channel):
    milliseconds = int(round(time.time() * 1000))
    lane_data["green"] = milliseconds
    print("green crossed!")
    time.sleep(0.05)


def yellow_callback(channel):
    milliseconds = int(round(time.time() * 1000))
    lane_data["yellow"] = milliseconds
    print("yellow crossed!")
    time.sleep(0.05)

def timer_start(channel):
    milliseconds = int(round(time.time() * 1000))
    lane_data["timer_start"] = milliseconds
    print("timer started!")
    time.sleep(0.05)




# debug


# main loop
def main():

    race_ID = input("race ID: ") # race ID !! MOVE TO CLASS !!
    # red_lane_racer = input("Racer on red lane: ")
    # blue_lane_racer = input("Racer on blue lane: ")
    # green_lane_racer = input("Racer on green lane: ")
    # yellow_lane_racer = input("Racer on yellow lane: ")
    
    # debug
    red_lane_racer = "John"
    blue_lane_racer = "Kaylynn"
    green_lane_racer = "Timmy"
    yellow_lane_racer = "David"

    racers = {
        "red": red_lane_racer,
        "blue": blue_lane_racer,
        "green": green_lane_racer,
        "yellow": yellow_lane_racer
    }

    lanes = ["red", "blue", "green", "yellow"] # lane list !! MOVE TO CLASS !!


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

    print("RACE ", race_ID)

    # calc race times
    for i in lanes:
        race_times[i] = (lane_data[i] - lane_data["timer_start"]) / 1000
        awanagrandpi_database.insert_data(race_ID, racers[i], i, race_times[i])
        print(i, " : ", racers[i], " : ", race_times[i])



    #TODO sent data to database (either sqlite3 or mongoDB)
    #TODO add command line arguments to determine number of lanes
    #TODO add support for racer name to lane

# end main


if __name__ == "__main__":
    main()




    
    
GPIO.cleanup()  # Clean up



