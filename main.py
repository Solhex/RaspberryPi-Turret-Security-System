# import RPi.GPIO as GPIO
import time
import sys
import os
import picamera
import cv2
import mediapipe as mp
# import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from subprocess import Popen
from logger import init_logging
from poseDetectionModule import PoseDetector

# DEBUG: Detailed information, typically for diagnosing problems.
# INFO: Conformation that all is operating normally.
# WARNING: Indication that something unexpected happened.
# ERROR: A more serious problem that halts some form of function.
# CRITICAL: A serious error indicating program instability.

log = init_logging(log_name=__name__)
log.debug(' Logging initiated.')

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
log.debug(' GPIO PIN 11 setup as IN and PUD_DOWN.')
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
log.debug(' GPIO PIN 12 setup as IN and PUD_DOWN.')

GPIO.setup(16, GPIO.OUT)
log.debug(' GPIO PIN 16 setup as OUT.')
GPIO.output(16, False)
log.debug(' GPIO PIN 22 output set as False.')

GPIO.setup(18, GPIO.OUT)
log.debug(' GPIO PIN 18 setup as OUT.')
GPIO.output(18, False)
log.debug(' GPIO PIN 22 output set as False.')

GPIO.setup(22, GPIO.OUT)
log.debug(' GPIO PIN 22 setup as OUT.')
GPIO.output(22, False)
log.debug(' GPIO PIN 22 output set as False.')

x_servo = GPIO.PWM(16, 50)
x_servo.start(2.5)
# 2.5-12.5 180

y_servo = GPIO.PWM(18, 50)
y_servo.start(2.5)
# 2.5-5 180

f_servo = GPIO.PWM(22, 50)
f_servo.start(2.5)
# ? 360

cap = cv2.VideoCapture(0)
past_time = 0
detector = PoseDetector()

try:
    while True:
        success, img = cap.read()
        img = detector.find_pose(img)
        lm_dict = detector.find_position()

        for i in range(5):
            y_servo.ChangeDutyCycle(i)
            time.sleep(0.5)
        for i in range(5, 0, -1):
            y_servo.ChangeDutyCycle(i)
            time.sleep(0.5)

            current_time = time.time()
            fps = 1 / (current_time - past_time)
            past_time = current_time

            cv2.putText(img, str(int(fps)), (70, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

            cv2.imshow('Image', img)
            cv2.waitKey(1)
except KeyboardInterrupt:
    y_servo.stop()
    GPIO.cleanup()
    log.exception(' Closing program due to keyboard interrupt.')