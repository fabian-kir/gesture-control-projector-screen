import cv2
import mediapipe as mp

import cv2
import mediapipe as mp

import config as C

class HandDetector:
    def __init__(self, camera_res, transformation):
        self.camera_res = camera_res
        self.transformation = transformation
        self.debug = C.DEBUG
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands()
        self.mp_draw = mp.solutions.drawing_utils  # For drawing landmarks

    def __call__(self, image):
        # Convert the BGR image to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Process the image and get the results
        results = self.hands.process(rgb_image)

        # If no hands are detected, return False
        if not results.multi_hand_landmarks:
            return [None, None]

        # Initialize fingertip coordinates for left and right hands
        left_hand_tip = None
        right_hand_tip = None

        for index, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # Check if the hand is left or right
            hand_type = results.multi_handedness[index].classification[0].label

            # Get the tip of the middle finger
            middle_finger_tip = hand_landmarks.landmark[
                self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP
            ]
            tip_coordinates = (
                int(abs(middle_finger_tip.x * self.camera_res[0])),
                int(abs(middle_finger_tip.y * self.camera_res[1]))
            )

            # Transform the tip coordinates using the provided transformation
            transformed_tip = self.transformation.transform_point(tip_coordinates)

            if hand_type == "Right":
                right_hand_tip = transformed_tip
            else:
                left_hand_tip = transformed_tip

            # If debugging is enabled, draw the landmarks and hand type on the image
            if self.debug:
                self.mp_draw.draw_landmarks(image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                cv2.putText(image, hand_type, (tip_coordinates[0], tip_coordinates[1] - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # If debugging is enabled, show the image with the landmarks
        if self.debug:
            cv2.imshow("Hand Detection", image)
            cv2.waitKey(1)  # Display the window for a short duration

        return (left_hand_tip, right_hand_tip)


# Example usage:
# transformation = YourTransformationClass()
# detector = HandDetector((640, 480), transformation, debug=True)
# image = cv2.imread("path_to_image.jpg")
# result = detector(image)
# print(result)