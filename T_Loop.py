from config import UnitsC, f_triggers, web_url, upload_url, key, your_token, your_domain, img_url, key
from lbh2 import *
import time
import numpy as np
import json
import urllib2
import requests
import threading
from base_camera import BaseCamera
from camera_pi import pCamera


bWriteImages = True
bSaveVideo = True

def Triggered(trigger, PctExceeded, url, mx, bVal):
	if bVal:
		my_url = web_url.replace('{event}',trigger['name'])
		data = {'value1': PctExceeded, 'value2': mx, 'value3': url}
		print('TRIGGERED' + trigger['name'])
	else:
		my_url = web_url.replace('{event}',"no_" + trigger['name'])
		data = {'value1': '%.2f' % PctExceeded, 'value2': '%.2f' % mx, 'value3': url}
		print("no_"+trigger['name'])
	#req = urllib2.Request(my_url)
	#req.add_header('Content-Type', 'application/json')
	#response = urllib2.urlopen(req, json.dumps(data))
	#headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}    
	#data = json.dumps(data)
	try:
		rout = requests.post(my_url, data=data)
		print(rout.text)
	except:
		print "Could not contact IFTTT cloud"


def SaveImages(rw, t, mn, mx,PctInRange):
	try:
		time.sleep(0.01)
		s = datetime.now()
		ff = open('static/archive/log.csv','a')
		nowstr = datetime.now().strftime("%m_%d_%y-%H:%M:%S")
		fnameT = 'thermal_'+ nowstr + '.jpg'
		fnameV = 'visible_'+ nowstr + '.jpg'       
		c = pCamera()
		vis_frame = c.get_frame()
		FF = open("static/archive/" + fnameV, 'w')
		FF.write(vis_frame)
		FF.close()
		Big = cv2.imread("static/archive/" + fnameV)
		Small = cv2.resize(Big, (160,120))
		img = MakeItPretty(rw, t, mn, mx)
		BigImg = MakeSavedImage(img, Big)
		o = CloudSync(ktof(mn), ktof(mx), BigImg, None, True)
		url = img_url + o
		Triggered(t, PctInRange*100, url, ktof(mx), True)
		
		if UnitsC:
			ff.write( nowstr + ',' + t['name'] + ',' + str(ktoc(mx)) + ',' + str(ktof(mn)) + ',' + fnameT + ',' +fnameV+"\n")
		else:
			ff.write( nowstr + ',' + t['name'] + ',' + str(ktof(mx))+ ',' + str(ktof(mn)) + ',' + fnameT + ',' +fnameV + "\n")
		ff.close()
		time.sleep(0)
		cv2.imwrite("static/archive/" + fnameV,Big)
		cv2.imwrite("static/archive/thumb/" + fnameV,Small)
		cv2.imwrite("static/archive/" + fnameT,img)
		tSmall = cv2.resize(img, (160,120))
		cv2.imwrite("static/archive/thumb/" + fnameT,tSmall)
	except:
		print "Error with images", sys.exc_info()
		

def MainLoop ():
	while True:
		LoopActions
		
def LoopActions (retImg=False):
	try:
			s1=datetime.now()
			
			time.sleep(0.01)
			mn, mx, rw = GetDataFast(False)
			tempsF, cdf = MakeHistogramFast(rw)
			tval=0
			activet=''
			for k,t in trs.iteritems():
				idxMin = np.abs(tempsF-t['minTemp']).argmin()
				idxMax = np.abs(tempsF-t['maxTemp']).argmin()
				if activet == '':
					activet  = t['name']
				elif (trs[activet]['nOn']==0) & (t['minTemp'] < trs[activet]['minTemp']):
					activet  = t['name']
				PctInRange = cdf[idxMin] - cdf[idxMax]
				t['pctInRange']=PctInRange*100
				if PctInRange*100 > t['pct']:
					activet =  t['name']
					#temperatures are in Range
					t['nOn']+=1
					
					#print t['nOn'], t['nRepeat']
					if t['nOn'] >= t['delayOn']:
						#Delay condition is met
							if t['nOff'] > t['delayOff'] or (t['nRepeat'] > t['delayRepeat']):
												  
							#Sufficient time has passed since last trigger
							#Big, Small = GetPiCameraImage()
								thread = threading.Thread(target=SaveImages, args=[np.array(rw, copy=True),t,mn,mx, float(PctInRange)])
								thread.start()
								t['nRepeat']=0
								print "TRIGGER ",t['name'], PctInRange*100, "% is in range exceeds ", t['minTemp'], ' - ', t['maxTemp']
							t['nOff']=0
				else:
					#Temperatures not in Range
					#print(PctInRange*100, "% in range ", t['minTempF'], '-', t['maxTempF'])
					t['nOn'] = 0
					t['nOff'] += 1
					if t['nOff'] == t['delayOff']:
						thread = threading.Thread(target=Triggered, args=[t, PctInRange, mn, mx, False])
						thread.start()
						print("NULL TRIGGER", t['name'])
				#print(t['name'], ' ', PctInRange*100, ' ', t['minTempF'], '-', t['maxTempF'], ' ', t['nOn'])
				#print t['name'], '%.1f' % t['pct'], t['nOn'], t['nOff'], t['nRepeat']
				
				t['nRepeat']+=1
			try:
				t=trs[activet]
			except:
				t= {'minTemp':0, 'maxTemp':800, 'pctInRange':100, 'nOn':0}
			s2=datetime.now()
			img = MakeItPretty(rw, t, mn, mx)
			#try:
			#    q2.put(im,True,0.5)
			#except:
			#    print "can't put!"
			#o = CloudSync(ktof(mn),ktof(mx),im, key,'')
			#print 1.0/tdd.total_seconds()
			#print(td1.total_seconds(),td2.total_seconds(),td3.total_seconds())   
			if retImg:
				return img
	except:
			print 'Error in LoopActions', sys.exc_info()

class Camera(BaseCamera):

	@staticmethod
	def frames():
		while True:
			# read current frame
			img = LoopActions(True)

			# encode as a jpeg image and return it
			yield cv2.imencode('.jpg', img)[1].tobytes()
	 
def CloudSync(mn, mx, im, k, ReturnURL):
		try:
			img = cv2.imencode(".jpg",im)[1].tostring()
			files = {'img':img}
			data = {'minTempF':mn, 'maxTempF': mx, 'key': k, 'ReturnURL': ReturnURL}
			rout = requests.post(upload_url, data=data, files=files)
			return rout.text
		except:
			print "Could not sync to Thermal_lookout cloud"
			return "CloudNotAvailable"

try:
	with open('trs.pickle', 'rb') as handle:
		trs=  pickle.load(handle)
except:
	trs = {}
#tcsv = open('triggers.csv','r')
#o = tcsv.readlines()
#tcsv.close()
#trs = UpdateTriggers(o, {})

#t = {'minTempF':85, 'maxTempF':95}
#mn, mx, rw, immm = GetData(False)
#MakeItPretty(rw,12.123, t)
