from basic_hist import *
import time
import numpy as np
import json
import urllib2


f_triggers = open('triggers.csv','r')
web_url = 'https://maker.ifttt.com/trigger/{event}/with/key/cxREu7pLkejEkwtCRKMfiA'

triggers = []

for ln in f_triggers.readlines():
    t = ln.split(',')
    d = {}
    d['name'] = t[0]
    d['pct'] = float(t[1])
    d['tempF']=float(t[2])
    d['delay'] = float(t[3])
    d['off']= float(t[4])
    d['n']=0
    d['o']=0
    triggers.append(d)

bWriteImages = True
bSaveVideo = True

def Triggered(trigger, PctExceeded, mn, mx, bVal):
    if bVal:
        my_url = web_url.replace('{event}',trigger['name'])
        data = {'value1': PctExceeded, 'value2': mx, 'value3': mn}
        print(trigger['name'])
    else:
        my_url = web_url.replace('{event}',"no_" + trigger['name'])
        data = {'value1': PctExceeded, 'value2': mx, 'value3': mn}
        print("no_"+trigger['name'])
    req = urllib2.Request(my_url)
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, json.dumps(data))

    
def MainLoop ():
    while True:
        #try:
            mn, mx, rw, im = GetData(True)
            tempsF, cdf = MakeHistogram(rw)
            for trigger in triggers:
                idx = np.abs(tempsF-trigger['tempF']).argmin()
                PctExceeded = cdf[idx]
                if PctExceeded*100 > trigger['pct']:
                    trigger['n']+=1
                    trigger['o']=0
                    if trigger['n'] == trigger['delay']:
                        Triggered(trigger, PctExceeded, mn, mx, True)
                        print("TRIGGER ",trigger['name'], PctExceeded*100, "% exceeds ", trigger['tempF'])
                else:
                    print(PctExceeded*100, "% exceeds ", trigger['tempF'])
                    trigger['n'] = 0
                    trigger['o'] += 1
                    if trigger['o'] == trigger['off']:
                        Triggered(trigger, PctExceeded, mn, mx, False)
                    
                    
        #except:
            #print('error')
            
    


