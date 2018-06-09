#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uvctypes import *
import time
import cv2
import numpy as np
try:
  from queue import Queue
except ImportError:
  from Queue import Queue
import platform
import atexit

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

BUF_SIZE = 2
q = Queue(BUF_SIZE)

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

def raw_to_8bit(data):
  cv2.normalize(data, data, 0, 65535, cv2.NORM_MINMAX)
  np.right_shift(data, 8, data)
  return cv2.cvtColor(np.uint8(data), cv2.COLOR_GRAY2RGB)

def display_temperature(img, val_k, loc, color):
  val = ktof(val_k)
  cv2.putText(img,"{0:.1f} degF".format(val), loc, cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
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
    display_temperature(img, minVal, minLoc, (255, 0, 0))
    display_temperature(img, maxVal, maxLoc, (0, 0, 255))
    cv2.imshow('Lepton Radiometry', img)
    cv2.imwrite("test.jpg",img)
    
    cv2.waitKey(1)
          
def GetData(bWrite):
    raw = q.get(True, 500)
    if raw is None:
                  print("data is none")
    data = cv2.resize(raw[:,:], (640, 480))
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(data)
    img = raw_to_8bit(data)
    display_temperature(img, minVal, minLoc, (255, 0, 0))
    display_temperature(img, maxVal, maxLoc, (0, 0, 255))
    #cv2.imshow('Lepton Radiometry', img)
    if bWrite:
		cv2.imwrite("static/current.jpg",img)
    return minVal, maxVal, raw, img 

def exit_handler():
    print("Application is terminating!")
    cv2.destroyAllWindows()
    libuvc.uvc_stop_streaming(devh)
    libuvc.uvc_unref_device(dev)
    libuvc.uvc_exit(ctx)

def Run(X):
  x = 0
  while x<X:
    DoNextFrame()
    x+=1       

def MakeHistogram(rw):
		fig = Figure()
		FigureCanvas(fig)
		ax = fig.add_subplot(111)
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
		return tempsF, cdf


def HistLoop(tT,tPct):
    fig = Figure()
    FigureCanvas(fig)
    ax = fig.add_subplot(111)

    while True:
      try:
        mn, mx, rw, im = GetData()
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
OpenUVC()

#DoNextFrame()
#mn, mx, rw, im = GetData()
