import requests
import threading
import time
from flask import Flask
from local_thermal_loop import *
from flask import render_template
from flask import request, redirect, url_for

app = Flask(__name__)

@app.before_first_request
def activate_job():
    #def run_job():
    #    while True:
    #        print("Run recurring task")
    #        time.sleep(3)
    
    thread = threading.Thread(target=MainLoop)
    thread.start()

@app.route("/")
def hello():
    return "Hello World!"

@app.route('/data/current.jpg')
def CurrentImage():
	#imm = cv2.imread("test.jpg")
	mn, mx, rw, imm = GetData()
	#basic_hist.MakeHistogram(rw)
	buf = cv2.imencode(".jpg",imm)
	resp = Flask.make_response(app, buf[1].tostring())
	resp.content_type = "image/jpeg"
	return resp

@app.route('/triggers')
def triggers():
    tcsv = open('triggers.csv','r')
    o = tcsv.readlines()
    Triggers = UpdateTriggers(o, {})
    return render_template('triggers.html', triggers=trs.values(), url='me')


@app.route('/trgs')
def trgs():
    return render_template('triggers.html', triggers=trs.values(), url='me')


@app.route('/status')
def status(name=None):
    return render_template('status.html', name="Erik")

@app.route('/update', methods=['POST','GET'])
def update():
    action = request.form['submit']
    rf = request.form
    if action == "Delete":
        print "DELETE"
        print rf['triggerName']
        del trs[rf['triggerName']]
        #TODO add delete code
        
    #if action == "Save":
    #    trs[rf['name']]['name'] = rf['name']
    #    trs[rf['name']]['minTemp'] = rf['minTemp']

    else:
        if action != "Save":
            trs[rf['triggerName']]={}
    #   print "Add"
    #    print(request.form['name'])
    #    print(request.form)
        #trs[rf['name']] = request.form['name']
    
        trs[rf['triggerName']]['name'] = rf['triggerName']
        trs[rf['triggerName']]['minTemp'] = rf['minTemp']
        trs[rf['triggerName']]['maxTemp'] = rf['maxTemp']
        trs[rf['triggerName']]['pct'] = rf['imgPercent']
        trs[rf['triggerName']]['onDelay'] = rf['onDelay']
        trs[rf['triggerName']]['offDelay'] = rf['offDelay']
        trs[rf['triggerName']]['repeatDelay'] = rf['repeatDelay']



        
        #ff = open('triggers.csv','w')
    ##Trigger Name, Min Temp, Max Temp, Image Percent, On Delay, Off Delay, Repeat Delay
        #ff.write('\n' + rf['triggerName'] + ', ')
        #ff.write(rf['minTemp'] + ', ')
        #ff.write(rf['maxTemp'] + ', ')
        #ff.write(rf['imgPercent'] + ', ')
        #ff.write(rf['onDelay'] + ', ')
        #ff.write(rf['offDelay'] + ', ')
        #ff.write(rf['repeatDelay'] + ', ')
        #ff.close()
        
        
    return redirect(url_for('triggers'))
        
def start_runner():
    def start_loop():
        not_started = True
        while not_started:
            print('In start loop')
            try:
                r = requests.get('http://127.0.0.1:5000/')
                if r.status_code == 200:
                    print('Server started, quiting start_loop')
                    not_started = False
                print(r.status_code)
            except:
                print('Server not yet started')
            time.sleep(2)

    print('Started runner')
    thread = threading.Thread(target=start_loop)
    thread.start()

if __name__ == "__main__":
    start_runner()
    app.run()
