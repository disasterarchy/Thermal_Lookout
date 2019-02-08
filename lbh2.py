#!/usr/bin/env python
# -*- coding: utf-8 -*-
from config import UnitsC
from uvctypes import *
import time
import pickle
import cv2
import numpy as np
import sys
try:
  from queue import Queue
except ImportError:
  from Queue import Queue
import platform
import atexit
from datetime import datetime 

#from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
#from matplotlib.figure import Figure

import io

# import the necessary packages for Picamera
#from picamera.array import PiRGBArray
#from picamera import PiCamera
import time
 
# initialize the camera and grab a reference to the raw camera capture
#camera = PiCamera()
#rawCapture = PiRGBArray(camera)
#camera.resolution=(1280,720)


BUF_SIZE = 2
q = Queue(BUF_SIZE)


binsF = np.arange(0,200,1)

def py_frame_callback(frame, userptr):

  array_pointer = cast(frame.contents.data, POINTER(c_uint16 * (frame.contents.width * frame.contents.height)))
  data = np.frombuffer(
    array_pointer.contents, dtype=np.dtype(np.uint16)
  ).reshape(
    frame.contents.height, frame.contents.width
  ) # no copy

  # data = np.fromiter(
  #   frame.contents.data, dtype=np.dtype(np.uint8), count=frame.contents.data_bytes
  # ).reshape(
  #   frame.contents.height, frame.contents.width, 2
  # ) # copy

  if frame.contents.data_bytes != (2 * frame.contents.width * frame.contents.height):
    return

  if not q.full():
    q.put(data)

PTR_PY_FRAME_CALLBACK = CFUNCTYPE(None, POINTER(uvc_frame), c_void_p)(py_frame_callback)

def ktof(val):
  return (1.8 * ktoc(val) + 32.0)

def ktoc(val):
  return (val - 27315) / 100.0

def ftok(val):
  return (val-32.0)*100.0/1.8+27315.0

def ctok(val):
  return (val+273.15)*100.0

def raw_to_8bit(data):
  cv2.normalize(data, data, 0, 65535, cv2.NORM_MINMAX)
  np.right_shift(data, 8, data)
  return cv2.cvtColor(np.uint8(data), cv2.COLOR_GRAY2RGB)

def display_temperature(img, val_k, loc, color):
  
  if UnitsC:
      val = ktoc(val_k)
      cv2.putText(img,"{0:.1f} C".format(val), loc, cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
  else:
      val = ktof(val_k)
      cv2.putText(img,"{0:.1f} F".format(val), loc, cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
  x, y = loc
  cv2.line(img, (x - 2, y), (x + 2, y), color, 1)
  cv2.line(img, (x, y - 2), (x, y + 2), color, 1)


def OpenUVC():
    res = libuvc.uvc_init(byref(ctx), 0)
    if res < 0:
        print("uvc_init error")
        exit(1)

  #try:
    res = libuvc.uvc_find_device(ctx, byref(dev), 0, 0, 0)
    if res < 0:
      print("uvc_find_device error")
      exit(1)

    res = libuvc.uvc_open(dev, byref(devh))
    if res < 0:
        print("uvc_open error")
        exit(1)

    print("device opened!")

    print_device_info(devh)
    print_device_formats(devh)

    frame_formats = uvc_get_frame_formats_by_guid(devh, VS_FMT_GUID_Y16)
    if len(frame_formats) == 0:
        print("device does not support Y16")
        exit(1)

    libuvc.uvc_get_stream_ctrl_format_size(devh, byref(ctrl), UVC_FRAME_FORMAT_Y16,
        frame_formats[0].wWidth, frame_formats[0].wHeight, int(1e7 / frame_formats[0].dwDefaultFrameInterval)
      )

    res = libuvc.uvc_start_streaming(devh, byref(ctrl), PTR_PY_FRAME_CALLBACK, None, 0)
    if res < 0:
        print("uvc_start_streaming failed: {0}".format(res))
        exit(1)


def DoNextFrame():
    data = q.get(True, 500)
    if data is None:
                  print("data is none")
    data = cv2.resize(data[:,:], (720, 540))
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(data)
    img = raw_to_8bit(data)
    display_temperature(img, minVal, minLoc, (255, 60, 60))
    display_temperature(img, maxVal, maxLoc, (80, 80, 255))
    cv2.imshow('Lepton Radiometry', img)
    cv2.imwrite("test.jpg",img)
    
    cv2.waitKey(1)
          
def GetData(bWrite=False):
    raw = q.get(True, 500)
    if raw is None:
                  print("data is none")
    data = cv2.resize(raw[:,:], (640, 480))
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(data)
    img = raw_to_8bit(data)
    display_temperature(img, minVal, minLoc, (255, 60, 60))
    display_temperature(img, maxVal, maxLoc, (80, 80, 255))
    #cv2.imshow('Lepton Radiometry', img)
    if bWrite:
      cv2.imwrite("static/current.jpg",img)
    time.sleep(0)  
    return minVal, maxVal, raw, img

def GetDataFast(bWrite=False):
    minVal = 0
    while minVal < 25000:
      raw = q.get(True, 500)
      if raw is None:
                    print("data is none")
      minVal = raw.min()
      maxVal = raw.max()

    return minVal, maxVal, raw 

def exit_handler():
    print("Application is terminating!")
    libuvc.uvc_stop_streaming(devh)
    libuvc.uvc_unref_device(dev)
    libuvc.uvc_exit(ctx)

def Run(X):
  x = 0
  while x<X:
    DoNextFrame()
    x+=1       

def MakeHistogramFast(rw):
    bins = np.concatenate((np.arange(-10,15,1),np.arange(16,35,0.4),np.arange(35,105,1),np.arange(105,400,2)))
    bins = (bins+273.15)*100
    counts, temps = np.histogram(rw,bins=bins)
    counts = np.insert(counts, 0,0)
    if UnitsC:
      temps = ktoc(temps)
    else:
      temps = ktof(temps)
    it = np.nditer(counts, flags=['f_index'])
    cdf = np.zeros_like(counts)
    while not it.finished:
      cdf[it.index]=np.sum(counts[it.index::])
      it.iternext()
    cdf = cdf/19200.0
    return temps, cdf

def MakeItPretty(rw, t, mn, mx):
  if UnitsC:
    lowerB = ctok(t['minTemp'])
    upperB = ctok(t['maxTemp'])
  else:
    lowerB = ftok(t['minTemp'])
    upperB = ftok(t['maxTemp'])
  time.sleep(0)
  #rw = cv2.flip(rw,1)
  mask = cv2.inRange(rw,lowerB, upperB)
  imask = cv2.bitwise_not(mask)
  img = raw_to_8bit(rw)
  img_bg = cv2.bitwise_and(img,img, mask=imask)
  im_hot = cv2.applyColorMap(img, 2)
  im_hot_fg = cv2.bitwise_and(im_hot,im_hot,mask=mask)
  composite = cv2.add(im_hot_fg,img_bg)
  img2 = cv2.resize(composite[:,:], (640, 480))
  raw = cv2.resize(rw[:,:], (640, 480))
  minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(raw)
      #http://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_colorspaces/py_colorspaces.html
      #https://docs.opencv.org/3.2.0/d0/d86/tutorial_py_image_arithmetics.html
  img = cv2.copyMakeBorder(img2,top=0, bottom=80, left=0, right=30, borderType=0)
  mnLoc = (minLoc[0]+0,minLoc[1]+0)
  mxLoc = (maxLoc[0]+0,maxLoc[1]+0)
  if mn < 27300:
    print "PROBLEM"
    np.savetxt('raw.csv',raw,delimiter=',')
    print mn, mx
    cv2.imwrite('prettybad.jpg',img)
    cv2.imwrite('img2.jpg',img2)

  display_temperature(img, mn, minLoc, (255, 200, 200))
  display_temperature(img, mx, maxLoc, (0, 0, 140))
  color = (255,255,255)
  if t['nOn']>=1:
    TextInfo = t['name'] + ' ACTIVE'
  else:
    TextInfo = ""
  cv2.putText(img, TextInfo, (15,15), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
  if UnitsC:
    TextInfo = '%.2f percent is in range %.0f C to %.0f C' % (t['pctInRange'], t['minTemp'], t['maxTemp'])
  else:
    TextInfo = '%.2f percent is in range %.0f F to %.0f F' % (t['pctInRange'], t['minTemp'], t['maxTemp'])
  cv2.putText(img, TextInfo, (20,500), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
  TextInfo = datetime.now().__format__("%m-%d-%Y %H:%M:%S") 
  cv2.putText(img, TextInfo, (10,540), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
#  cv2.imwrite('pretty.jpg',img)
  return img

def MakeItPretty2(rw, t, mn, mx):
  #rawCapture = PiRGBArray(camera)
  if UnitsC:
    lowerB = ctok(t['minTemp'])
    upperB = ctok(t['maxTemp'])
  else:
    lowerB = ftok(t['minTemp'])
    upperB = ftok(t['maxTemp'])
  mask = cv2.inRange(rw,lowerB, upperB)
  imask = cv2.bitwise_not(mask)
  img = raw_to_8bit(rw)
  img_bg = cv2.bitwise_and(img,img, mask=imask)
  im_hot = cv2.applyColorMap(img, 2)
  im_hot_fg = cv2.bitwise_and(im_hot,im_hot,mask=mask)
  composite = cv2.add(im_hot_fg,img_bg)
  img2 = cv2.resize(composite[:,:], (480, 360))
  raw = cv2.resize(rw[:,:], (480, 360))
  time.sleep(0)
  minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(raw)
      #http://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_colorspaces/py_colorspaces.html
      #https://docs.opencv.org/3.2.0/d0/d86/tutorial_py_image_arithmetics.html
  img = cv2.copyMakeBorder(img2,top=0, bottom=60, left=0, right=410, borderType=0)
  mnLoc = (minLoc[0]+0,minLoc[1]+0)
  mxLoc = (maxLoc[0]+0,maxLoc[1]+0)
  display_temperature(img, mn, minLoc, (255, 200, 200))
  display_temperature(img, mx, maxLoc, (0, 0, 140))
  colorWHT = (255,255,255)
  if t['nOn']>=1:
    TextInfo = t['name'] + ' ACTIVE'
    color = (255,20,20)
  else:
    TextInfo = "No active trigger"
    color = (255,255,255)
  cv2.putText(img, TextInfo, (10,380), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
  #TextInfo = '%.2f'  % (t['pctInRange']) + ' % in range' 
  #cv2.putText(img, TextInfo, (10,535), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
  if UnitsC:
    TextInfo = '%.2f'  % (t['pctInRange']) + ' % in range ' +'%.0f C to %.0f C' % ( t['minTemp'], t['maxTemp'])
  else:
    TextInfo = '%.2f'  % (t['pctInRange']) + ' % in range ' + '%.0f F to %.0f F' % ( t['minTemp'], t['maxTemp'])
  cv2.putText(img, TextInfo, (10,400), cv2.FONT_HERSHEY_SIMPLEX, 0.75, colorWHT, 2)
  
  TextInfo = datetime.now().__format__("%m-%d-%Y %H:%M:%S") 
  cv2.putText(img, TextInfo, (490,330), cv2.FONT_HERSHEY_SIMPLEX, 0.75, colorWHT, 2)
#  cv2.imwrite('pretty.jpg',img)
  camera.capture(rawCapture, format="bgr")
  image = rawCapture.array
  small = cv2.resize(image, (410,308))
  x=0
  y=480
  img[x:x+small.shape[0], y:y+small.shape[1]]=small
  return img
  
def MakeSavedImage(img, Big):
  image = cv2.resize(Big, (1280,720))
  imageBig = cv2.copyMakeBorder(image, top=0, bottom = 0, left = 700, right = 0, borderType=0)
  x = 60
  y = 0
  imageBig[x:x+img.shape[0], y:y+img.shape[1]]=img
  return imageBig

def GetPiCameraImage():
  # grab an image from the camera
  rawCapture = pCamera.get_frame()
 
  # allow the camera to warmup
  #time.sleep(0.05)
  #camera.capture(rawCapture, format="bgr")
  imageBig = rawCapture.array
  imageSmall = cv2.resize(imageBig, (160,120))
  
  return imageBig, imageSmall


def HistLoop(tT,tPct):
    fig = Figure()
    FigureCanvas(fig)
    ax = fig.add_subplot(111)

    while True:
      try:
        mn, mx, rw, im = GetData(True)
        cv2.imwrite("static/current.jpg",im)
        counts, temps = np.histogram(rw,bins=256)
        counts = np.insert(counts, 0,0)
        tempsF = ktof(temps)
        ax.plot(tempsF,counts)
        fig.savefig('static/histogram')
        ax.clear()
        it = np.nditer(counts, flags=['f_index'])
        cdf = np.zeros_like(counts)
        while not it.finished:
          cdf[it.index]=np.sum(counts[it.index::])
          it.iternext()
        cdf = cdf/19200.0
        ax.plot(tempsF,cdf)
        fig.savefig('static/cdf')
        idx = np.abs(tempsF-tT).argmin()
        PctExceeded = cdf[idx]
        print(PctExceeded*100, "% exceeds ", tT)
      except:
        print("error")
      
ctx = POINTER(uvc_context)()
dev = POINTER(uvc_device)()
devh = POINTER(uvc_device_handle)()
ctrl = uvc_stream_ctrl()
atexit.register(exit_handler)
# Setup Picamera
#stream = io.BytesIO()
#camera = picamera.PiCamera()
#camera.start_preview()
#time.sleep(2)
#camera.capture(stream, format='jpeg')
#Open UVC Camera
OpenUVC()

#DoNextFrame()
#mn, mx, rw, im = GetData()