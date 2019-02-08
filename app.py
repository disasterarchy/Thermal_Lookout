from config import UnitsC, f_triggers
from T_Loop import *
from flask import Flask
from flask import render_template, Response, request, redirect, url_for
from subprocess import call
# Raspberry Pi camera module (requires picamera package)
#from camera_pi import pCamera

#from camera_pi import Camera

app = Flask(__name__)

#@app.before_first_request
#def activate_job():
    #def run_job():
    #    while True:
    #        print("Run recurring task")
    #        time.sleep(3)
    
##    thread = threading.Thread(target=MainLoop)
##    thread.start()

@app.route("/")
def hello():
    return "Hello World!"

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/vvideo_feed')
def vvideo_feed():
    """Video streaming route."""
    return Response(gen(pCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/data/current.jpg')
def CurrentImage():
        mn, mx, rw, imm = GetData()
        buf = cv2.imencode(".jpg",imm)
        resp = Flask.make_response(app, buf[1].tostring())
        resp.content_type = "image/jpeg"
	return resp

@app.route('/triggers')
def triggers():

    return render_template('triggers.html', triggers=trs.values(), url='me')

@app.route('/log')
def log():
    try:
        ff = open('static/archive/log.csv')
        lines = ff.readlines()
        ff.close()
    except:
        return "Couldn't open log!"
    return render_template('log.html', lines=lines[:-15:-1])

@app.route('/control')
def control():
    return render_template('control.html', url=web_url)


@app.route('/status')
def status(name=None):
    return render_template('status.html')

@app.route('/update', methods=['POST','GET'])
def update():
    action = request.form['submit']
    rf = request.form

    #with open('trs.pickle', 'rb') as handle:
    #            trs=  pickle.load(handle)
                
    if action == "Delete":
        print "DELETE"
        print rf['triggerName']
        try:
            del trs[rf['triggerName']]
        except:
            print "already deleted!"
      
    #if action == "Save":
    #    trs[rf['name']]['name'] = rf['name']
    #    trs[rf['name']]['minTemp'] = rf['minTemp']

    else:
        trs[rf['triggerName']]={}
    #   print "Add"
    #    print(request.form['name'])
    #    print(request.form)
        #trs[rf['name']] = request.form['name']
    
        trs[rf['triggerName']]['name'] = rf['triggerName']
        trs[rf['triggerName']]['minTemp'] = float(rf['minTemp'])
        trs[rf['triggerName']]['maxTemp'] = float(rf['maxTemp'])
        trs[rf['triggerName']]['pct'] = float(rf['imgPercent'])
        trs[rf['triggerName']]['delayOn'] = float(rf['onDelay'])
        trs[rf['triggerName']]['delayOff'] = float(rf['offDelay'])
        trs[rf['triggerName']]['delayRepeat'] = float(rf['repeatDelay'])
        trs[rf['triggerName']]['nOff']=0
        trs[rf['triggerName']]['nOn']=0
        trs[rf['triggerName']]['nRepeat']=9E+9

        with open('trs.pickle', 'wb') as handle:
            pickle.dump(trs, handle, protocol=pickle.HIGHEST_PROTOCOL)

        
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

@app.route('/ctrl', methods=['POST','GET'])
def ctrl():
    print 'Entered ctrl'
    rf = request.form
    print rf
    
    action = rf['submit']
    
    print rf['password']
    if rf['password'] == 'qwerty':
                
        if action == "Shutdown":
            print 'Shutting down'
            call("sudo shutdown -h now", shell=True)
            return "Restarting now..."
        if action == "Restart":
            call("sudo shutdown -r now", shell=True)
            return "Shutting down..."

        if action == "Delete Logs":
            call("sudo ./delete_logs.sh", shell=True)
            return "Deleting logs..."

        if action == "Submit":
            try:
                fff = open('web_url.txt','w')
                fff.write(rf['url'])
                fff.close()
                return "Updated IFTTT URL.  Restart for changes to take effect"
            except:
                return "Error updating url!"
    return "No action completed."
       
def start_runner():
    def start_loop():
        not_started = True
        while not_started:
            print('In start loop')
            try:
                r = requests.get('http://127.0.0.1:5000/video_feed')
                if r.status_code == 200:
                    print('Server started, quitting start_loop')
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
    app.run(host='0.0.0.0', threaded=True)
