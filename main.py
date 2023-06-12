"""This module's purpose is to run a modified rubberband turret found
here: https://www.thingiverse.com/thing:953753,the only modified part
is the addition of a picamera on the y-axis of the barrel.
"""

__version__ = '1.02'
__author__ = 'Fvern Witherial'

import RPi.GPIO as GPIO  # To control GPIO inputs and outputs.
import time  # To get the date or time, and to halt the program.
import cv2  # For camera functionality.
import os  # For manipulating the operating system.
import pigpio  # To control servos more smoothly.
import smtplib as smtp  # For emailing
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
# For formatting emails, email message, and email images.

import logger
import config
from objectDetectionModule import ObjectDetector
# Imports the local logging module for additional logging features.
# Imports the config file which is just user set variables.
# Allows for object detection.


# Imports all the necessary modules used for noted reasons.

# DEBUG: Detailed information, typically for diagnosing problems.
# INFO: Conformation that all is operating normally.
# WARNING: Indication that something unexpected happened.
# ERROR: A more serious problem that halts some form of function.
# CRITICAL: A serious error indicating program instability.
# log.*level* will be used to log what's occurring within the program.

class TimedBool:
    """Creates a boolean value that is toggled on/off after the inputted
    time passes.
    
    :param init_val: The default value of the boolean, defaults to
        `True`
    :type init_val: bool, optional
    :param logger: An optional logger addon to log switches, defaults
        to None
    :type logger: class`logging.logger`, optional
    """

    def __init__(self,
                 init_val: bool = False,
                 logger=None):
        """Constructs the timed boolean, setting the variables later
        needed.
        """

        self.val = init_val
        self.switch_time = 0
        self.time_switched = 0
        self.logger = logger
        if self.logger is not None:
            self.logger.debug(f' TimedBool initiated.')

    def __call__(self):
        """Changes what happens when the TimedBool is directly called
        upon to firstly check if the time passed through has passed,
        if no switch time set by return the default value, then return
        the current value.
        
        :return: The default state if no time set or time set has
            passed, and the opposite bool value if time set has not
            passed
        :rtype: bool
        """

        if self.switch_time == 0:
            return self.val
        # Returns the default value if the switch_time has the 

        time_passed = int(time.time()) - self.switch_time
        if time_passed > self.time_switched:
            self.switch_time = 0
            self.time_switched = 0
            self.val = not self.val
            if self.logger is not None:
                self.logger.info(' A timed bool has switched '
                                 f'back to {self.val}.')
        return self.val

    def switch_for(self, time_switched: int = 5):
        """Sets the time for how long the TimedBool's value will be
        switched.
        
        :param time_switched: The amount of seconds needed to pass
            before returning to the default state, defaults to 5
        :type time_switched: int, optional
        """

        self.switch_time = int(time.time())
        self.time_switched = time_switched
        self.val = not self.val
        if self.logger is not None:
            self.logger.info(f' A timed bool has switched to {self.val} '
                             f'for {self.time_switched / 60} minutes.')


class PWMGpio:
    """Allows for cleaner manipulation of PWM with pigpio, and
    optional logging functionality.

    :param pwm: An initialised pigpio class to send commands to
    :type pwm: class`pigpio.pi`
    :param pin: The gpio number of the pin based on broadcom SOC
        channel
    :type pin: int
    :param freq: The frequency (in Hz) of the pulse width modulation
        on the GPIO pin
    :type freq: int
    :param logger: An optional logger addon to log switches, defaults
        to None
    :type logger: class`logging.logger`, optional
    """

    def __init__(self,
                 pwm,
                 pin: int,
                 freq: int,
                 logger=None):
        """Constructs the class"""
        self.pin = pin
        self.freq = freq
        self.logger = logger
        self.pwm = pwm
        self.pwm.set_mode(self.pin, pigpio.OUTPUT)
        self.pwm.set_PWM_frequency(self.pin, self.freq)
        if self.logger is not None:
            self.logger.info(f' GPIO PIN {self.pin} setup for PWM, '
                             'at {self.freq}Hz.')

    def set_servo_pw(self, pulsewidth: int, sleep_time: float = 0.5):
        """Sets the pulsewidth of the pin for servo use.

        :param pulsewidth: The pulsewidth to be transmitted to the
            servo
        :type pulsewidth: int
        :param sleep_time: The sleep time after setting pulsewidth,
            defaults to 0.5
        :type sleep_time: float, optional
        """
        self.pwm.set_servo_pulsewidth(self.pin, pulsewidth)
        if self.logger is not None:
            self.logger.info(f' GPIO PIN {self.pin} pulsewidth set as {pulsewidth}.')
        time.sleep(sleep_time)


def gpio_pin_setup(
        pin: int, in_out: classmethod,
        pud: classmethod = None, start_state: bool = False,
        logger=None):
    """Sets up a GPIO pin by automatically setting out to false
    and including the logger module.

    :return: Method
    """

    def log_message(mesg, logger=logger):
        """Helps clean up the code of if statements for better
        readability.
        """
        if logger is not None:
            logger.info(mesg)

    if in_out == 0:
        GPIO.setup(pin, in_out)
        log_message(f' GPIO PIN {pin} setup as OUT.')
        GPIO.output(pin, start_state)
        log_message(f' GPIO PIN {pin} output set as {start_state}.')
    else:
        GPIO.setup(pin, in_out, pull_up_down=pud)
        log_message(
            f' GPIO PIN {pin} setup '
            f'as IN and PUD {"DOWN" if pud == 21 else "UP"}.'
        )


def send_email(email_address: str, email_password: str, email_receiver: str,
               subject: str, body: str, image_path: str = None,
               domain: str = 'smtp.gmail.com', port: int = 465,
               logger=None):
    """Helps compose an email to be sent with an option image addon.
    
    :param email_address: The sender email address
    :type email_address: str
    :param email_password: The password (or app password) of the
        sender email address
    :type email_password: str
    :param email_receiver: The email address that the email will be
        sent to
    :type email_receiver: str
    :param subject: The text subject header of the email to be sent
    :type subject: str
    :param body: The text body of the email to be sent
    :type body: str
    :param image_path: The path to an optional image that'll be
        added as an attachment within the email, defaults to None
    :type image_path: str, optional
    :param domain: The domain of the smtp server, defaults to
        `smtp.gmail.com`
    :type domain: str, optional
    :param port: The port of the smtp server, defaults to 465
    :type port: int, optional
    :param logger: An optional logger addon to log switches, defaults
        to None
    :type logger: class`logging.logger`, optional
    """

    if logger is not None:
        logger.debug(f' Composing email to {email_receiver} from '
                     '{email_address} of:\n{subject}\n{body}.')
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = email_address
    msg['To'] = email_receiver

    msg.attach(MIMEText(body))
    if image_path is not None:
        with open(image_path, 'rb') as infile:
            image_data = infile.read()
        msg.attach(MIMEImage(image_data, name=os.path.basename(image_path)))
        if logger is not None:
            logger.debug(f' Attaching image to email.')

    with smtp.SMTP_SSL(domain, port) as connection:
        connection.login(email_address, email_password)
        connection.sendmail(from_addr=email_address, to_addrs=email_receiver,
                            msg=msg.as_string())
    if logger is not None:
        logger.debug(f' Email sent.')


def temp_folder_cleaner(extension: str, folder: str, max_items: int = 20):
    """Checks a folder to ensure that it doesn't become overloaded
    with files of a certain extension by deleting the older files over
    the max_items variable.
    
    :param extension: The extension of the files needed to be kept in
        check done like this to avoid the accidental deletions of
        misplaced files
    :type extension: str
    :param folder: The path to the folder to be kept in check
    :type folder: str
    :param max_items: The maximum amount of files of the extension
        allowed within the folder hen scanned, defaults to 20
    :type max_items: int, optional
    """

    folder_dir = os.listdir(folder)
    items_in_dir = []
    for i in folder_dir:
        if extension in i:
            items_in_dir.append(i)
    if len(items_in_dir) > max_items:
        items_timed = {}
        for i in items_in_dir:
            items_timed[i] = os.path.getmtime(f'{folder}/{i}')
        for i in range(len(items_in_dir) - max_items):
            oldest_item = min(items_timed, key=items_timed.get)
            os.remove(
                f'{folder}/{oldest_item}')
            del items_timed[oldest_item]


def main():
    """Starts the turret security system."""
    log = logger.init_outfile_logging(log_name=__name__)
    log.debug(' Logging initiated.')
    # Creates and initialises the custom logger
    # passing through this program's identity.

    if not os.path.exists(config.capture_folder):
        os.mkdir(config.capture_folder)
    # Ensures that the capture folder, used for storing images, is
    # present.

    img_w = 640
    img_h = 480
    # The pixel measurements of the width and height of the capture.

    GPIO.setmode(GPIO.BOARD)
    log.info(' mode set as board.')
    GPIO.setwarnings(False)
    log.debug(' GPIO.setwarnings set as False.')
    # Sets the mode to board, which refers to the pin, then allows the
    # program can run if previous pins have been active but not
    # deactivated.

    pwm = pigpio.pi()
    # Creates and initialises pigpio which is used for Pulse Width
    # Modulation.

    gpio_pin_setup(22, GPIO.IN, GPIO.PUD_DOWN, logger=log)
    gpio_pin_setup(18, GPIO.IN, GPIO.PUD_DOWN, logger=log)
    # Sets up the following pins to be later used. GPIO.IN means
    # they'll be input pins and GPIO.PUD_DOWN to steer the inputs
    # to a known state.

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
    # pigpio is used here as it taps into the rpi's hardware clock
    # pigpio uses BCM instead of BOARD numbering
    # 1500 should be the servo centre, and 0 stops it

    xpulsewidth = 1500
    ypulsewidth = 2100
    fpulsewidth = 1520
    # The starting pulse width of the servos.

    x_servo = PWMGpio(pwm, 18, 50, logger=log)
    x_servo.set_servo_pw(xpulsewidth)
    # pigpio registers pin 12 as 18
    # 500-2500 == 180
    # 750-2250 recommended
    y_servo = PWMGpio(pwm, 27, 50, logger=log)
    y_servo.set_servo_pw(ypulsewidth)
    # pigpio registers pin 13 as 27
    # 1750-2250 recommended
    f_servo = PWMGpio(pwm, 17, 50, logger=log)
    # pigpio registers pin 11 as 17
    # 500-1480 == clockwise, 1500-2500 == counter-clockwise
    # clockwise: higher == slower, counter: lower = slower
    # 1520 recommended

    cap = cv2.VideoCapture(config.camera_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, img_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, img_h)
    # Sets the camera up for opencv, limits the camera resolution for
    # resource usage.

    detector = ObjectDetector()
    detector_scan_step = 5
    lm_dict = {}
    # Initiates the object detection module. Sets when the detector
    # will scan the image, for better resource usage, and sets
    # lm_dict to empty.

    entity_in_xrange = False
    entity_in_yrange = False
    # Used later to check when to shoot.

    y_height_bias = 140
    # The leeways set how large will be the target centre box in
    # pixels (*2). The y_height_bias will move the target box up
    # to accommodate for projectile drop. Could be dynamically set
    # but found it was a slight too taxing.

    y_leeway = 25
    y_margins = {
        'up': int((img_h / 2)
                  - y_leeway
                  + y_height_bias),
        'down': int((img_h / 2)
                    + y_leeway
                    + y_height_bias
                    - 1)
    }
    # Stores the y margins calculated by getting the centre point of
    # the image, and then applying the leeway.
    # This is up here to save up on calculation resources.

    xpw_jumps = 50
    ypw_jumps = 20
    # This will be used to +/- the pulse width to move it left/right
    # up/down larger jumps mean less accurate but faster to aim,
    # smaller the opposite. Could be dynamically set but found it
    # was a slight too taxing.

    counter, fps = 0, 0
    start_time = time.time()
    row_size = 20  # pixels
    left_margin = 24  # pixels
    text_color = (0, 0, 255)  # red
    font_size = 1
    font_thickness = 1
    fps_avg_frame_count = 10
    # Variables for setting up the fps view in opencv.imshow
    # practically useless when finished debugging.

    bool_switch_time = 5 * 60
    human_multiplier = 2
    # Variables for controlling how long the timedbools should last,
    # the human_multiplier is to increase time due to higher proof of
    # a break in.

    door_opened = TimedBool(logger=log)
    motion_detected = TimedBool(logger=log)
    human_detected = TimedBool(logger=log)
    # Used to only allow an incident to occur again after a certain
    # amount of time passes. Log is passed through as logger to allow
    # for logging.

    try:
        # If an exception occurs the program will execute the
        # exception code and continue out of the try loop.
        while True:
            # Causes the code to indefinitely loop.

            success, img = cap.read()
            if not success:
                raise RuntimeError(
                    'Unable to read from webcam.'
                    'Please verify your webcam in config.py.'
                )
            # Stores if the camera was successfully accessed and the
            # current visual feed of the camera. If the camera
            # couldn't be accessed it will cause a RuntimeError and
            # the program would stop.

            img = cv2.flip(img, -1)
            if counter % detector_scan_step == 0:
                img = detector.find_object(img)
                lm_dict = detector.find_position()
            # Firstly flips the image both horizontally and
            # vertically, then checks if the counter is a multiple of
            # detector_scan_step and if so detect the image for
            # objects and return objects.

            counter += 1
            # A counter for both fps and detection calculations.

            if (GPIO.input(22) == 0
                    and door_opened() is False):
                # A door opening has been detected, now on alert for
                # additional triggers, to prevent false alarms.
                # A timer has now been set till this trigger is
                # deactivated.

                door_opened.switch_for(bool_switch_time)
                # Sets door_opened to true for bool_switch_time seconds.

                ctime = time.strftime('%b %d %Y %H:%M:%S')
                # Gets the current time in
                # 'Month Date Year Hour:Minute:Second' format.

                time.sleep(3)
                # Lets the entity get more in frame before the image is taken

                img_file_name = (
                    'door-opened-'
                    f'{ctime.replace(" ", "-").replace(":", "")}'
                    '.png'
                )
                temp_folder_cleaner('.png', config.capture_folder)
                cv2.imwrite(f'{config.capture_folder}/{img_file_name}', img)
                # Sets the output file's name then calls
                # temp_folder_cleaner to ensure the folder is not
                # being overloaded then writes the image to the folder.

                subject = 'Security Alert: Door Opened'
                body = (
                    f'ALERT: A door opening has been detected on {ctime}.\n'
                    'Please see the image attached.'
                )
                send_email(
                    email_address=config.email_addr,
                    email_password=config.email_passwd,
                    email_receiver=config.email_receiver,
                    subject=subject,
                    body=body,
                    image_path=f'{config.capture_folder}/{img_file_name}',
                    logger=log
                )
                log.info(
                    f' Door opening detected on {ctime}'
                    ', trigger will be active for '
                    f'{bool_switch_time / 60} minutes.'
                )
                # Sets the subject and body of the email and then
                # passes it through to the send_email function with
                # the image's path and the email account's credentials
                # to send.

            if (GPIO.input(18) == 1
                    and motion_detected() is False):
                # Motion detected, now on alert for additional
                # triggers, to prevent false alarms.
                # A timer has now been set till this trigger is
                # deactivated.

                motion_detected.switch_for(bool_switch_time)
                # Sets motion_detected to true for bool_switch_time
                # seconds.

                ctime = time.strftime('%b %d %Y %H:%M:%S')
                # Gets the current time in
                # 'Month Date Year Hour:Minute:Second' format.

                time.stop(3)
                # Lets the entity get more in frame before the image is taken

                img_file_name = (
                    'motion-detected-'
                    f'{ctime.replace(" ", "-").replace(":", "")}'
                    '.png'
                )
                temp_folder_cleaner('.png', config.capture_folder)
                cv2.imwrite(f'{config.capture_folder}/{img_file_name}', img)
                # Sets the output file's name then calls
                # temp_folder_cleaner to ensure the folder is not
                # being overloaded then writes the image to the folder.

                subject = 'Security Alert: Motion Detected'
                body = (
                    f'ALERT: Motion has been detected on {ctime}.\n'
                    'Please see the image attached.'
                )
                send_email(
                    email_address=config.email_addr,
                    email_password=config.email_passwd,
                    email_receiver=config.email_receiver,
                    subject=subject,
                    body=body,
                    image_path=f'{config.capture_folder}/{img_file_name}',
                    logger=log
                )
                log.info(
                    f' Motion detected on {ctime}'
                    ', trigger will be active for '
                    f'{bool_switch_time / 60} minutes.'
                )
                # Sets the subject and body of the email and then
                # passes it through to the send_email function with
                # the image's path and the email account's credentials
                # to send.

            if ('person' in lm_dict
                    and human_detected() is False):
                # A human has been detected, now on alert for
                # additional triggers, to prevent false alarms.
                # An extended timer has now been set till this trigger
                # is deactivated.

                human_detected.switch_for(
                    bool_switch_time
                    * human_multiplier
                )
                # Sets human_detected to true for
                # bool_switch_time * human_multiplier seconds.

                ctime = time.strftime('%b %d %Y %H:%M:%S')
                # Gets the current time in
                # 'Month Date Year Hour:Minute:Second' format.

                img_file_name = (
                    'person-detected-'
                    f'{ctime.replace(" ", "-").replace(":", "")}'
                    '.png'
                )
                temp_folder_cleaner('.png', config.capture_folder)
                cv2.imwrite(f'{config.capture_folder}/{img_file_name}', img)
                # Sets the output file's name then calls
                # temp_folder_cleaner to ensure the folder is not
                # being overloaded then writes the image to the folder.

                subject = 'Security Alert: Human Detected'
                body = (
                    'SEVERE ALERT: A humanoid figure has been detected.\n'
                    f'The figure was detected on {ctime}.\n'
                    'Please see the image attached.'
                )
                send_email(
                    email_address=config.email_addr,
                    email_password=config.email_passwd,
                    email_receiver=config.email_receiver,
                    subject=subject,
                    body=body,
                    image_path=f'{config.capture_folder}/{img_file_name}',
                    logger=log
                )
                log.info(
                    ' Humanoid figure detected on '
                    f'{ctime}, trigger will be active for '
                    f'{bool_switch_time * human_multiplier / 60}'
                    ' minutes.'
                )
                # Sets the subject and body of the email and then
                # passes it through to the send_email function with
                # the image's path and the email account's credentials
                # to send.

            if ('person' in lm_dict
                    and counter % detector_scan_step == 0
                    and config.turret_active):
                # lm_dict['person'][0] should always have a centre
                # point. Now targeting the centre point, if the turret
                # not disabled and if a scan has occurred.
                log.info(
                    'Targeting'
                    f'X: {lm_dict["person"]["centre_x"]} '
                    f'Y: {lm_dict["person"]["centre_y"]}'
                )

                x_leeway = lm_dict['person']['width'] / 2
                x_margins = {
                    'left': int(
                        (img_w / 2)
                        - x_leeway
                    ),
                    'right': int(
                        (img_w / 2)
                        + x_leeway
                        + 1
                    )
                }
                # Stores the x margins calculated by getting the centre
                # point of the image, and then applying the leeways.

                x_in_range = range(x_margins['left'], x_margins['right'])
                y_in_range = range(y_margins['up'], y_margins['down'])
                # The ranges are used to create an area where the
                # turret will stop trying to centre its target.

                x_out_range = {
                    'left': range(-1, x_margins['left']),
                    'right': range(x_margins['right'], img_w + 1)
                }
                y_out_range = {
                    'up': range(-1, y_margins['up']),
                    'down': range(y_margins['down'], img_h + 1)
                }
                # Used to find where the target is and what side is
                # it more to for later aiming.

                target_pos = {
                    'x': lm_dict['person']['centre_x'],
                    'y': lm_dict['person']['centre_y']
                }
                # Gets the centre point of the target.

                if target_pos['x'] not in x_in_range:
                    # Checks if the target x position is not within the
                    # turret's crosshair, if not set entity_in_xrange
                    # to True.

                    entity_in_xrange = False
                    # Target not in x range makes sure not to shoot.

                    if target_pos['x'] in x_out_range['left']:
                        log.debug(' Under the range moving into range.')
                        xpulsewidth += xpw_jumps
                        x_servo.set_servo_pw(xpulsewidth)
                    elif target_pos['x'] in x_out_range['right']:
                        log.debug(' Over the range moving into range.')
                        xpulsewidth -= xpw_jumps
                        x_servo.set_servo_pw(xpulsewidth)
                    # Checks if the target is out of range towards the
                    # left or right and inch towards the target, by
                    # increasing or reducing the xpulsewidth.
                else:
                    entity_in_xrange = True

                if target_pos['y'] not in y_in_range:
                    # Checks if the target y position is not within the
                    # turret's crosshair, if not set entity_in_xrange
                    # to True.

                    entity_in_yrange = False
                    # Target not in y range makes sure not to shoot.

                    if target_pos['y'] in y_out_range['up']:
                        log.debug(' Under the range moving into range.')
                        ypulsewidth += ypw_jumps
                        y_servo.set_servo_pw(ypulsewidth)
                    elif target_pos['y'] in y_out_range['down']:
                        log.debug(' Over the range moving into range.')
                        ypulsewidth -= ypw_jumps
                        y_servo.set_servo_pw(ypulsewidth)
                    # Checks if the target is out of range being too up
                    # or too down and inch towards the target, by
                    # increasing or reducing the ypulsewidth.
                else:
                    entity_in_yrange = True

                # clockwise == right/down == 500-1500
                # anti == left/up == 1500-2500

            if (config.turret_active
                    and entity_in_xrange
                    and entity_in_yrange
                    and (door_opened()
                         or motion_detected())):
                # Checks if the turret is centred and if the turret
                # is not disabled and if so shoot, else stop.
                f_servo.set_servo_pw(fpulsewidth)
            else:
                f_servo.set_servo_pw(0)

            if counter % fps_avg_frame_count == 0:
                end_time = time.time()
                fps = fps_avg_frame_count / (end_time - start_time)
                start_time = time.time()
            # Calculates the fps by seeing how much time has passes
            # since the previous fps_avg_frame_count (10) frames,
            # while resetting the start time.

            text_location = (left_margin, row_size)
            cv2.putText(
                img, f'FPS = {fps}',
                text_location, cv2.FONT_HERSHEY_PLAIN,
                font_size, text_color,
                font_thickness
            )
            # Adds a small fps counter found within the image

            cv2.imshow('Camera', img)
            cv2.waitKey(1)
            # Shows the image output and waits 1 millisecond for
            # input to prevent running the thread infinitely for
            # keyboard inputs.
    except KeyboardInterrupt:
        # When the program is stopped, by ctrl+c it will execute the
        # commands below to stop the servos, reset all GPIO pins, and
        # log the exit.
        pwm.stop()
        GPIO.cleanup()
        log.exception(' Closing program due to keyboard interrupt.')


if __name__ == "__main__":
    # More for formality but also allows functions
    # used to be used in other projects.
    main()
