from django.shortcuts import render
from django.http import HttpResponse,StreamingHttpResponse, HttpResponseServerError,HttpResponseRedirect

from django.views.decorators import gzip
from imutils.video import VideoStream
from imutils.video import FPS
import cv2
import time
import imutils
import math
import numpy as np
id_s = 0
line = 500
auth = False
def get_line():
    global line
    
    return line
def line_edit(r):
    global line
    line = r
    
def get_info(mas,box):
    global id_s
    d = 1000
    imas = 0
    info = []
   
    for i in range(len(mas)):
        #print((box[0]+box[2])/2  - (mas[i]['box'][0]+mas[i]['box'][2])/2)
        x = int(math.fabs((box[0]+box[2])/2 - (mas[i]['box'][0]+mas[i]['box'][2])/2))
        
        y = int(math.fabs((box[1]+box[3])/2 - (mas[i]['box'][1]+mas[i]['box'][3])/2))
        
        dn = int(math.sqrt(x*x + y*y))
        
        if dn < d:
            d = dn
            imas = i
   
    if d < 100:
        info.append(mas[imas]['id'])
        #print('заход if')
        speed = [0,0]
        speed[0] = (box[0]+box[2])/2 - (mas[i]['box'][0]+mas[i]['box'][2])/2
        speed[1] = (box[1]+box[3])/2 - (mas[i]['box'][1]+mas[i]['box'][3])/2
        info.append(speed)
        return info
    else:
        id_s+=1
        #print('заход елсе')
        info.append(id_s)
        info.append([0,0])
        return info
class VideoCamera(object):
    
    def __init__(self,path):
        #self.video = cv2.VideoCapture(path)
        self.video = VideoStream('00348.mts').start()
        self.last_obj = []
        self.sh = 0
        self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
	"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
	"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
	"sofa", "train", "tvmonitor"]
        
        
        self.COLORS = np.random.uniform(0, 255, size=(len(self.CLASSES), 3))
        self.net = cv2.dnn.readNetFromCaffe("MobileNetSSD_deploy.prototxt.txt", "MobileNetSSD_deploy.caffemodel")
       
        self.pipl_cross = []
    def __del__(self):
        self.video.read()

    def get_frame(self):
        frame = self.video.read()
        myrez = []
        LINE = get_line()
        frame = imutils.resize(frame, width=1000)
        (h,w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
        0.007843, (300, 300), 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()
        for i in np.arange(0, detections.shape[2]):
         confidence = detections[0, 0, i, 2]
         idx = int(detections[0, 0, i, 1])
         if confidence > 0.3 and idx == 15:
              obj ={}
              box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
              (startX, startY, endX, endY) = box.astype("int")
              label = "{}: {:.2f}%".format(self.CLASSES[idx],
                  confidence * 100)
              obj['label'] = self.CLASSES[idx]
              obj['box'] = [startX, startY,endX, endY]
              obj_inf = get_info(self.last_obj,obj['box'])
              obj['id']=  obj_inf[0]
              obj['speed'] = obj_inf[1]
              cv2.rectangle(frame, (startX, startY), (endX, endY),
		      (0,0,255), 2)
              y = startY - 15 if startY - 15 > 15 else startY + 15
              cv2.putText(frame, label +' ' + str(obj['id']), (startX, y),
              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
     
              myrez.append(obj)
      
              if obj['box'][1] < LINE and  obj['box'][3] > LINE and not(obj['id'] in self.pipl_cross):
                             self.sh+=1
                             self.pipl_cross.append(obj['id'])
                             f= open('othet.txt','a')
                             f.write(' id: ' + str(obj['id']) + ' time: ' + str(int(time.time())) + ' всего: ' + str(self.sh) + '\n')
                             f.close()
              del(obj)

        del(self.last_obj)
 
        cv2.putText(frame, str(self.sh) , (20,30),cv2.FONT_HERSHEY_SIMPLEX, 0.7,(0,255,0) , 3) 
        cv2.line(frame,(0,LINE),(2000,LINE ),(0,255,0),thickness=2)
 
        self.last_obj = []
        for j in range(len(myrez)):
                      self.last_obj.append(myrez[j])
        del(myrez)
       
        jpeg = cv2.imencode('.jpg',frame)[1].tostring()
        '''print(jpeg)
        j = jpeg.tobytes()
        print(j)'''
        return jpeg
    

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield(b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


def indexscreen(request): 
    try:
    
        template = "screens.html"
        return render(request,template)
    except HttpResponseServerError:
        print("aborted")
def changeline(request):
    global line
    print('-------------------------------------------')
    print(request)
    line = str(request).split('/')
    line = int(line[2])
    print(str(line))
    print('-------------------------------------------')
    return HttpResponseRedirect('/stream/screen')
@gzip.gzip_page
def dynamic_stream(request,num=0,stream_path="0"):
    
    stream_path = 'add your camera stream here that can rtsp or http'
    return StreamingHttpResponse(gen(VideoCamera(stream_path)),content_type="multipart/x-mixed-replace;boundary=frame")

