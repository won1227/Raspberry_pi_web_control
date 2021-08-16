import cv2
import sys
import time
import numpy as np
import pytesseract
import threading

cap = cv2.VideoCapture(-1)

class Camera():
	thread = None  # background thread that reads frames from camera
	frame = None  # current frame is stored here by background thread
	last_access = 0  # time of last client access to the camera

	def initialize(self):
		if Camera.thread is None:
			# start background frame thread
			Camera.thread = threading.Thread(target=self._thread)
			Camera.thread.start()

			# wait until frames start to be available
			while self.frame is None:
				time.sleep(0)

	def get_frame(self):
		Camera.last_access = time.time()
		self.initialize()
		return self.frame

	@classmethod
	def _thread(cls):
		success, cls.frame = cap.read()
		while success:
			print('!!!')
			imgH, imgW, _ = cam.shape

			x1,y1,w1,h1 = 0,0,imgH,imgW

			gray = cv2.cvtColor(cam,cv2.COLOR_BGR2GRAY)
			blur = cv2.GaussianBlur(gray, (3,3),0)
			thr = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,5)

			imgchar = pytesseract.image_to_string(thr, lang='hangul+eng',config='--psm 10 --oem 3')
			imgboxes = pytesseract.image_to_boxes(thr)

			print(imgchar)

			for boxes in imgboxes.splitlines():	#영상에서 글자에 네모박스 만들어준다
				boxes = boxes.split(' ')
				x,y,w,h = int(boxes[1]),int(boxes[2]),int(boxes[3]),int(boxes[4])
				cv2.rectangle(cam,(x,imgH-y),(w,imgH-h),(0,0,255),2)
			cv2.imshow('frame', cam)
# if there hasn't been any clients asking for frames in
# the last 10 seconds stop the thread
			if time.time() - cls.last_access > 10:
				break
#		cls.thread = None

if __name__ == '__main__':
	Camera()
