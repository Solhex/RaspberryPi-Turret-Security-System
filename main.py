"""This module's purpose is to run a modified rubberband turret found
here: https://www.thingiverse.com/thing:953753,the only modified part
is the addition of a picamera on the y-axis of the barrel.
"""

__version__ = '0.32'
__author__ = 'Fvern Witherial'

import RPi.GPIO as GPIO
import time
import sys
import os
import picamera
import cv2
import mediapipe as mp
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from subprocess import Popen
import logger
from poseDetectionModule import PoseDetector


# DEBUG: Detailed information, typically for diagnosing problems.
# INFO: Conformation that all is operating normally.
# WARNING: Indication that something unexpected happened.
# ERROR: A more serious problem that halts some form of function.
# CRITICAL: A serious error indicating program instability.


class TimedBool:
    def __init__(self, init_val: bool = False, logger=None):
        self.val = init_val
        self.switch_time = 0
        self.time_switched = 0

    def __call__(self):
        if self.switch_time == 0:
            return self.val

        time_passed = int(time.time()) - self.switch_time
        if time_passed > self.time_switched:
            self.switch_time = 0
            self.time_switched = 0
            self.val = not self.val
            if logger is not None:
                logger.info(f' ')
        return self.val

    def switch_for(self, time_switched: int = 5):
        self.switch_time = int(time.time())
        self.time_switched = time_switched
        self.val = not self.val


def gpio_pin_setup(
        pin: int, in_out: classmethod,
        pud: classmethod = None, start_state: bool = False,
        logger=None):
    """Sets up a GPIO pin by automatically setting out to false
    and including the logger module.

    :return: Method
    """

    log_message = []
    if in_out.__name__ != 'IN':
        GPIO.setup(pin, in_out)
        log_message.append(f' GPIO PIN {pin} setup as OUT.')
        GPIO.output(pin, start_state)
        log_message.append(f' GPIO PIN {pin} output'
                           'set as {start_state}.')
    else:
        GPIO.setup(pin, in_out, pull_up_down=pud)
        log_message.append(f' GPIO PIN {pin} setup'
                           'as IN and {pud.__name__}.')

    if logger is not None:
        for message in log_message:
            logger.info(message)


def gpio_pwm_setup(
        pin: int, freq: float,
        dc: float, logger=None):
    """Sets up a GPIO pin for PWM control with added logging output.

    :return: Method
    """

    log_message = []
    servo = GPIO.PWM(pin, freq)
    log_message.append(f' GPIO PIN {pin} setup for PWM, at {freq}Hz.')
    servo.start(dc)
    log_message.append(f' Started GPIO PIN {pin} at {dc}.')

    if logger is not None:
        for message in log_message:
            logger.info(message)

    return servo


def main():
    log = logger.init_outfile_logging(log_name=__name__)
    log.debug(' Logging initiated.')

    GPIO.setmode(GPIO.BOARD)
    log.info(' mode set as board.')
    GPIO.setwarnings(False)
    log.debug(' GPIO.setwarnings set as False.')

    gpio_pin_setup(11, GPIO.IN, GPIO.PUD_DOWN, logger=log)
    gpio_pin_setup(12, GPIO.IN, GPIO.PUD_DOWN, logger=log)
    gpio_pin_setup(16, GPIO.OUT, logger=log)
    gpio_pin_setup(18, GPIO.OUT, logger=log)
    gpio_pin_setup(22, GPIO.OUT, logger=log)

    # Servo controlling the y-axis max cycle 2.5 to 5
    # Servo controlling the x-axis max cycle 2.5 to 12.5
    # Servo controlling the firing speed

    # A typical servo responds to pulse widths in the range 1000 to
    # 2000 µs, typically pulse width of 1500 µs moves the servo to
    # angle 0. Each 10 µs increase in pulse width typically moves
    # the servo 1 degree more clockwise

    # Small 9g servos typically have an extended range and may respond
    # to pulse widths in the range 500 to 2500 µs
    # dutycycle = ((angle/180.0) + 1.0) * 5.0
    # RPi.GPIO ChangeDutyCycle method is not reliable.
    # It uses software timing which will cause servo glitches

    x_servo = gpio_pwm_setup(18, 50, 2.5, logger=log)
    # 2.5-12.5 180
    y_servo = gpio_pwm_setup(16, 50, 2.5, logger=log)
    # 2.5-5 180
    f_servo = gpio_pwm_setup(22, 50, 2.5, logger=log)
    # ? 360

    cap = cv2.VideoCapture(0)
    detector = PoseDetector()
    x_leeway = 20
    y_leeway = 20

    bool_switch_time = 5 * 60
    human_multiplier = 2

    past_time = 0

    door_opened = TimedBool()
    motion_detected = TimedBool()
    human_detected = TimedBool()

    try:
        while True:
            success, img = cap.read()
            img = detector.find_pose(img)
            lm_dict = detector.find_position()

            if GPIO.output(11) is True and door_opened() is False:
                door_opened.switch_time(bool_switch_time)
                log.info(' door opening detected, trigger will '
                         f'be active for {bool_switch_time/60} minutes')

            if GPIO.output(12) is True and motion_detected() is False:
                motion_detected.switch_time(bool_switch_time)
                log.info(' motion detected, trigger will '
                         f'be active for {bool_switch_time/60} minutes')

            if len(lm_dict) != 0 and human_detected() is False:
                human_detected.switch_time(bool_switch_time
                                           * human_multiplier)
                log.info(' humanoid figure detected, trigger will be'
                         'active for '
                         f'{bool_switch_time * human_multiplier / 60}'
                         ' minutes')

            if 12 in lm_dict.keys() and 11 in lm_dict.keys():
                print('Targeting X:'
                      f'{(lm_dict[12][0] + lm_dict[11][0]) / 2} '
                      f'Y:{(lm_dict[12][1] + lm_dict[11][1]) / 2}')
                img_h, img_w, img_c = img.shape
                x_range = range((img_h / 2) - x_leeway,
                                (img_h / 2) + x_leeway + 1)
                y_range = range((img_w / 2) - y_leeway,
                                (img_w / 2) + y_leeway + 1)
                x_target = (lm_dict[12][0] + lm_dict[11][0]) / 2
                y_target = (lm_dict[12][1] + lm_dict[11][1]) / 2

                while x_target not in x_range:
                    if x_target in range(0, (img_h / 2) - x_leeway):
                        log.debug(' Under the range')
                    elif x_target in range((img_h / 2) + x_leeway - 1,
                                           img_h + 1):
                        log.debug(' Over the range')

                while y_target not in y_range:
                    if y_target in range(0,
                                         (img_w / 2) - y_leeway):
                        log.debug(' Under the range')
                    elif x_target in range((img_w / 2) + y_leeway - 1,
                                           img_w + 1):
                        log.debug(' Over the range')

            for i in range(5):
                y_servo.ChangeDutyCycle(i)
                time.sleep(0.5)
            for i in range(5, 0, -1):
                y_servo.ChangeDutyCycle(i)
                time.sleep(0.5)

                current_time = time.time()
                fps = 1 / (current_time - past_time)
                past_time = current_time

                cv2.putText(img, str(int(fps)), (70, 50),
                            cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)
                cv2.imshow('Image', img)
                cv2.waitKey(1)
    except KeyboardInterrupt:
        y_servo.stop()
        GPIO.cleanup()
        log.exception(' Closing program due to keyboard interrupt.')


if __name__ == "__main__":
    main()
