import cv2
import numpy as np
import pygame as pyg
from typing import Callable

import config as C


import pygame as pyg

class SelectCorners:
    monitor = 1

    def __init__(self, src_img):
        self.corners = []
        self.dragging = None

        pyg.init()

        img_height, img_width, _ = src_img.shape
        size = (img_width, img_height)

        pyg.display.set_caption('Wählen Sie die 4 Bildecken aus --- | Oben-Links -> Unten-Links |')
        self.screen = pyg.display.set_mode(size)

        src_img = cv2.cvtColor(src_img, cv2.COLOR_BGR2RGB)
        self.img = pyg.image.frombuffer(src_img.tostring(), src_img.shape[1::-1], "RGB")

    def is_cursor_on_point(self, pos: tuple[float, float], point: tuple[float, float]):
        """Check if the cursor is on the given point."""
        x, y = pos
        px, py = point
        return (px - 5 <= x <= px + 5) and (py - 5 <= y <= py + 5)

    def move_point(self, pos):
        """Move the point to the new position."""
        if self.dragging is not None:
            self.corners[self.dragging] = pos

    def draw_circle(self, x, y):
        pyg.draw.circle(self.screen, (0, 255, 0), (x, y), 5)
        pyg.display.update()

    def draw_lines(self):
        """Draw lines between the points."""
        if len(self.corners) >= 2:
            for i in range(len(self.corners) - 1):
                pyg.draw.line(self.screen, (0, 0, 255), self.corners[i], self.corners[i+1], 2)
            if len(self.corners) == 4:  # Connect the last point to the first point
                pyg.draw.line(self.screen, (0, 0, 255), self.corners[-1], self.corners[0], 2)

    def __call__(self) -> list[tuple[int, int], ]:
        self.screen.fill((255, 255, 255))
        self.screen.blit(self.img, self.img.get_rect())
        pyg.display.update()

        while True:
            for event in pyg.event.get():
                if event.type == pyg.QUIT:
                    raise Exception("Operation Interrupted")
                if event.type == pyg.MOUSEBUTTONDOWN:
                    for idx, point in enumerate(self.corners):
                        if self.is_cursor_on_point(event.pos, point):
                            self.dragging = idx
                            break
                if event.type == pyg.MOUSEBUTTONUP:
                    self.dragging = None
                    if len(self.corners) < 4 and not any([self.is_cursor_on_point(event.pos, point) for point in self.corners]):
                        self.draw_circle(*event.pos)
                        self.corners.append(event.pos)
                        self.draw_lines()

                if event.type == pyg.MOUSEMOTION and self.dragging is not None:
                    self.move_point(event.pos)
                    self.screen.fill((255, 255, 255))
                    self.screen.blit(self.img, self.img.get_rect())
                    self.draw_lines()  # Add this line
                    for point in self.corners:
                        self.draw_circle(*point)

                if event.type == pyg.KEYDOWN and event.key == pyg.K_RETURN:
                    if len(self.corners) == 4:
                        pyg.quit()
                        return self.corners

            pyg.display.update()


class Transformation:
    def __init__(self, transformation_matrix, region_of_interest, image_shape):
        self.transformation_matrix = transformation_matrix
        self.region_of_interest = region_of_interest
        self.image_shape = image_shape

    def transform_image(self, img):
        return cv2.warpPerspective(img, self.transformation_matrix, C.MONITOR_RESOLUTION)

    def transform_point(self, point):
        p = np.array([point[0], point[1], 1])
        m = self.transformation_matrix
        res = p * m
        return np.array([
            sum(res[0]) / sum(res[2]),
            sum(res[1]) / sum(res[2])
        ])

    def transform_relative(self, point):
        transformed_point = self.transform_point(point)
        return transformed_point / np.array(C.MONITOR_RESOLUTION)

    def get_data(self, point, img):
        return {
            'transformed_point': self.transform_point(point),
            'relative_position': self.transform_relative(point),
            'transformed_image': self.transform_image(img)
        }


class Calibration:
    def __init__(self, camera_sources):
        self.camera_sources = camera_sources

    def __call__(self):
        with self.camera_sources[0] as camera:
            img = camera()
        self.window = SelectCorners(img)
        self.coordinates = self.window()
        H = self._processing(self.coordinates)
        return H

    def _processing(self, coordinates) -> Transformation:
        camera_rect = coordinates
        screen_rect = [
            (0, 0),
            (C.MONITOR_RESOLUTION[0], 0),
            (C.MONITOR_RESOLUTION[0], C.MONITOR_RESOLUTION[1]),
            (0, C.MONITOR_RESOLUTION[1])
        ]

        P = []
        for (x, y), (x_, y_) in zip(camera_rect, screen_rect):
            P.extend(
                (
                    [-x, -y, -1, 0, 0, 0, x * x_, y * x_, x_],
                    [0, 0, 0, -x, -y, -1, x * y_, y * y_, y_],
                )
            )

        USV = np.linalg.svd(P)
        V = USV[2]
        h = V[-1]

        transformation_matrix = np.reshape(h, (3, 3))

        region_of_interest = lambda img: self.mask_image(
            img,
            self.coordinates,
            np.zeros((self.camera_sources[0].height, self.camera_sources[0].width), dtype="uint8"),
        )
        image_transformation_function = lambda img: cv2.warpPerspective(img, transformation_matrix, C.MONITOR_RESOLUTION)

        return Transformation(transformation_matrix, region_of_interest, (self.camera_sources[0].height, self.camera_sources[0].width))


    @staticmethod
    def point_transformation_function(point, transformation_matrix):
        p = np.array([
            point[0],
            point[1],
            1
        ])

        m = transformation_matrix
        res = p*m
        return np.array([
            sum(res[0]) / sum(res[2]),
            sum(res[1]) / sum(res[2])
        ])

    @staticmethod
    def mask_image(image, mask_points, _empty_mask):
        #mask = np.zeros(image.shape[:2], dtype="unit8")
        mask = _empty_mask

        #draw the poly on the mask
        polygon = np.array(mask_points, np.int32)
        polygon = polygon.reshape((-1, 1, 2))

        #apply mask
        cv2.fillPoly(mask, [polygon], (255, 255, 255))

        return cv2.bitwise_and(image, image, mask=mask)



#https://docs.opencv.org/4.x/dc/da5/tutorial_py_drawing_functions.html
#https://pyimagesearch.com/2021/01/19/image-masking-with-opencv/

#https://pyimagesearch.com/2015/03/09/capturing-mouse-click-events-with-python-and-opencv/
#https://www.pygame.org/docs/tut/PygameIntro.html
#https://stackoverflow.com/questions/19306211/opencv-cv2-image-to-pygame-image
#https://de.wikipedia.org/wiki/Liste_von_Transformationen_in_der_Mathematik
#https: // de.wikipedia.org / wiki / Drehmatrix
#https://forum.patagames.com/posts/t501-What-Is-Transformation-Matrix-and-How-to-Use-It
