from flask import Flask, render_template,url_for,request,Response,redirect,g
import os
import serial
import time
import cv2
import sys
import numpy as np
import pytesseract
import RPi.GPIO as GPIO

GPIO.setwarnings(False)

app = Flask(__name__)


serial_p = serial.Serial('/dev/ttyACM0', 9600, timeout = 1)
serial_p.flush()


web_flag = False
pz_data = 0
global panServoAngle
global tiltServoAngle
panServoAngle = 150
tiltServoAngle = 60
os.system("python3 angleServoCtrl.py " + "17 " + str(panServoAngle))
os.system("python3 angleServoCtrl.py " + "27 " + str(tiltServoAngle))

#servo_motor
panPin = 17
tiltPin = 27  

led = 19
GPIO.setmode(GPIO.BCM)
GPIO.setup(led, GPIO.OUT)

cap = cv2.VideoCapture(-1)

GPIO.output(led,True)
time.sleep(1)
GPIO.output(led,False)

@app.route('/')
@app.route('/form_send')											#초기화면
def form_send():
	return render_template('form_send.html')	


@app.route('/go_next')
def go_next():
	return render_template('go_next.html')
	
@app.route('/form_recv',methods=['POST'])
def form_recv():													#결과화면
	global pz_data
	if request.method == 'POST':
		data = request.form
		data = data.get('number')
		pz_data = data
		

	return render_template('form_send.html',pz_data=pz_data)


@app.route('/picam')												#파이_카메라
def index():														#비디오 스트리밍
	return redirect(url_for('form_send'))


def gen():								# video streaming function
	global imgchar_num
	while True:
		success, frame = cap.read()
		if success:
			try:
				ret, buffer = cv2.imencode('.jpg', frame)
				frame = buffer.tobytes()

				yield(b'--frame\r\n'
					b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
			except Exception as e:
				pass
		else:
			pass

@app.route('/video_feed')
def video_feed():													#비디오 스트리밍 루트
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')
	
#cv2 camera

@app.route('/cv_picam')												#파이_카메라
def cv_index():														#비디오 스트리밍
	return redirect(url_for('form_send'))


def cv_gen():								# video streaming function
	global web_flag
	while True:
		success, frame = cap.read()
		if success:
			imgH, imgW, _ = frame.shape
			x1,y1,w1,h1 = 0,0,imgH,imgW
			gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)	# Grayscale 변환
			blur = cv2.GaussianBlur(gray, (3,3),0)	# 3x3 픽셀값에서 가운데있는 픽셀에 가중치를 좀 더 높게 주어 큰 값은 선명해지도록 만들어준다.
			th = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,5) # 영상 이진화(binary)
			imgchar = pytesseract.image_to_string(th, lang='hangul+eng',config='--psm 10 --oem 3')	# 이미지에서 문자열 추출 
			imgboxes = pytesseract.image_to_boxes(th)
			
			str = imgchar.split('\n')[0:-1]				#202 개행없음
			imgchar = '\n'.join(str)
					
			print(imgchar)
			print(pz_data)			

		if imgchar == pz_data:
			web_flag = True
			for i in range(5):
				GPIO.output(led,True)
				time.sleep(0.3)
				GPIO.output(led,False)
				time.sleep(0.3)

			try:
				ret, buffer = cv2.imencode('.jpg', frame)
				frame = buffer.tobytes()

				yield(b'--frame\r\n'
					b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
			except Exception as e:
				pass
		else:
			web_flag = False

@app.route('/finish')
def finish():
	global web_flag
	if web_flag == True:
		return render_template('finish.html')
	elif web_flag == False:
		return render_template('form_send.html')
		
			
@app.route('/cv_video_feed')
def cv_video_feed():													#비디오 스트리밍 루트
    return Response(cv_gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

#angle
@app.route("/<servo>/<angle>")										#카메라 팬 / 틸트 제어
def move(servo, angle):
	global panServoAngle
	global tiltServoAngle
	if servo == 'pan':
		if angle == '+':
			panServoAngle = panServoAngle + 10
		else:
			panServoAngle = panServoAngle - 10
		os.system("python3 angleServoCtrl.py " + str(panPin) + " " + str(panServoAngle))
	if servo == 'tilt':
		if angle == '+':
			tiltServoAngle = tiltServoAngle + 10
		else:
			tiltServoAngle = tiltServoAngle - 10
		os.system("python3 angleServoCtrl.py " + str(tiltPin) + " " + str(tiltServoAngle))

	return redirect(url_for('index'))

@app.route("/go")
def go_move():
	serial_p.write(bytes('w\n', encoding='ascii'))
	return render_template('form_send.html')

@app.route("/stop")
def stop_move():
	serial_p.write(bytes('x\n', encoding='ascii'))
	return render_template('form_send.html')
	


if __name__ =='__main__':
	app.run(host = '192.168.0.7', port= 5000)
	
cap.release()
cv2.destroyAllWindows()

