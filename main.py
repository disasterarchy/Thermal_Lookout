from flask import Flask
import requests
import threading
from basic_hist import *
import numpy
import cv2

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'
    
@app.route('/temp')
def Get_Temps():
	mn, mx, rw, im = GetData()
	OutputText = "Min:  " + str(mn) + "\n <br>Max:  "+ str(mx)
	return OutputText

@app.route('/user/<username>')
def show_user_profile(username):
    n = open('hi.txt','w')
    n.write('hello '+username)
    n.close()
    # show the user profile for that user
    return 'User %s' % username

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id
  
@app.route('/data/current.jpg')
def CurrentImage():
	#imm = cv2.imread("test.jpg")
	mn, mx, rw, imm = GetData()
	#basic_hist.MakeHistogram(rw)
	buf = cv2.imencode(".jpg",imm)
	resp = Flask.make_response(app, buf[1].tostring())
	resp.content_type = "image/jpeg"
	return resp
@app.route('/data/pretty.jpg')
def PrettyImage():
	#imm = cv2.imread("test.jpg")
	mn, mx, rw = GetDataFast(False)
	t={}
	t['minTempF'] = 85
	t['maxTempF'] = 95
	t['nOn']=1
	t['name']='Erik'
	t['pctInRange'] = 0.15
	imm = MakeItPretty(rw,t,mn,mx)
	#basic_hist.MakeHistogram(rw)
	buf = cv2.imencode(".jpg",imm)
	resp = Flask.make_response(app, buf[1].tostring())
	resp.content_type = "image/jpeg"
	return resp
    
@app.before_first_request
def activate_job():
    def run_job():
        while True:
            print("Run recurring task")
            time.sleep(3)

    thread = threading.Thread(target=run_job)
    thread.start()


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

start_runner()

if __name__ == "__main__":
    start_runner()
    app.run()
