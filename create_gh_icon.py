"""GitHub Pages用にicon-512.pngを生成"""
import os
import cv2
import numpy as np

def bezier(p0, p1, p2, n=30):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0]
        y = (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1]
        pts.append([int(x), int(y)])
    return np.array(pts, np.int32)

img = np.full((512, 512, 3), (30, 30, 30), dtype=np.uint8)
pts1 = bezier((150, 350), (150, 150), (200, 150))
pts2 = bezier((200, 150), (250, 150), (250, 350))
cv2.polylines(img, [pts1, pts2], False, (255, 255, 255), 15)
pts3 = bezier((260, 350), (260, 180), (310, 180))
pts4 = bezier((310, 180), (360, 180), (360, 350))
cv2.polylines(img, [pts3, pts4], False, (204, 204, 204), 15)
pts5 = np.array([[120, 400], [180, 320], [250, 360], [320, 280], [400, 220]], np.int32)
cv2.polylines(img, [pts5], False, (197, 209, 79), 12)
for c in [(120, 400), (180, 320), (250, 360), (320, 280), (400, 220)]:
    cv2.circle(img, c, 10, (197, 209, 79), -1)

base = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(base, 'docs', 'icon-512.png')
os.makedirs(os.path.dirname(out), exist_ok=True)
cv2.imwrite(out, img)
print(f"Created: {out}")
