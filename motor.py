import RPi.GPIO as gpio
import time


def init():
    gpio.setmode(gpio.BCM)
    gpio.setup(17, gpio.OUT)
    gpio.setup(22, gpio.OUT)
    gpio.setup(23, gpio.OUT)
    gpio.setup(24, gpio.OUT)


def fttf(sec):
    init()
    print("f t t f")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(24, False)
    input("Press Enter to continue...")
    gpio.cleanup()


def tfft(sec):
    init()
    # 1 out
    print("t f f t")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(24, True)
    input("Press Enter to continue...")
    gpio.cleanup()


def tftf(sec):
    init()
    # 1 out
    print("t f t f")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(24, False)
    input("Press Enter to continue...")
    gpio.cleanup()


def ftft(sec):
    # 1 in
    init()
    print("f t f t")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(24, True)
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
    gpio.output(24, True)

def zero_in_0():
    # 0
    print("zero 2")
    gpio.output(23, False)
    gpio.output(24, True)



def reset():
    init()
    zero_in_0()
    time.sleep(120)
    gpio.cleanup()



def combo_ffff(sec):
    init()
    print("f f f f - 17:F 22:F 23:F 24:F")
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(24, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_ffft(sec):
    init()
    print("f f f t - 17:F 22:F 23:F 24:T")
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(24, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_fftf(sec):
    init()
    print("f f t f - 17:F 22:F 23:T 24:F")
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(24, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_fftt(sec):
    init()
    print("f f t t - 17:F 22:F 23:T 24:T")
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(24, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_ftff(sec):
    init()
    print("f t f f - 17:F 22:T 23:F 24:F")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(24, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_ftft(sec):
    init()
    print("f t f t - 17:F 22:T 23:F 24:T")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(24, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_fttf(sec):
    init()
    print("f t t f - 17:F 22:T 23:T 24:F")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(24, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_fttt(sec):
    init()
    print("f t t t - 17:F 22:T 23:T 24:T")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(24, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_tfff(sec):
    init()
    print("t f f f - 17:T 22:F 23:F 24:F")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(24, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_tfft(sec):
    init()
    print("t f f t - 17:T 22:F 23:F 24:T")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(24, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_tftf(sec):
    init()
    print("t f t f - 17:T 22:F 23:T 24:F")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(24, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_tftt(sec):
    init()
    print("t f t t - 17:T 22:F 23:T 24:T")
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(24, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_ttff(sec):
    init()
    print("t t f f - 17:T 22:T 23:F 24:F")
    gpio.output(17, True)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(24, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_ttft(sec):
    init()
    print("t t f t - 17:T 22:T 23:F 24:T")
    gpio.output(17, True)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(24, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_tttf(sec):
    init()
    print("t t t f - 17:T 22:T 23:T 24:F")
    gpio.output(17, True)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(24, False)
    input("Press Enter to continue...")
    gpio.cleanup()

def combo_tttt(sec):
    init()
    print("t t t t - 17:T 22:T 23:T 24:T")
    gpio.output(17, True)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(24, True)
    input("Press Enter to continue...")
    gpio.cleanup()

def main():
    seconds = 33
    print("Testing all 16 GPIO combinations for pins 17,22,23,24...")
    print("Format: 17:state 22:state 23:state 24:state")
    print("=" * 99)

    combo_ffff(seconds)
    combo_ffft(seconds)
    combo_fftf(seconds)
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
