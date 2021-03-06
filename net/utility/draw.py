import numpy as np
import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt
import cv2
import os
import net.utility.file as file
from config import cfg
import net.processing.boxes3d as box3d


file.makedirs(cfg.LOG_DIR)

def imshow(name, image, resize=1):
    H,W,_ = image.shape
    cv2.namedWindow(name, cv2.WINDOW_NORMAL)
    cv2.imshow(name, image.astype(np.uint8))
    cv2.resizeWindow(name, round(resize*W), round(resize*H))


def normalise(image, limit=255.0):
    image -= image.min()
    image *= (limit/image.max())
    return image

def imsave(name, image,subdir=''):
    dir=os.path.join(cfg.LOG_DIR,subdir)
    os.makedirs(dir,exist_ok=True)
    plt.imsave(os.path.join(dir,name)+'.png' ,image)

def npsave(name,numpy_array):
    np.save(os.path.join(cfg.LOG_DIR,name),numpy_array)

def draw_box3d_on_camera(rgb, boxes3d, color=(255, 0, 255), thickness=1, text_lables=[]):

    projections = box3d.box3d_to_rgb_box(boxes3d)
    rgb = box3d.draw_rgb_projections(rgb, projections, color=color, thickness=thickness)
    font = cv2.FONT_HERSHEY_SIMPLEX
    for i,text in enumerate(text_lables):
        text_pos = (np.min(projections[i,:, 0]), max(np.min(projections[i,:, 1]), 15) )
        cv2.putText(rgb, text, text_pos, font, 0.7, (0, 255, 100), 1, cv2.LINE_AA)

    return rgb

def draw_box3d_on_camera_obj(rgb, boxes3d, P, R0_rect, Tr_velo_to_cam, color=(255, 0, 255), thickness=1, text_lables=[]):

    projections = box3d.box3d_to_rgb_box_obj(boxes3d, P, R0_rect, Tr_velo_to_cam)
    rgb = box3d.draw_rgb_projections(rgb, projections, color=color, thickness=thickness)
    font = cv2.FONT_HERSHEY_SIMPLEX
    for i,text in enumerate(text_lables):
        text_pos = (np.min(projections[i,:, 0]), max(np.min(projections[i,:, 1]), 15) )
        cv2.putText(rgb, text, text_pos, font, 0.7, (0, 255, 100), 1, cv2.LINE_AA)

    return rgb
