import json

from rd03d import RD03D
import time

# Initialize radar with Pi 5 UART settings
radar = RD03D()  # Uses /dev/ttyAMA0 by default

radar.set_multi_mode(True)   # Switch to multi-target mode

while True:
    if radar.update():
        try:
            target1 = radar.get_target(1)
            target2 = radar.get_target(2)
            target3 = radar.get_target(3)
            position = { 'distance_mm': target1.distance, 'angle': target1.angle, 'speed': target1.speed, 'x': target1.x, 'y': target1.y }
            print(json.dumps(position, indent=4))
            print('1 dist:', target1.distance, 'mm Angle:', target1.angle, " deg Speed:", target1.speed, "cm/s X:", target1.x, "mm Y:", target1.y, "mm")
        except Exception as e:
            print(e)

    else:
        print('No radar data received.')

    time.sleep(1)
