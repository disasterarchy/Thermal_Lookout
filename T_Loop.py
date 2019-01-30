from config import UnitsC, f_triggers, web_url, upload_url, key, your_token, your_domain, img_url, key
from local_basic_hist import *
import time
import numpy as np
import json
import urllib2
import requests
import threading
from base_camera import BaseCamera



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
    rout = requests.post(my_url, data=data)
    print(rout.text)
    
def UpdateTriggers(out, triggers):
    newtriggers={}
    for ln in out[1::]:
            if ln:
                t = ln.split(',')
                d = {}
                n = t[0]
                d['updated'] = str(t[7])
                d['name'] = t[0]
                d['pct'] = float(t[3])
                d['minTemp']=float(t[1])
                d['maxTemp']=float(t[2])
                d['delayOn'] = float(t[4])
                d['delayOff'] = float(t[5])
                d['delayRepeat']= float(t[6])
                
                try:
                    tn = triggers[n]['updated']
                    if tn == d['updated']:
                        d['nOn']=triggers[n]['nOn']
                        d['nOff']=triggers[n]['nOff']
                        d['nRepeat']=triggers[n]['nRepeat']
                    else:
                        d['nOn']=0
                        d['nOff']=0
                        d['nRepeat']=9.999E+9
                except:
                    print('Add new trigger ' , n)
                    d['nOn']=0
                    d['nOff']=0
                    d['nRepeat']=9.999E+9
                newtriggers[n] = d
    return newtriggers

def SaveImages(rw, t, mn, mx,Big,Small):
        
        img = MakeItPretty(rw, t, mn, mx)
        BigImg = MakeSavedImage(img, Big)
        o = CloudSync(ktof(mn), ktof(mx), BigImg, None, True)
        url = img_url + o.text
        Triggered(t, PctInRange*100, url, ktof(mx), True)
        s = datetime.now()
        ff = open('static/archive/log.csv','a')
        nowstr = datetime.now().strftime("%m_%d_%y-%H:%M:%S")
        fnameT = 'thermal_'+ nowstr + '.jpg'
        fnameV = 'visible_'+ nowstr + '.jpg'
        if UnitsC:
            ff.write( nowstr + ',' + t['name'] + ',' + str(ktoc(mx)) + ',' + str(ktof(mn)) + ',' + fnameT + ',' +fnameV+"\n")
        else:
            ff.write( nowstr + ',' + t['name'] + ',' + str(ktof(mx))+ ',' + str(ktof(mn)) + ',' + fnameT + ',' +fnameV + "\n")
        ff.close()
        cv2.imwrite("static/archive/" + fnameV,Big)
        cv2.imwrite("static/archive/thumb/" + fnameV,Small)
        cv2.imwrite("static/archive/" + fnameT,img)
        tSmall = cv2.resize(img, (160,120))
        cv2.imwrite("static/archive/thumb/" + fnameT,tSmall)
        

def MainLoop ():
    while True:
        LoopActions
        
def LoopActions (retImg=False):
            s1=datetime.now()
            
            time.sleep(0)
            mn, mx, rw = GetDataFast(False)
            time.sleep(0)
            tempsF, cdf = MakeHistogramFast(rw)
            tval=0
            activet=''
            for k,t in trs.iteritems():
                idxMin = np.abs(tempsF-t['minTemp']).argmin()
                idxMax = np.abs(tempsF-t['maxTemp']).argmin()
                PctInRange = cdf[idxMin] - cdf[idxMax]
                t['pctInRange']=PctInRange*100
                if PctInRange*100 > t['pct']:
                    activet =  t['name']
                    #temperatures are in Range
                    t['nOn']+=1
                    t['nOff']=0
                    if t['nOn'] >= t['delayOn']:
                        #Delay condition is met 
                        if t['nRepeat'] > t['delayRepeat']:
                        #Sufficient time has passed since last trigger
                            Big, Small = GetPiCameraImage()
                            thread = threading.Thread(target=SaveImages, args=[rw,t,mn,mx, Big, Small])
                            thread.start()
                            t['nRepeat']=0
                            print "TRIGGER ",t['name'], PctInRange*100, "% is in range exceeds ", t['minTemp'], ' - ', t['maxTemp']
                else:
                    #Temperatures not in Range
                    #print(PctInRange*100, "% in range ", t['minTempF'], '-', t['maxTempF'])
                    t['nOn'] = 0
                    t['nOff'] += 1
                    if t['nOff'] == t['delayOff']:
                        Triggered(t, PctInRange, mn, mx, False)
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
            s3=datetime.now()
            #o = CloudSync(ktof(mn),ktof(mx),im, key,'')
            s4=datetime.now()
            td1=s2-s1
            td2=s3-s2
            td3=s4-s3
            tdd = s4-s1
            #print 1.0/tdd.total_seconds()
            #print(td1.total_seconds(),td2.total_seconds(),td3.total_seconds())   
            if retImg:
                return img
        #except:
            #print('error')

class Camera(BaseCamera):

    @staticmethod
    def frames():
        while True:
            # read current frame
            img = LoopActions(True)

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()
     
def CloudSync(mn, mx, im, k, ReturnURL):
        img = cv2.imencode(".jpg",im)[1].tostring()
        files = {'img':img}
        data = {'minTempF':mn, 'maxTempF': mx, 'key': k, 'ReturnURL': ReturnURL}
        rout = requests.post(upload_url, data=data, files=files)
        return rout

with open('trs.pickle', 'rb') as handle:
    trs=  pickle.load(handle)

#tcsv = open('triggers.csv','r')
#o = tcsv.readlines()
#tcsv.close()
#trs = UpdateTriggers(o, {})

#t = {'minTempF':85, 'maxTempF':95}
#mn, mx, rw, immm = GetData(False)
#MakeItPretty(rw,12.123, t)
