import cv2
import mediapipe as mp
import time


class PoseDetector:
    def __init__(self,
                 static_image_mode=False,
                 model_complexity=1,
                 smooth_landmarks=True,
                 enable_segmentation=False,
                 smooth_segmentation=True,
                 min_detection_confidence=0.5,
                 min_tracking_confidence=0.5):
        self.mode = static_image_mode
        self.modelComplexity = model_complexity
        self.smoothLm = smooth_landmarks
        self.enableS = enable_segmentation
        self.smoothS = smooth_segmentation
        self.detectionCon = min_detection_confidence
        self.trackingCon = min_tracking_confidence

        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(self.mode, self.modelComplexity, self.smoothLm,
                                     self.enableS, self.smoothS, self.detectionCon,
                                     self.trackingCon)

    def find_pose(self, img, draw=True):
        self.img = img

        img_rgb = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(img_rgb)

        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(self.img, self.results.pose_landmarks, self.mpPose.POSE_CONNECTIONS)

        return img

    def find_position(self):
        lm_dict = {}
        if self.results.pose_landmarks:
            for identify, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = self.img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_dict[identify] = [cx, cy]

        return lm_dict


def main():
    cap = cv2.VideoCapture(0)
    past_time = 0
    detector = PoseDetector()

    while True:
        success, img = cap.read()
        img = detector.find_pose(img)
        lm_dict = detector.find_position()

        if 12 in lm_dict.keys() and 11 in lm_dict.keys():
            # print(lm_list)
            # print(lm_dict[12], lm_dict[11])
            print(f'Targeting X:{(lm_dict[12][0] + lm_dict[11][0]) / 2} Y:{(lm_dict[12][1] + lm_dict[11][1]) / 2}')
            # aim for the mean of 12 and 11

        current_time = time.time()
        fps = 1 / (current_time - past_time)
        past_time = current_time

        cv2.putText(img, str(int(fps)), (70, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

        cv2.imshow('Image', img)
        cv2.waitKey(1)


if __name__ == '__main__':
    main()
