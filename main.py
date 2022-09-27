import cv2
import os
import keyboard
import time
import datetime
from gpiozero import LED
from adafruit_servokit import ServoKit

from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685


def main():
    # PCA9685 Init
    i2c_bus = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c_bus)
    pca.frequency = 40
    debug_mode = True  # Change this to True to cause m to be Shutodwn, False for NewSession
    usb_root = '/media/pi/SamsungUSB'
    fps = 1
    kit = ServoKit(channels=16)
    kit.servo[0].set_pulse_width_range(500, 2500)
    kit.servo[0].actuation_range = 270
    servo_angle = 125
    # All Modes of Operation:
    mode = ["PASSIVE", "WATERSKI", "WAKEBOARD", "TUBING", "NEWSESSION"]
    active_mode = 0
    operation_light = LED(17)
    water_ski_light = LED(27)
    wake_board_light = LED(22)
    tube_light = LED(23)
    # Servo Settings and Init
    frame_num = 0
    flag_up = False
    capture = True  # Determines if a frame should be saved based on fps
    timer_start = time.time()
    last_flag_move = time.time()  # records the seconds since the flag has been moved (via keyboard)

    try:
        cap1 = cv2.VideoCapture(0)
    except ConnectionError:
        print('ERROR: Unable to establish VideoCapture Camera 1!')

    print("Startup Complete...")
    print("Initialized in " + mode[active_mode] + " MODE...")
    # changes directory to dataFrames folder
    try:
        os.chdir(usb_root)
    except OSError:
        print('no SamsungUSB found, using currency working directory...')

    if os.path.exists('dataFrames'):
        os.chdir('dataFrames')
    else:
        os.mkdir('dataFrames')
        print('Creating dataFrames directory...')
        dataframes_root = os.getcwd()

    if os.path.exists('camera1'):
        os.mkdir('camera1')
        print('Creating camera1 directory...')
    else:
        print('Using existing camera1 directory...')
    session_num1 = len(os.listdir('camera1')) + 1
    session_path = f'camera1/session_{session_num1}'

    if not os.path.exists(session_path):
        os.mkdir(session_path)
    else:
        print(f'Unable to create new session directory directory: {os.path.abspath(session_path)}')

    print('Lowering Flag for Initialization')
    operation_light.on()
    water_ski_light.on()
    wake_board_light.on()
    tube_light.on()
    kit.servo[0].angle = servo_angle
    time.sleep(10)
    print('Flag Lowered...')
    water_ski_light.off()
    wake_board_light.off()
    tube_light.off()
    print('Starting Data Collection...')
    print(f'Beginning session #{session_num1} for Camera 1...')

    while cap1.isOpened():
        ret1, frame1 = cap1.read()
        if not ret1:
            break

        if flag_up:
            flag_pos = 'FlagUp'
        else:
            flag_pos = 'FlagDown'

        if capture:
            os.chdir(os.path.join(session_path, session_num1))
            cv2.imwrite(f'camera1_{mode[active_mode]}_{flag_pos}_frame_{frame_num}_session_{session_num1}_{fps}fps.jpeg',
                        frame1)
            os.chdir(dataframes_root)
            frame_num += 1
            capture = False

        cv2.waitKey(10)
        if time.time() - last_flag_move < 1:  # Prevents input being entered too frequently
            command_halt = True
        else:
            command_halt = False

        if not command_halt:
            if keyboard.is_pressed('q') and (not flag_up):
                flag_up = True
                last_flag_move = time.time()
                print('Raising Flag...')
                command_halt = True
                while servo_angle > 0:
                    servo_angle = servo_angle - 5
                    time.sleep(0.05)
                    kit.servo[0].angle = servo_angle
                servo_angle = 0
                print('Flag Raised...')
            elif keyboard.is_pressed('q') and flag_up:
                flag_up = False
                last_flag_move = time.time()
                print('Lowering Flag...')
                command_halt = True
                while servo_angle < 125:
                    servo_angle = servo_angle + 5
                    time.sleep(0.05)
                    kit.servo[0].angle = servo_angle
                servo_angle = 125
                print('Flag Lowered...')

        # MODE CHANGES
        if keyboard.is_pressed('p'):
            if active_mode == 0:
                print("Already in PASSIVE MODE...")
            else:
                try:
                    print("Changing to PASSIVE MODE...")
                    active_mode = 0
                except RecursionError:
                    print("Error: Unable to Change mode to PASSIVE...")

        if keyboard.is_pressed('s'):
            if active_mode == 1:
                print("Already in WATERSKI MODE...")
            else:
                try:
                    print("Changing to WATERSKI MODE...")
                    active_mode = 1
                except RecursionError:
                    print("Error: Unable to Change mode to WATERSKI...")

        if keyboard.is_pressed('w'):
            if active_mode == 2:
                print("Already in WAKEBOARD MODE...")
            else:
                try:
                    print("Changing to WAKEBOARD MODE...")
                    active_mode = 2
                except RecursionError:
                    print("Error: Unable to Change mode to WAKEBOARD...")

        if keyboard.is_pressed('t'):
            if active_mode == 3:
                print("Already in TUBING MODE...")
            else:
                try:
                    print("Changing to TUBING MODE...")
                    active_mode = 3
                except RecursionError:
                    print("Error: Unable to Change mode to TUBING...")
        if keyboard.is_pressed('m'):
            if active_mode == 4:
                pass
            else:
                try:
                    print("Changing to NEWSESSION MODE...")
                    active_mode = 4
                    time.sleep(1)
                except RecursionError:
                    print("Error: Unable to Change mode to NEWSESSION...")
        # END OF MODE CHANGE
        if active_mode == 0:
            operation_light.on()
            water_ski_light.off()
            wake_board_light.off()
            tube_light.off()
        elif active_mode == 1:
            operation_light.on()
            water_ski_light.on()
            wake_board_light.off()
            tube_light.off()
        elif active_mode == 2:
            operation_light.on()
            water_ski_light.off()
            wake_board_light.on()
            tube_light.off()
        elif active_mode == 3:
            operation_light.on()
            water_ski_light.off()
            wake_board_light.off()
            tube_light.on()
        else:
            operation_light.on()
            water_ski_light.on()
            wake_board_light.on()
            tube_light.on()

        if keyboard.is_pressed('m') and active_mode == 4 and debug_mode:
            print('Ending session...')
            try:
                frame_total = len(os.listdir(session_path))
                print(f'Saved {frame_total} frames to session_{session_num1}')
                print('Session Ended...')
            except RecursionError:
                pass
            break

        if keyboard.is_pressed('m') and active_mode == 4 and (not debug_mode):
            try:
                frame_total = len(os.listdir(session_path))
                print(f'Saved {frame_total} frames to session_{session_num1}')
                print('Starting new session...')
                session_num1 = len(os.listdir('camera1')) + 1
                os.mkdir(f'camera1/session_{session_num1}')
                active_mode = 0
                dir_len = (os.listdir('camera1'))
                print(f'Session {dir_len} has begun...')
                print('mode changed to PASSIVE...')
            except OSError:
                print('Error starting new session...')

        if (time.time() - timer_start) * fps > frame_num:
            capture = True

    cap1.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
