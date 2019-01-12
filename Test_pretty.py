from basic_hist import *
#import picamera
import time
import io

#stream = io.BytesIO()
#with picamera.PiCamera() as camera:
#    camera.start_preview()
#    time.sleep(2)
#    camera.capture(stream, format='jpeg')

# Construct a numpy array from the stream
#data = np.fromstring(stream.getvalue(), dtype=np.uint8)
# "Decode" the image from the array, preserving colour
#image = cv2.imdecode(data, 1)
# OpenCV returns an array with data in BGR order. If you want RGB instead
# use the following...
#cv2.imwrite('rgb.jpg', image)
#

t = {'minTempF':85, 'maxTempF':95}
pct = 12.125
mn, mx, rw, immm = GetData(False)
lowerB = ftok(t['minTempF'])
upperB = ftok(t['maxTempF'])
mask = cv2.inRange(rw,lowerB, upperB)
cv2.imwrite('mask.jpg', mask)
imask = cv2.bitwise_not(mask)
cv2.imwrite('mask_inv.jpg', imask)
img = raw_to_8bit(rw)
img_bg = cv2.bitwise_and(img,img, mask=imask)
cv2.imwrite('img_bg.jpg',img_bg)
im_hot = cv2.applyColorMap(img, 2)
im_hot_fg = cv2.bitwise_and(im_hot,im_hot,mask=mask)
cv2.imwrite('im_hot.jpg',im_hot)
cv2.imwrite('im_hot.jpg_fg',im_hot_fg)
composite = cv2.add(im_hot_fg,img_bg)
img2 = cv2.resize(composite[:,:], (640, 480))
raw = cv2.resize(rw[:,:], (640, 480))
minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(raw)
    #http://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_colorspaces/py_colorspaces.html
    #https://docs.opencv.org/3.2.0/d0/d86/tutorial_py_image_arithmetics.html
img = cv2.copyMakeBorder(img2,top=0, bottom=100, left=30, right=30, borderType=0)
display_temperature(img, mn, minLoc, (255, 140, 140))
display_temperature(img, mx, maxLoc, (240, 240, 255))
color = (255,255,255)
TextInfo = '%.2f percent is in range %.0f F to %.0f F' % (pct, t['minTempF'], t['maxTempF'])
cv2.putText(img, TextInfo, (10,500), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
TextInfo = datetime.now().__format__("%m-%d-%Y %H:%M:%S") 
cv2.putText(img, TextInfo, (10,540), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
cv2.imwrite('pretty.jpg',img)

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
 
# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
rawCapture = PiRGBArray(camera)
 
# allow the camera to warmup
time.sleep(0.1)
 
# grab an image from the camera
camera.capture(rawCapture, format="bgr")
image = rawCapture.array
 
# display the image on screen and wait for a keypress
#cv2.imshow("Image", imageBig)
#cv2.waitKey(0)

imageBig = cv2.copyMakeBorder(image, top=0, bottom = 0, left = 700, right = 0, borderType=0)
x = 100
y = 0
imageBig[x:x+img.shape[0], y:y+img.shape[1]]=img

cv2.imwrite('combine.jpg',imageBig)

