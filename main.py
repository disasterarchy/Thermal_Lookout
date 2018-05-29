from flask import Flask
from multiprocessing import Process, Queue, Pipe
import basic_hist
import numpy
import cv2

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'
    
@app.route('/temp')
def Get_Temps():
	mn, mx, rw, im = basic_hist.GetData()
	OutputText = "Min:  " + str(mn) + "\n <br>Max:  "+ str(mx)
	return OutputText

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id
  
@app.route('/data/current.jpg')
def CurrentImage():
	#imm = cv2.imread("test.jpg")
	mn, mx, rw, imm = basic_hist.GetData()
	basic_hist.MakeHistogram(rw)
	buf = cv2.imencode(".jpg",imm)
	resp = Flask.make_response(app, buf[1].tostring())
	resp.content_type = "image/jpeg"
	return resp
