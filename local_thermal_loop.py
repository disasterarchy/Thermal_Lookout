from local_basic_hist import *
import time
import numpy as np
import json
import urllib2
import requests


f_triggers = open('triggers.csv','r')
web_url = 'https://maker.ifttt.com/trigger/{event}/with/key/cxREu7pLkejEkwtCRKMfiA'
dns_url = 'https://duckdns.org/update/{YOURDOMAIN}/{YOURTOKEN}/'
upload_url = 'https://thermal-lookout.appspot.com/upload'
key = "ahFzfnRoZXJtYWwtbG9va291dHI6CxIHTG9va291dCIWZGVmYXVsdF90aGVybWFsTG9va291dAwLEgpTYXZlZEltYWdlGICAgICA8ogKDA"
your_token = '481eb920-6df8-4ebd-aa63-8d64198833a9'
your_domain = 'thermal-lookout'
img_url = "https://thermal-lookout.appspot.com/img?img_id="

key = "ahFzfnRoZXJtYWwtbG9va291dHI6CxIHTG9va291dCIWZGVmYXVsdF90aGVybWFsTG9va291dAwLEgpTYXZlZEltYWdlGICAgICg55gKDA"
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
                #print d['name']
    return newtriggers
   
def MainLoop ():
    tcsv = open('triggers.csv','r')
    o = tcsv.readlines()
    tcsv.close()
    trs = UpdateTriggers(o, {})
    while True:
        LoopActions
        
def LoopActions (retImg=False):
            s1=datetime.now()
            mn, mx, rw = GetDataFast(False)
            print ktof(mx)
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
                    if t['nOn'] == t['delayOn']:
                        #Delay condition is met 
                        if t['nRepeat'] > t['delayRepeat']:
                        #Sufficient time has passed since last trigger
                            img = MakeItPretty(rw, t, mn, mx)
                            s = datetime.now()
                            BigImg = MakeSavedImage(img)
                            cv2.imwrite("static\BigImage.jpg",BigImg)
                            #o = CloudSync(ktof(mn), ktof(mx), BigImg, None, True)
                            print "Big Image: ", datetime.now()-s
                            
                            url = img_url + "BigImage.jpg"
                            Triggered(t, PctInRange*100, url, ktof(mx), True)
                            t['nRepeat']=0
                            print "TRIGGER ",t['name'], PctInRange*100, "% is in range exceeds ", t['minTemp'], ' - ', t['maxTempF']
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



#t = {'minTempF':85, 'maxTempF':95}
#mn, mx, rw, immm = GetData(False)
#MakeItPretty(rw,12.123, t)
