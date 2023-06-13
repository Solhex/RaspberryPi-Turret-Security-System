"""This module's purpose is to create an easy to use object detector,
minimising the code needed to be used within other programs.
"""

import cv2
import time
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision
# imports the necessary code.


class ObjectDetector:
    def __init__(self,
                 model: str = './models/efficientdet_lite0.tflite',
                 size: tuple = (640, 480),
                 num_threads: int = 4,
                 max_results: int = 3,
                 score_threshold: float = 0.5):
        """Continuously run inference on images acquired from the camera.

        :param model: Path location of the TFLite object detection model.
        :type model: str, defaults to `./models/efficientdet_lite0.tflite`
            size: The width and height of the frame captured from the camera.
            num_threads: The number of CPU threads to run the model.
            draw_image: To show the capture with additional information.
        """

        self.model = model
        self.size = size
        self.num_threads = num_threads
        self.max_results = max_results
        self.score_threshold = score_threshold
        # Sets the variables for the class.

        base_options = core.BaseOptions(
            file_name=self.model,
            num_threads=self.num_threads
        )
        detection_options = processor.DetectionOptions(
            max_results=self.max_results,
            score_threshold=self.score_threshold
        )
        options = vision.ObjectDetectorOptions(
            base_options=base_options,
            detection_options=detection_options
        )
        # Sets the TFLite object model, and the CPU threads allocated.
        # Then sets the maximum amount of objects that can be detected, and
        # the score threshold for a object to be detected.
        # Then combines both options into a custom variable.

        self.detector = vision.ObjectDetector.create_from_options(options)
        # Initialises the detector from the object model.

    def find_object(self, img, draw=True):
        self.img = img
        # Allows other classes to access img.

        rgb_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        # Convert the image from BGR to RGB as required by the TFLite model.

        input_tensor = vision.TensorImage.create_from_array(rgb_img)
        # Create a TensorImage object from the RGB image.

        self.results = self.detector.detect(input_tensor)
        # Run object detection estimation using the model.

        if self.results.detections:
            # Checks if anything was detected.
            if draw:
                _MARGIN = 10  # pixels
                _ROW_SIZE = 10  # pixels
                _FONT_SIZE = 1
                _FONT_THICKNESS = 1
                _TEXT_COLOR = (0, 0, 255)  # red
                # Sets variables for adding the box surrounding detected
                # objects.

                for detection in self.results.detections:
                    # Draw bounding_box
                    bbox = detection.bounding_box
                    start_point = (
                        bbox.origin_x,
                        bbox.origin_y
                    )
                    end_point = (
                        bbox.origin_x + bbox.width,
                        bbox.origin_y + bbox.height
                    )
                    # Stores the dimensions of the box.

                    cv2.rectangle(
                        img, start_point,
                        end_point, _TEXT_COLOR,
                        3
                    )
                    # Adds the box surrounding the object.

                    category = detection.categories[0]
                    category_name = category.category_name
                    probability = round(category.score, 2)
                    result_text = f'{category_name} ({str(probability)}'
                    text_location = (
                        _MARGIN + bbox.origin_x,
                        _MARGIN + _ROW_SIZE + bbox.origin_y
                    )
                    # Draw label and score

                    cv2.putText(
                        img, result_text,
                        text_location, cv2.FONT_HERSHEY_PLAIN,
                        _FONT_SIZE, _TEXT_COLOR,
                        _FONT_THICKNESS
                    )

        return img

    def find_position(self):
        """Finds the position of the detected objects and returns a
        dictionary of relevant information.

        :return: A dictionary of points of objects detected
        :rtype: dict
        """

        lm_dict = {}
        if self.results.detections:
            # Checks if anything was detected.
            for obj_id, obj_info in enumerate(self.results.detections):
                obj_box = obj_info.bounding_box

                cx = int((obj_box.width/2)+obj_box.origin_x)
                cy = int((obj_box.height/2)+obj_box.origin_y)
                # Gets the centre points of the object.

                lm_dict[obj_info.categories[0].category_name] = {
                    'obj_id': obj_id,
                    'origin_x': obj_box.origin_x,
                    'origin_y': obj_box.origin_y,
                    'width': obj_box.width,
                    'height': obj_box.height,
                    'centre_x': cx,
                    'centre_y': cy
                }
                # Adds the category and its object id's positional
                # information.

        return lm_dict
        # Stops the function and returns what is lm_dict.


def main():
    """Starts some module tests, to check if this module works."""
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # Sets the camera up for opencv, limits the camera resolution for
    # resource usage.

    detector = ObjectDetector()
    # Initiates the object detection module.

    counter, fps = 0, 0
    start_time = time.time()
    row_size = 20  # pixels
    left_margin = 24  # pixels
    text_color = (0, 0, 255)  # red
    font_size = 1
    font_thickness = 1
    fps_avg_frame_count = 10
    # Variables for setting up the fps view in opencv.imshow.

    while cap.isOpened():
        # While the camera is being accessed the code within the while loop
        # will loop.

        success, img = cap.read()
        img = cv2.flip(img, -1)
        # Stores if the camera was successfully accessed and the current
        # visual feed of the camera.

        if counter % 12 == 0:
            img = detector.find_object(img)
            lm_dict = detector.find_position()
            # Checks if the counter is a multiple of 12 and
            # if so detect the image for objects and return objects.

        counter += 1
        # A counter for both fps and detection calculations.

        if counter % fps_avg_frame_count == 0:
            end_time = time.time()
            fps = fps_avg_frame_count / (end_time - start_time)
            start_time = time.time()
            # Calculates the fps by seeing how much time has passes since
            # the previous fps_avg_frame_count (10) frames, while resetting
            # the start time.

        fps_text = 'FPS = {:.1f}'.format(fps)
        text_location = (left_margin, row_size)
        cv2.putText(
            img, fps_text,
            text_location, cv2.FONT_HERSHEY_PLAIN,
            font_size, text_color,
            font_thickness
        )
        # Adds a small fps counter found within the image

        if 'person' in lm_dict:
            cv2.putText(
                img, 'O',
                (
                    lm_dict['person']['centre_x'] - 25,
                    lm_dict['person']['centre_y']
                ),
                cv2.FONT_HERSHEY_PLAIN,
                5, (255, 0, 0), 5)
            # Just places a blue O at the centre of a person

        cv2.imshow('Image', img)
        cv2.waitKey(1)
        # Shows the image output and waits 1 millisecond for input to
        # prevent running the thread infinitely for keyboard inputs.


if __name__ == '__main__':
    # Used to test the module and makes sure the test won't be performed when
    # importing this module.
    main()
