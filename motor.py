import RPi.GPIO as gpio
import time
import math
import os
import sys
from time import sleep
from flask import Flask, jsonify, request, render_template_string
ORANGE=25
DUTY_CYCLE=.001
ACTIVE_SECONDS=0
MOVE_SECONDS=0
DISTANCE_RADAR_TO_AXIS_CM=75
MAX_OUT_MM = 120
MAX_MOVE_SECONDS = 30
LIGHT_HEIGHT_CM = 300
X_AT = 0
Y_AT = 0
# Per-strut calibration (both struts now move 130mm in 10 seconds)
SECONDS_PER_MM_STRUT0 = 0.0769  # 10 seconds / 130mm = 0.0769 sec/mm
SECONDS_PER_MM_STRUT1 = 0.0769  # 10 seconds / 130mm = 0.0769 sec/mm
VERSION = "1.0.0"

# Flask app setup
app = Flask(__name__)


def calculate_actuator_offsets(angle_offset, distance_mm, current_x, current_y):
    """
    Calculates the required X and Y actuator offsets to aim a spotlight at a target.

    Args:
        angle_offset (float): The angular offset from the RADAR (-90 to 90 degrees).
        distance_mm (float): The distance to the target from the RADAR in mm.
        current_x (float): The current extension of the X-axis (pan) actuator in mm.
        current_y (float): The current extension of the Y-axis (tilt) actuator in mm.

    Returns:
        tuple[float, float]: A tuple containing the required (x_offset, y_offset)
                             in millimeters to move the actuators.
    """
    # --- 1. Unit Conversion ---
    # Convert all dimensions to millimeters for consistent calculations.
    light_height_mm = LIGHT_HEIGHT_CM * 10
    radar_to_axis_mm = DISTANCE_RADAR_TO_AXIS_CM * 10

    # --- 2. Calculate Target's Ground Coordinates ---
    # Convert the RADAR's polar coordinates (angle, distance) to Cartesian coordinates (x, y)
    # on the playa floor, relative to the spotlight's pivot point.
    angle_rad = math.radians(angle_offset)

    # Calculate the target's position relative to the RADAR sensor
    target_x_from_radar = distance_mm * math.sin(angle_rad)
    target_y_from_radar = distance_mm * math.cos(angle_rad)

    # The target's X position is the same relative to the pivot.
    # The target's Y position is the distance from the radar plus the radar-to-axis distance.
    target_x_on_playa = target_x_from_radar
    target_y_on_playa = target_y_from_radar + radar_to_axis_mm

    # --- 3. Determine Required Pan and Tilt Angles ---
    # Calculate the horizontal (pan) angle from the pivot to the target.
    # atan2 is used to get the correct angle in all quadrants.
    pan_angle_rad = math.atan2(target_x_on_playa, target_y_on_playa)
    pan_angle_deg = math.degrees(pan_angle_rad)

    # Calculate the vertical (tilt) angle. First, find the straight-line distance
    # on the ground from the pivot point to the target.
    horizontal_distance_to_target = math.sqrt(target_x_on_playa ** 2 + target_y_on_playa ** 2)

    # Now, find the tilt angle from straight down (0 degrees) to the target.
    tilt_angle_rad = math.atan2(horizontal_distance_to_target, light_height_mm)
    tilt_angle_deg = math.degrees(tilt_angle_rad)

    # --- 4. Translate Angles to Target Actuator Extensions ---
    # This assumes a linear mapping from angle to actuator extension.
    # Pan (X-axis): -90 to +90 degrees maps to 0 to MAX_OUT_MM
    # Tilt (Y-axis): 0 (down) to 90 degrees (horizon) maps to 50% to 100% extension.

    home_position = MAX_OUT_MM / 2.0

    # Calculate target X extension
    mm_per_pan_degree = MAX_OUT_MM / 180.0  # 180-degree total range
    target_x = home_position + (pan_angle_deg * mm_per_pan_degree)

    # Calculate target Y extension
    # The tilt actuator moves from 50% to 100% to cover the 0-90 degree range.
    mm_per_tilt_degree = home_position / 90.0  # 90-degree total range uses half the actuator travel
    target_y = home_position + (tilt_angle_deg * mm_per_tilt_degree)

    # --- 5. Clamp values to ensure they are within physical limits ---
    target_x = max(0.0, min(MAX_OUT_MM, target_x))
    target_y = max(0.0, min(MAX_OUT_MM, target_y))

    # --- 6. Calculate Final Offsets ---
    x_offset = target_x - current_x
    y_offset = target_y - current_y

    return (x_offset, y_offset)

def compute_rotation(from_x, from_y, to_x, to_y):
    """
    Compute travel times for each strut to move spotlight from one position to another.

    Args:
        from_x, from_y: Current position (cm)
        to_x, to_y: Target position (cm)

    Returns:
        (strut0_seconds, strut1_seconds): Travel times in seconds
        Positive = extend, Negative = retract
    """
    print(f"compute {from_x}, {from_y}, {to_x}, {to_y}")
    new_x = (to_x - from_x) * 10  # Convert cm to mm
    new_y = (to_y - from_y) * 10  # Convert cm to mm
    return mm2time(new_x, 0), mm2time(new_y, 1)  # Use per-strut calibration

def move_strut0(seconds):
    """Move strut 0 (positive=extend, negative=retract)"""
    global X_AT, Y_AT
    init()
    if seconds > 0:
        print(f"Extending strut 0 for {seconds:.1f}s")
        gpio.output(17, True)   # Forward
        gpio.output(22, False)
        gpio.output(23, False)
        gpio.output(ORANGE, False)
    else:
        print(f"Retracting strut 0 for {abs(seconds):.1f}s")
        gpio.output(17, False)  # Backward
        gpio.output(22, True)
        gpio.output(23, False)
        gpio.output(ORANGE, False)

    let_move(abs(seconds))

    # Update X position tracking (strut0 controls X axis)
    # Convert time back to distance: seconds / SECONDS_PER_MM_STRUT0 = mm, then mm/10 = cm
    distance_cm = (seconds / SECONDS_PER_MM_STRUT0) / 10.0
    X_AT += distance_cm
    print(f"Updated X_AT to {X_AT:.2f} cm")

    gpio.cleanup()

def move_strut1(seconds):
    """Move strut 1 (positive=extend, negative=retract)"""
    global X_AT, Y_AT
    init()
    if seconds > 0:
        print(f"Extending strut 1 for {seconds:.1f}s")
        gpio.output(17, False)
        gpio.output(22, False)
        gpio.output(23, True)   # Forward
        gpio.output(ORANGE, False)
    else:
        print(f"Retracting strut 1 for {abs(seconds):.1f}s")
        gpio.output(17, False)
        gpio.output(22, False)
        gpio.output(23, False)  # Backward
        gpio.output(ORANGE, True)

    let_move(abs(seconds))

    # Update Y position tracking (strut1 controls Y axis)
    # Convert time back to distance: seconds / SECONDS_PER_MM_STRUT1 = mm, then mm/10 = cm
    distance_cm = (seconds / SECONDS_PER_MM_STRUT1) / 10.0
    Y_AT += distance_cm
    print(f"Updated Y_AT to {Y_AT:.2f} cm")

    gpio.cleanup()

def move_to_position(target_x, target_y):
    """Move spotlight to target position"""
    global X_AT, Y_AT

    # Calculate required movements
    strut0_time, strut1_time = compute_rotation(X_AT, Y_AT, target_x, target_y)

    # Apply cooling if needed
    cool_down()

    # Move struts (could be done simultaneously, but doing sequentially for safety)
    if abs(strut0_time) > 0.1:  # Only move if significant
        move_strut0(strut0_time)
        cool_down()

    if abs(strut1_time) > 0.1:  # Only move if significant
        move_strut1(strut1_time)
        cool_down()

    # Update current position
    X_AT = target_x
    Y_AT = target_y
    print(f"Now at position: ({X_AT}, {Y_AT})")

def let_move(seconds):
    global ACTIVE_SECONDS, MOVE_SECONDS, DUTY_CYCLE
    print("sleeping for structs to move")
    sleep(seconds)
    ACTIVE_SECONDS=ACTIVE_SECONDS+seconds
    MOVE_SECONDS=MOVE_SECONDS+seconds
    DUTY_CYCLE=ACTIVE_SECONDS/MOVE_SECONDS
    print(f"active: {ACTIVE_SECONDS} / move: {MOVE_SECONDS} / cycle: {DUTY_CYCLE}")


def let_wait(seconds):
    global ACTIVE_SECONDS, MOVE_SECONDS, DUTY_CYCLE
    print("sleeping for cooldown")
    sleep(seconds)
    MOVE_SECONDS = MOVE_SECONDS + seconds  # Add to total time
    DUTY_CYCLE = ACTIVE_SECONDS / MOVE_SECONDS  # Correct calculation
    print(f"active: {ACTIVE_SECONDS} / move: {MOVE_SECONDS} / cycle: {DUTY_CYCLE}")

def cool_down():
    global ACTIVE_SECONDS, MOVE_SECONDS, DUTY_CYCLE
    # loop and continue to sleep until the duty cycle gets below .22
    while DUTY_CYCLE > .22:
        print(f"Duty cycle {DUTY_CYCLE:.3f} too high, cooling down...")
        let_wait(10)

def mm2time(millimeters, strut_num):
    """
    Calculates the time in seconds needed to move a linear actuator
    a specified distance in millimeters.

    The calculation uses per-strut calibration rates:
    - Strut 0: 5 seconds for 20mm (0.25 sec/mm)
    - Strut 1: 5 seconds for 16mm (0.3125 sec/mm)

    Args:
      millimeters: The desired distance to travel in mm.
      strut_num: Which strut (0 or 1) to get calibration for.

    Returns:
      The time in seconds required to travel that distance.
    """
    if strut_num == 0:
        seconds_per_mm = SECONDS_PER_MM_STRUT0
    else:
        seconds_per_mm = SECONDS_PER_MM_STRUT1

    return millimeters * seconds_per_mm

def init():
    gpio.setmode(gpio.BCM)
    gpio.setup(17, gpio.OUT)
    gpio.setup(22, gpio.OUT)
    gpio.setup(23, gpio.OUT)
    gpio.setup(ORANGE, gpio.OUT)


# def fttf(sec):
#     init()
#     print("f t t f")
#     gpio.output(17, False)
#     gpio.output(22, True)
#     gpio.output(23, True)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()


# def tfft(sec):
#     init()
#     # 1 out
#     print("t f f t")
#     gpio.output(17, True)
#     gpio.output(22, False)
#     gpio.output(23, False)
#     gpio.output(ORANGE, True)
#     input("Press Enter to continue...")
#     gpio.cleanup()


# def tftf(sec):
#     init()
#     # 1 out
#     print("t f t f")
#     gpio.output(17, True)
#     gpio.output(22, False)
#     gpio.output(23, True)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()


# def ftft(sec):
#     # 1 in
#     init()
#     print("f t f t")
#     gpio.output(17, False)
#     gpio.output(22, True)
#     gpio.output(23, False)
#     gpio.output(ORANGE, True)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def zero_in():
#     init()
#     # 1
#     print("zero 1")
#     gpio.output(17, False)
#     gpio.output(22, True)
#     # 0
#     print("zero 2")
#     gpio.output(23, False)
#     gpio.output(ORANGE, True)

# def zero_in_0():
#     # 0
#     print("zero 2")
#     gpio.output(23, False)
#     gpio.output(ORANGE, True)



# def reset():  # OLD UNUSED reset function - different from Flask route
#     init()
#     zero_in_0()
#     time.sleep(120)
#     gpio.cleanup()



# def combo_ffff(sec):
#     init()
#     print("f f f f - 17:F 22:F 23:F ORANGE:F")
#     print("lock all")
#     gpio.output(17, False)
#     gpio.output(22, False)
#     gpio.output(23, False)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def combo_ffft(sec):
#     init()
#     # zoer back
#     print("f f f t - 17:F 22:F 23:F ORANGE:T")
#     gpio.output(17, False)
#     gpio.output(22, False)
#     gpio.output(23, False)
#     gpio.output(ORANGE, True)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def zeroin(sec):
#     init()
#     print("f f t f - 17:F 22:F 23:T ORANGE:F - ZERO IN")
#     gpio.output(17, False)
#     gpio.output(22, False)
#     gpio.output(23, True)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def combo_fftt(sec):
#     init()
#     # none
#     print("f f t t - 17:F 22:F 23:T ORANGE:T")
#     gpio.output(17, False)
#     gpio.output(22, False)
#     gpio.output(23, True)
#     gpio.output(ORANGE, True)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def combo_ftff(sec):
#     init()
#     print("f t f f - 17:F 22:T 23:F ORANGE:F")
#     # 1 back
#     gpio.output(17, False)
#     gpio.output(22, True)
#     gpio.output(23, False)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()

def bothin(sec):
    init()
    print("f t f t - 17:F 22:T 23:F ORANGE:T")
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(ORANGE, True)
    let_move(sec)  # remember duty cycle
    gpio.cleanup()

# DEAD FUNCTIONS - GPIO testing/debug code from development
# def zero_out_one_in(sec):
#     init()
#     print("f t t f - 17:F 22:T 23:T ORANGE:F")
#     gpio.output(17, False)
#     gpio.output(22, True)
#     gpio.output(23, True)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def combo_fttt(sec):
#     init()
#     print("f t t t - 17:F 22:T 23:T ORANGE:T")
#     # 1in
#     gpio.output(17, False)
#     gpio.output(22, True)
#     gpio.output(23, True)
#     gpio.output(ORANGE, True)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def combo_tfff(sec):
#     init()
#     # 1 out
#     print("t f f f - 17:T 22:F 23:F ORANGE:F")
#     gpio.output(17, True)
#     gpio.output(22, False)
#     gpio.output(23, False)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def zeroinoneout(sec):
#     init()
#     print("t f f t - 17:T 22:F 23:F ORANGE:T")
#     gpio.output(17, True)
#     gpio.output(22, False)
#     gpio.output(23, False)
#     gpio.output(ORANGE, True)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def bothout(sec):
#     init()
#     print("t f t f - 17:T 22:F 23:T ORANGE:F")
#     print(f"both out {sec}")
#     gpio.output(17, True)
#     gpio.output(22, False)
#     gpio.output(23, True)
#     gpio.output(ORANGE, False)
#     let_move(sec)  # remember duty cycle
#     gpio.cleanup()

# def combo_tftt(sec):
#     init()
#     print("t f t t - 17:T 22:F 23:T ORANGE:T")
#     # 1 out
#     gpio.output(17, True)
#     gpio.output(22, False)
#     gpio.output(23, True)
#     gpio.output(ORANGE, True)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def combo_ttff(sec):
#     init()
#     print("t t f f - 17:T 22:T 23:F ORANGE:F")
#     # nothing
#     gpio.output(17, True)
#     gpio.output(22, True)
#     gpio.output(23, False)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def combo_ttft(sec):
#     init()
#     print("t t f t - 17:T 22:T 23:F ORANGE:T")
#     # zero in
#     gpio.output(17, True)
#     gpio.output(22, True)
#     gpio.output(23, False)
#     gpio.output(ORANGE, True)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def combo_tttf(sec):
#     init()
#     print("t t t f - 17:T 22:T 23:T ORANGE:F")
#     # 0 out
#     gpio.output(17, True)
#     gpio.output(22, True)
#     gpio.output(23, True)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def combo_tttt(sec):
#     init()
#     print("t t t t - 17:T 22:T 23:T ORANGE:T")
#     # nothing
#     gpio.output(17, True)
#     gpio.output(22, True)
#     gpio.output(23, True)
#     gpio.output(ORANGE, True)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def m0fw(sec):
#     init()
#     print("ZERO FORWARD")
#     gpio.output(17, False)
#     gpio.output(22, False)
#     gpio.output(23, True)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def m0bw(sec):
#     init()
#     print("ZERO BACK")
#     gpio.output(17, False)
#     gpio.output(22, False)
#     gpio.output(23, False)
#     gpio.output(ORANGE, True)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def m1fw(sec):
#     init()
#     print("one FORWARD - t f f f - 17:T 22:f 23:f ORANGE:f")
#     gpio.output(17, True)
#     gpio.output(22, False)
#     gpio.output(23, False)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# def m1bw(sec):
#     init()
#     print("one BACK")
#     gpio.output(17, False)
#     gpio.output(22, True)
#     gpio.output(23, False)
#     gpio.output(ORANGE, False)
#     input("Press Enter to continue...")
#     gpio.cleanup()

# HTTP API Endpoints
@app.route('/', methods=['GET'])
def home():
    """Test interface for motor control"""
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Motor Control Test Interface</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .section h3 { margin-top: 0; color: #333; }
        button { padding: 8px 15px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #007bff; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-info { background: #17a2b8; color: white; }
        input[type="number"], input[type="text"] { padding: 5px; margin: 2px; border: 1px solid #ccc; border-radius: 3px; width: 80px; }
        .inline { display: inline-block; margin: 5px; }
        .response { margin-top: 10px; padding: 10px; background: #f8f9fa; border-left: 4px solid #007bff; font-family: monospace; white-space: pre-wrap; }
        .status { padding: 5px 10px; border-radius: 3px; font-weight: bold; }
        .status.ok { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Motor Control Test Interface</h1>
        <p><em>"Ours is the stage of calamity, on which we deliver the dance of death."</em></p>

        <div class="section">
            <h3>📍 Current Position</h3>
            <button class="btn-info" onclick="getCurrentPosition()">Get Current X,Y</button>
            <div id="position-response" class="response" style="display:none;"></div>
        </div>

        <div class="section">
            <h3>🎯 Target Control</h3>
            <div class="inline">
                <label>Angle (-90 to 90):</label>
                <input type="number" id="angle" value="0" min="-90" max="90" step="0.1">
            </div>
            <div class="inline">
                <label>Distance (mm):</label>
                <input type="number" id="distance" value="1000" min="0" max="8000" step="100">
            </div>
            <button class="btn-primary" onclick="moveToTarget()">Move to Target</button>
            <div id="target-response" class="response" style="display:none;"></div>
        </div>

        <div class="section">
            <h3>🔧 Individual Strut Testing</h3>
            <h4>Strut 0 (X-axis)</h4>
            <div class="inline">
                <label>Seconds:</label>
                <input type="number" id="strut0-seconds" value="1.0" min="0.1" max="30" step="0.1">
            </div>
            <button class="btn-warning" onclick="moveStrut(0, 'in')">Retract</button>
            <button class="btn-success" onclick="moveStrut(0, 'out')">Extend</button>
            <button class="btn-danger" onclick="moveStrut(0, 'in', true)">Force Retract</button>
            <button class="btn-danger" onclick="moveStrut(0, 'out', true)">Force Extend</button>

            <h4>Strut 1 (Y-axis)</h4>
            <div class="inline">
                <label>Seconds:</label>
                <input type="number" id="strut1-seconds" value="1.0" min="0.1" max="30" step="0.1">
            </div>
            <button class="btn-warning" onclick="moveStrut(1, 'in')">Retract</button>
            <button class="btn-success" onclick="moveStrut(1, 'out')">Extend</button>
            <button class="btn-danger" onclick="moveStrut(1, 'in', true)">Force Retract</button>
            <button class="btn-danger" onclick="moveStrut(1, 'out', true)">Force Extend</button>

            <div id="strut-response" class="response" style="display:none;"></div>
        </div>

        <div class="section">
            <h3>📏 Precise Distance Movement</h3>
            <h4>Strut 0 (X-axis) - Rate: 0.0769 sec/mm</h4>
            <div class="inline">
                <label>Distance (mm):</label>
                <input type="number" id="strut0-mm" value="20" min="-120" max="120" step="1">
            </div>
            <button class="btn-primary" onclick="moveToMM(0)">Move Distance</button>
            <button class="btn-danger" onclick="moveToMM(0, true)">Force Move</button>

            <h4>Strut 1 (Y-axis) - Rate: 0.0769 sec/mm</h4>
            <div class="inline">
                <label>Distance (mm):</label>
                <input type="number" id="strut1-mm" value="20" min="-120" max="120" step="1">
            </div>
            <button class="btn-primary" onclick="moveToMM(1)">Move Distance</button>
            <button class="btn-danger" onclick="moveToMM(1, true)">Force Move</button>

            <div id="moveto-response" class="response" style="display:none;"></div>
        </div>

        <div class="section">
            <h3>🔄 System Control</h3>
            <button class="btn-warning" onclick="resetSystem()">Reset System</button>
            <button class="btn-danger" onclick="shutdownSystem()">Shutdown</button>
            <div id="system-response" class="response" style="display:none;"></div>
        </div>
    </div>

    <script>
        async function makeRequest(url, method = 'GET') {
            try {
                const response = await fetch(url, { method: method });
                const data = await response.json();
                return { ok: response.ok, data: data };
            } catch (error) {
                return { ok: false, data: { error: error.message } };
            }
        }

        function showResponse(elementId, result, url) {
            const element = document.getElementById(elementId);
            element.style.display = 'block';
            element.innerHTML = `
                <div class="status ${result.ok ? 'ok' : 'error'}">
                    ${result.ok ? '✅ Success' : '❌ Error'}
                </div>
                <strong>URL:</strong> ${url}
                <strong>Response:</strong>
                ${JSON.stringify(result.data, null, 2)}
            `;
        }

        async function getCurrentPosition() {
            const result = await makeRequest('/current_xy');
            showResponse('position-response', result, '/current_xy');
        }

        async function moveToTarget() {
            const angle = document.getElementById('angle').value;
            const distance = document.getElementById('distance').value;
            const url = `/target?angle=${angle}&distance=${distance}`;
            const result = await makeRequest(url);
            showResponse('target-response', result, url);
        }

        async function moveStrut(strutNum, direction, force = false) {
            const seconds = document.getElementById(`strut${strutNum}-seconds`).value;
            const forceParam = force ? '/force' : '';
            const url = `/${direction}/${strutNum}/${seconds}${forceParam}`;
            const result = await makeRequest(url);
            showResponse('strut-response', result, url);
        }

        async function moveToMM(strutNum, force = false) {
            const mm = document.getElementById(`strut${strutNum}-mm`).value;
            const forceParam = force ? '/force' : '';
            const url = `/moveto/${strutNum}/${mm}${forceParam}`;
            const result = await makeRequest(url);
            showResponse('moveto-response', result, url);
        }

        async function resetSystem() {
            const result = await makeRequest('/reset');
            showResponse('system-response', result, '/reset');
        }

        async function shutdownSystem() {
            if (confirm('Are you sure you want to shutdown the system?')) {
                const result = await makeRequest('/shutdown', 'POST');
                showResponse('system-response', result, '/shutdown');
            }
        }

        // Auto-refresh position every 5 seconds
        setInterval(getCurrentPosition, 5000);
        getCurrentPosition(); // Initial load
    </script>
</body>
</html>
    """
    return render_template_string(html_template)

@app.route('/current_xy', methods=['GET'])
def get_current_xy():
    """Get current X,Y position of the spotlight"""
    global X_AT, Y_AT
    return jsonify({
        'x': X_AT,
        'y': Y_AT,
        'status': 'success'
    })

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Shutdown the microservice"""
    try:
        gpio.cleanup()
        return jsonify({'status': 'shutting down'})
    finally:
        # Give time for response to send
        import threading
        def delayed_shutdown():
            time.sleep(1)
            os._exit(0)
        threading.Thread(target=delayed_shutdown).start()

@app.route('/target', methods=['GET'])
def target():
    """Move spotlight to target based on angle offset and distance

    Query params:
        angle: float - angle offset from radar (-90 to 90 degrees)
        distance: float - distance in mm (max ~8000)
    """
    try:
        # Check duty cycle first
        global DUTY_CYCLE, ACTIVE_SECONDS, MOVE_SECONDS
        if DUTY_CYCLE > 0.22:
            # Calculate estimated cooldown time
            # duty_cycle = active_seconds / move_seconds
            # We need: 0.22 = active_seconds / (move_seconds + additional_wait_time)
            # Solving for additional_wait_time: additional_wait_time = (active_seconds / 0.22) - move_seconds
            estimated_cooldown = max(0, (ACTIVE_SECONDS / 0.22) - MOVE_SECONDS)

            return jsonify({
                'status': 'cooling_down',
                'message': 'Duty cycle is above cutoff, waiting for cooldown',
                'current_duty_cycle': round(DUTY_CYCLE, 3),
                'cutoff_threshold': 0.22,
                'estimated_cooldown_seconds': round(estimated_cooldown, 1)
            }), 200

        # Get parameters
        angle_offset = float(request.args.get('angle', 0))
        distance_mm = float(request.args.get('distance', 0))

        # Validate parameters
        if not (-90 <= angle_offset <= 90):
            return jsonify({'error': 'angle must be between -90 and 90 degrees'}), 400
        if not (0 <= distance_mm <= 8000):
            return jsonify({'error': 'distance must be between 0 and 8000 mm'}), 400
        new_x, new_y = calculate_actuator_offsets(angle_offset, distance_mm, X_AT, Y_AT)
        move_to_position(new_x, new_y)
        # TODO: User will implement the targeting logic here
        # Placeholder response for now
        return jsonify({
            'status': 'targeting',
            'angle_offset': angle_offset,
            'distance_mm': distance_mm,
            'current_x': X_AT,
            'current_y': Y_AT,
            'new_x': new_x,
            'new_y': new_y,
        })

    except ValueError:
        return jsonify({'error': 'Invalid parameters - angle and distance must be numbers'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/in/<int:strut>/<seconds>', methods=['GET'])
@app.route('/in/<int:strut>/<seconds>/<bypass>', methods=['GET'])
def retract_strut(strut, seconds, bypass=None):
    """Retract a specific strut for calibration testing

    Args:
        strut: Strut number (0 or 1)
        seconds: Time to run the motor (positive value, will be negated for retraction)
    """
    try:
        # Convert seconds to float
        seconds = float(seconds)

        # Validate strut number
        if strut not in [0, 1]:
            return jsonify({'error': 'strut must be 0 or 1'}), 400

        # Validate seconds (should be positive, we'll negate it for retraction)
        if seconds <= 0:
            return jsonify({'error': 'seconds must be positive'}), 400

        if seconds > MAX_MOVE_SECONDS:
            return jsonify({'error': f'seconds cannot exceed {MAX_MOVE_SECONDS}'}), 400

        # Check duty cycle (unless bypassed for testing)
        global DUTY_CYCLE, ACTIVE_SECONDS, MOVE_SECONDS
        if DUTY_CYCLE > 0.22 and bypass != 'force':
            estimated_cooldown = max(0, (ACTIVE_SECONDS / 0.22) - MOVE_SECONDS)
            return jsonify({
                'status': 'cooling_down',
                'message': 'Duty cycle is above cutoff, waiting for cooldown. Use /in/<strut>/<seconds>/force to bypass',
                'current_duty_cycle': round(DUTY_CYCLE, 3),
                'estimated_cooldown_seconds': round(estimated_cooldown, 1)
            }), 200

        # Retract the specified strut (negative value for retraction)
        if strut == 0:
            move_strut0(-seconds)
        else:
            move_strut1(-seconds)

        return jsonify({
            'status': 'success',
            'action': 'retract',
            'strut': strut,
            'seconds': seconds,
            'message': f'Strut {strut} retracted for {seconds} seconds'
        })

    except ValueError:
        return jsonify({'error': 'seconds must be a valid number'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/out/<int:strut>/<seconds>', methods=['GET'])
@app.route('/out/<int:strut>/<seconds>/<bypass>', methods=['GET'])
def extend_strut(strut, seconds, bypass=None):
    """Extend a specific strut for calibration testing

    Args:
        strut: Strut number (0 or 1)
        seconds: Time to run the motor (positive value for extension)
    """
    try:
        # Convert seconds to float
        seconds = float(seconds)

        # Validate strut number
        if strut not in [0, 1]:
            return jsonify({'error': 'strut must be 0 or 1'}), 400

        # Validate seconds
        if seconds <= 0:
            return jsonify({'error': 'seconds must be positive'}), 400

        if seconds > MAX_MOVE_SECONDS:
            return jsonify({'error': f'seconds cannot exceed {MAX_MOVE_SECONDS}'}), 400

        # Check duty cycle (unless bypassed for testing)
        global DUTY_CYCLE, ACTIVE_SECONDS, MOVE_SECONDS
        if DUTY_CYCLE > 0.22 and bypass != 'force':
            estimated_cooldown = max(0, (ACTIVE_SECONDS / 0.22) - MOVE_SECONDS)
            return jsonify({
                'status': 'cooling_down',
                'message': 'Duty cycle is above cutoff, waiting for cooldown. Use /out/<strut>/<seconds>/force to bypass',
                'current_duty_cycle': round(DUTY_CYCLE, 3),
                'estimated_cooldown_seconds': round(estimated_cooldown, 1)
            }), 200

        # Extend the specified strut (positive value for extension)
        if strut == 0:
            move_strut0(seconds)
        else:
            move_strut1(seconds)

        return jsonify({
            'status': 'success',
            'action': 'extend',
            'strut': strut,
            'seconds': seconds,
            'message': f'Strut {strut} extended for {seconds} seconds'
        })

    except ValueError:
        return jsonify({'error': 'seconds must be a valid number'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/moveto/<int:strut>/<mm>', methods=['GET'])
@app.route('/moveto/<int:strut>/<mm>/<bypass>', methods=['GET'])
def move_to_mm(strut, mm, bypass=None):
    """Move a specific strut a specified distance in millimeters

    Args:
        strut: Strut number (0 or 1)
        mm: Distance to move in millimeters (positive=extend, negative=retract)
        bypass: Optional 'force' to bypass duty cycle check
    """
    try:
        # Convert mm to float
        mm = float(mm)

        # Validate strut number
        if strut not in [0, 1]:
            return jsonify({'error': 'strut must be 0 or 1'}), 400

        # Validate distance
        if abs(mm) > 120:  # MAX_OUT_MM
            return jsonify({'error': f'distance cannot exceed {MAX_OUT_MM}mm'}), 400

        # Convert millimeters to seconds using per-strut calibration
        seconds = mm2time(abs(mm), strut)
        if mm < 0:
            seconds = -seconds  # Negative for retraction

        # Validate time limit
        if abs(seconds) > MAX_MOVE_SECONDS:
            return jsonify({'error': f'calculated time {abs(seconds):.2f}s exceeds {MAX_MOVE_SECONDS}s limit'}), 400

        # Check duty cycle (unless bypassed for testing)
        global DUTY_CYCLE, ACTIVE_SECONDS, MOVE_SECONDS
        if DUTY_CYCLE > 0.22 and bypass != 'force':
            estimated_cooldown = max(0, (ACTIVE_SECONDS / 0.22) - MOVE_SECONDS)
            return jsonify({
                'status': 'cooling_down',
                'message': f'Duty cycle is above cutoff, waiting for cooldown. Use /moveto/{strut}/{mm}/force to bypass',
                'current_duty_cycle': round(DUTY_CYCLE, 3),
                'estimated_cooldown_seconds': round(estimated_cooldown, 1)
            }), 200

        # Move the specified strut
        if strut == 0:
            move_strut0(seconds)
        else:
            move_strut1(seconds)

        return jsonify({
            'status': 'success',
            'action': 'extend' if mm > 0 else 'retract',
            'strut': strut,
            'distance_mm': mm,
            'calculated_seconds': round(seconds, 3),
            'calibration_rate': SECONDS_PER_MM_STRUT0 if strut == 0 else SECONDS_PER_MM_STRUT1,
            'message': f'Strut {strut} moved {mm}mm in {abs(seconds):.2f} seconds'
        })

    except ValueError:
        return jsonify({'error': 'mm must be a valid number'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['GET'])
def reset():
    global X_AT, Y_AT, ORANGE, DUTY_CYCLE
    bothin(77)  # hit the stop
    X_AT = Y_AT = 0  # back to center
    DUTY_CYCLE = 0  # this is boot up - doesn't count
    return jsonify({})


# DEAD TESTING FUNCTION - was used for development testing
# def main():
#     global X_AT, Y_AT
#     print("homing both struts!")
#     print(compute_rotation(0,0,5,5))
#     # Assume the actuators are currently at their home position (50% extension)
#     current_actuator_x = MAX_OUT_MM / 2.0  # 75.0 mm
#     current_actuator_y = MAX_OUT_MM / 2.0  # 75.0 mm

#     # --- Scenario 1: Target is 30 degrees to the right, 10 meters away ---
#     angle_1 = 30.0  # degrees
#     distance_1 = 10000.0  # mm (10 meters)

#     x_off, y_off = calculate_actuator_offsets(angle_1, distance_1, current_actuator_x, current_actuator_y)

#     print(f"--- Scenario 1: Target at {angle_1} deg, {distance_1 / 1000}m ---")
#     print(f"Current Position (X, Y): ({current_actuator_x:.2f} mm, {current_actuator_y:.2f} mm)")
#     print(f"Required Offset (X, Y): ({x_off:.2f} mm, {y_off:.2f} mm)")
#     print(
#         f"New Target Position (X, Y): ({(current_actuator_x + x_off):.2f} mm, {(current_actuator_y + y_off):.2f} mm)\n")

#     # --- Scenario 2: Target is 20 degrees to the left, 5 meters away ---
#     angle_2 = -20.0  # degrees
#     distance_2 = 5000.0  # mm (5 meters)

#     x_off, y_off = calculate_actuator_offsets(angle_2, distance_2, current_actuator_x, current_actuator_y)

#     print(f"--- Scenario 2: Target at {angle_2} deg, {distance_2 / 1000}m ---")
#     print(f"Current Position (X, Y): ({current_actuator_x:.2f} mm, {current_actuator_y:.2f} mm)")
#     print(f"Required Offset (X, Y): ({x_off:.2f} mm, {y_off:.2f} mm)")
#     print(f"New Target Position (X, Y): ({(current_actuator_x + x_off):.2f} mm, {(current_actuator_y + y_off):.2f} mm)")
#     exit(1)
#     bothin(77) # hit the stop
#     X_AT = Y_AT = 0 # back to center
#     let_wait(20)
#     seconds = 33
#     bothout(mm2time(150))
#     exit(1)
#     print("Testing all 16 GPIO combinations for pins 17,22,23,ORANGE...")
#     print("Format: 17:state 22:state 23:state ORANGE:state")
#     print("=" * 99)
#     m0fw(seconds)
#     m0bw(seconds)
#     m1fw(seconds)
#     m1bw(seconds)
#     combo_ffff(seconds)
#     combo_ffft(seconds)
# #    zeroin(seconds)
#     combo_fftt(seconds)
#     combo_ftff(seconds)
#     combo_ftft(seconds)
#     combo_fttf(seconds)  # MISSING FUNCTION - BUG
#     combo_fttt(seconds)
#     combo_tfff(seconds)
#     combo_tfft(seconds)  # MISSING FUNCTION - BUG
#     combo_tftf(seconds)
#     combo_tftt(seconds)
#     combo_ttff(seconds)
#     combo_ttft(seconds)
#     combo_tttf(seconds)
#     combo_tttt(seconds)

#     print("=" * 50)
#     print("All combinations tested!")

if __name__ == "__main__":
    import sys
    # Run as HTTP microservice
    print("Starting motor control microservice...")
    print("Endpoints:")
    print("  GET  /current_xy - Get current X,Y position")
    print("  POST /shutdown   - Shutdown the service")
    print("  GET  /target?angle=<deg>&distance=<mm> - Target spotlight")
    print("  GET  /in/<strut>/<seconds> - Retract strut for testing")
    print("  GET  /out/<strut>/<seconds> - Extend strut for testing")
    print("  GET  /in/<strut>/<seconds>/force - Retract strut bypassing duty cycle")
    print("  GET  /out/<strut>/<seconds>/force - Extend strut bypassing duty cycle")
    print("  GET  /moveto/<strut>/<mm> - Move strut specific distance in mm")
    print("  GET  /moveto/<strut>/<mm>/force - Move strut mm bypassing duty cycle")
    print("\nStarting server on http://0.0.0.0:5000")
    #bothin(28)  # hit the stop
    X_AT = Y_AT = 0  # back to center
    DUTY_CYCLE = 0  # this is boot up - doesn't count
    move_strut0(5)
    move_strut1(5)
    app.run(host='0.0.0.0', port=5000, debug=False)

