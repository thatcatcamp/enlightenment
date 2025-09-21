import RPi.GPIO as gpio
import time
from time import sleep
ORANGE=25


def mm2time(millimeters):
    """
    Calculates the time in seconds needed to move a linear actuator
    a specified distance in millimeters.

    The calculation is based on an observed rate of 33 seconds
    for 66mm of travel (0.5 seconds per mm).

    Args:
      millimeters: The desired distance to travel in mm.

    Returns:
      The time in seconds required to travel that distance.
    """
    # The ratio is 33 seconds / 66 mm, which simplifies to 0.5 sec/mm
    seconds_per_mm = 0.5

    # Ensure the input is a positive number
    if millimeters < 0:
        return 0

    return millimeters * seconds_per_mm

def init():
    gpio.setmode(gpio.BCM)
    gpio.setup(17, gpio.OUT)
    gpio.setup(22, gpio.OUT)
    gpio.setup(23, gpio.OUT)
    gpio.setup(ORANGE, gpio.OUT)


def fttf(sec):
    init()
    print("f t t f")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()


def tfft(sec):
    init()
    # 1 out
    print("t f f t")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(ORANGE, True)
    input("Press Enter to continue...")
    gpio.cleanup()


def tftf(sec):
    init()
    # 1 out
    print("t f t f")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()


def ftft(sec):
    # 1 in
    init()
    print("f t f t")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(ORANGE, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def zero_in():
    init()
    # 1
    print("zero 1")
    gpio.output(17, False)
    gpio.output(22, True)
    # 0
    print("zero 2")
    gpio.output(23, False)
    gpio.output(ORANGE, True)

def zero_in_0():
    # 0
    print("zero 2")
    gpio.output(23, False)
    gpio.output(ORANGE, True)



def reset():
    init()
    zero_in_0()
    time.sleep(120)
    gpio.cleanup()



def combo_ffff(sec):
    init()
    print("f f f f - 17:F 22:F 23:F ORANGE:F")
    print("lock all")
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_ffft(sec):
    init()
    # zoer back
    print("f f f t - 17:F 22:F 23:F ORANGE:T")
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(ORANGE, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def zeroin(sec):
    init()
    print("f f t f - 17:F 22:F 23:T ORANGE:F - ZERO IN")
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_fftt(sec):
    init()
    # none
    print("f f t t - 17:F 22:F 23:T ORANGE:T")
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(ORANGE, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_ftff(sec):
    init()
    print("f t f f - 17:F 22:T 23:F ORANGE:F")
    # 1 back
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def bothin(sec):
    init()
    print("f t f t - 17:F 22:T 23:F ORANGE:T")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(ORANGE, True)
    sleep(sec)
    gpio.cleanup()

def zero_out_one_in(sec):
    init()
    print("f t t f - 17:F 22:T 23:T ORANGE:F")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_fttt(sec):
    init()
    print("f t t t - 17:F 22:T 23:T ORANGE:T")
    # 1in
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(ORANGE, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_tfff(sec):
    init()
    # 1 out
    print("t f f f - 17:T 22:F 23:F ORANGE:F")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def zeroinoneout(sec):
    init()
    print("t f f t - 17:T 22:F 23:F ORANGE:T")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(ORANGE, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def bothout(sec):
    init()
    print("t f t f - 17:T 22:F 23:T ORANGE:F")
    print(f"both out {sec}")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(ORANGE, False)
    sleep(sec)
    gpio.cleanup()

def combo_tftt(sec):
    init()
    print("t f t t - 17:T 22:F 23:T ORANGE:T")
    # 1 out
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(ORANGE, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_ttff(sec):
    init()
    print("t t f f - 17:T 22:T 23:F ORANGE:F")
    # nothing
    gpio.output(17, True)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_ttft(sec):
    init()
    print("t t f t - 17:T 22:T 23:F ORANGE:T")
    # zero in
    gpio.output(17, True)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(ORANGE, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_tttf(sec):
    init()
    print("t t t f - 17:T 22:T 23:T ORANGE:F")
    # 0 out
    gpio.output(17, True)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_tttt(sec):
    init()
    print("t t t t - 17:T 22:T 23:T ORANGE:T")
    # nothing
    gpio.output(17, True)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(ORANGE, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def m0fw(sec):
    init()
    print("ZERO FORWARD")
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def m0bw(sec):
    init()
    print("ZERO BACK")
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(ORANGE, True)
    input("Press Enter to continue...")
    gpio.cleanup()


def m1fw(sec):
    init()
    print("one FORWARD - t f f f - 17:T 22:f 23:f ORANGE:f")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()


def m1bw(sec):
    init()
    print("one BACK")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(ORANGE, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def main():
    print("homing both struts!")
    bothin(77) # hit the stop
    seconds = 33
    bothout(mm2time(150))
    exit(1)
    print("Testing all 16 GPIO combinations for pins 17,22,23,ORANGE...")
    print("Format: 17:state 22:state 23:state ORANGE:state")
    print("=" * 99)
    m0fw(seconds)
    m0bw(seconds)
    m1fw(seconds)
    m1bw(seconds)
    combo_ffff(seconds)
    combo_ffft(seconds)
#    zeroin(seconds)
    combo_fftt(seconds)
    combo_ftff(seconds)
    combo_ftft(seconds)
    combo_fttf(seconds)
    combo_fttt(seconds)
    combo_tfff(seconds)
    combo_tfft(seconds)
    combo_tftf(seconds)
    combo_tftt(seconds)
    combo_ttff(seconds)
    combo_ttft(seconds)
    combo_tttf(seconds)
    combo_tttt(seconds)

    print("=" * 50)
    print("All combinations tested!")

if __name__ == "__main__":
    main()
