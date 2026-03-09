import sys
import time
import threading
import numpy as np
import websocket
import csv
import os

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter

import firebase_admin
from firebase_admin import credentials, db


########################################
# CONFIG
########################################

ESP_IP = "10.137.252.50"

DATABASE_URL = "https://battery-gas-detection-default-rtdb.asia-southeast1.firebasedatabase.app/"

SCROLL_WINDOW = 20

SAVE_FOLDER="data"
os.makedirs(SAVE_FOLDER,exist_ok=True)


########################################
# FIREBASE
########################################

cred=credentials.Certificate(r"C:\Users\Hiteshi\OneDrive - iitgn.ac.in\Desktop\ATET\key.json.json")

firebase_admin.initialize_app(cred,{
'databaseURL':DATABASE_URL
})


########################################
# STATE
########################################

times=[]

H2O=[]
CO2=[]
CO=[]

sessionTimes=[]
sessionH2O=[]
sessionCO2=[]
sessionCO=[]

running=False
connected=False

ws=None

status_text="Finding ESP IP address..."

lock=threading.Lock()


########################################
# FILTER
########################################

filter_on=False
filter_window=5


def movingAvg(x,n):

    if len(x)<n:
        return x

    kernel=np.ones(n)/n

    return np.convolve(x,kernel,mode='same')


########################################
# SAMPLE RATE TRACKING
########################################

sample_counter=0
sample_rate=0
last_rate_time=time.time()


########################################
# WEBSOCKET
########################################

def on_message(wsapp,msg):

    global status_text
    global sample_counter

    try:

        h2o,co2,co=map(int,msg.split(","))

        t=time.time()

        with lock:

            times.append(t)
            H2O.append(h2o)
            CO2.append(co2)
            CO.append(co)

            if running:

                sessionTimes.append(t)
                sessionH2O.append(h2o)
                sessionCO2.append(co2)
                sessionCO.append(co)

        sample_counter+=1

        status_text="Streaming"

    except:
        pass


def on_open(wsapp):

    global connected,status_text

    connected=True

    status_text="Connected"


def on_close(wsapp,a,b):

    global connected,status_text

    connected=False

    status_text="Disconnected"



########################################
# CONNECTION THREAD
########################################

def connectionLoop():

    global ws,status_text

    while True:

        status_text="Connecting to ESP..."

        try:

            ws=websocket.WebSocketApp(
                f"ws://{ESP_IP}:81",
                on_message=on_message,
                on_open=on_open,
                on_close=on_close
            )

            ws.run_forever()

        except:

            status_text="Reconnect..."

        time.sleep(2)


########################################
# GUI
########################################

class Dashboard(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
        "Li-Ion Battery Gas Detection System")

        self.resize(1500,900)

        main=QVBoxLayout()

        central=QWidget()
        central.setLayout(main)

        self.setCentralWidget(central)


        ##################################
        # TITLE BAR
        ##################################

        top=QHBoxLayout()

        title=QLabel(
        "Li-Ion Battery Gas Detection System")

        title.setStyleSheet("font-size:24px")

        self.light=QLabel("●")
        self.light.setStyleSheet(
        "font-size:30px;color:red")

        self.rateLabel=QLabel("Rate: 0 Hz")

        top.addWidget(title)

        top.addStretch()

        top.addWidget(self.rateLabel)
        top.addWidget(QLabel("ESP"))
        top.addWidget(self.light)

        main.addLayout(top)


        ##################################
        # PLOTS
        ##################################

        grid=QGridLayout()
        main.addLayout(grid)

        self.plotH2O=pg.PlotWidget(title="H₂O")
        self.plotCO2=pg.PlotWidget(title="CO₂")
        self.plotCO=pg.PlotWidget(title="CO")

        grid.addWidget(self.plotH2O,0,0)
        grid.addWidget(self.plotCO2,0,1)
        grid.addWidget(self.plotCO,1,0)

        self.curveH2O=self.plotH2O.plot(pen='y')
        self.curveCO2=self.plotCO2.plot(pen='c')
        self.curveCO=self.plotCO.plot(pen='m')


        ##################################
        # CONTROLS
        ##################################

        controls=QHBoxLayout()

        self.startBtn=QPushButton("Start")
        self.stopBtn=QPushButton("Stop")

        self.newBtn=QPushButton("New Session")

        self.uploadBtn=QPushButton("Upload")

        self.csvBtn=QPushButton("Download CSV")
        self.jpgBtn=QPushButton("Download JPG")

        self.zoomBtn=QPushButton("Reset Zoom")

        controls.addWidget(self.startBtn)
        controls.addWidget(self.stopBtn)
        controls.addWidget(self.newBtn)

        controls.addWidget(self.uploadBtn)
        controls.addWidget(self.csvBtn)
        controls.addWidget(self.jpgBtn)
        controls.addWidget(self.zoomBtn)


        ##################################
        # FILTER
        ##################################

        self.filterToggle=QCheckBox("Average Filter")

        self.filterBox=QSpinBox()

        self.filterBox.setValue(5)
        self.filterBox.setMinimum(1)
        self.filterBox.setMaximum(200)

        controls.addWidget(self.filterToggle)
        controls.addWidget(QLabel("Window"))
        controls.addWidget(self.filterBox)


        ##################################
        # AUTO SCROLL
        ##################################

        self.scrollToggle=QCheckBox("Auto Scroll")
        self.scrollToggle.setChecked(True)

        controls.addWidget(self.scrollToggle)

        main.addLayout(controls)


        ##################################
        # STATUS
        ##################################

        self.statusLabel=QLabel(status_text)

        main.addWidget(self.statusLabel)


        ##################################
        # EVENTS
        ##################################

        self.startBtn.clicked.connect(self.start)
        self.stopBtn.clicked.connect(self.stop)

        self.newBtn.clicked.connect(self.newSession)

        self.uploadBtn.clicked.connect(self.upload)
        self.csvBtn.clicked.connect(self.saveCSV)

        self.jpgBtn.clicked.connect(self.saveJPG)

        self.zoomBtn.clicked.connect(self.resetZoom)

        self.filterToggle.stateChanged.connect(self.filterChanged)
        self.filterBox.valueChanged.connect(self.filterChanged)


        ##################################
        # TIMERS
        ##################################

        self.timer=QTimer()
        self.timer.timeout.connect(self.updatePlots)
        self.timer.start(40)

        self.rateTimer=QTimer()
        self.rateTimer.timeout.connect(self.updateRate)
        self.rateTimer.start(1000)


    ################################

    def updateRate(self):

        global sample_counter,sample_rate

        sample_rate=sample_counter
        sample_counter=0

        self.rateLabel.setText(
        f"Rate: {sample_rate} Hz")


    ################################

    def start(self):

        global running

        if connected:

            ws.send("START")
            running=True


    ################################

    def stop(self):

        global running

        ws.send("STOP")
        running=False


    ################################

    def newSession(self):

        with lock:

            times.clear()
            H2O.clear()
            CO2.clear()
            CO.clear()

            sessionTimes.clear()
            sessionH2O.clear()
            sessionCO2.clear()
            sessionCO.clear()


    ################################

    def upload(self):

        global status_text

        if running:
            status_text="Stop session first"
            return

        if len(sessionH2O)==0:
            status_text="No data to upload"
            return

        status_text="Uploading..."

        # Session name
        session_name=time.strftime("%Y-%m-%d_%H-%M-%S")

        ref=db.reference(session_name)

        ref.set({

            "h2o":sessionH2O,
            "co2":sessionCO2,
            "co":sessionCO,
            "timestamps":sessionTimes

        })

        status_text="Upload Complete"


    def saveCSV(self):

        global status_text

        if running:
            status_text="Stop session first"
            return

        name=time.strftime("%Y%m%d_%H%M%S")+".csv"

        path=os.path.join(SAVE_FOLDER,name)

        with open(path,'w',newline='') as f:

            w=csv.writer(f)

            w.writerow(["time","H2O","CO2","CO"])

            for i in range(len(sessionH2O)):

                w.writerow([
                    sessionTimes[i],
                    sessionH2O[i],
                    sessionCO2[i],
                    sessionCO[i]
                ])

        status_text="Saved "+path


    ################################

    def saveJPG(self):

        global status_text

        name=time.strftime("%Y%m%d_%H%M%S")+".jpg"

        path=os.path.join(SAVE_FOLDER,name)

        pixmap=self.grab()

        pixmap.save(path,"JPG")

        status_text="Saved "+path


    ################################

    def resetZoom(self):

        self.plotH2O.enableAutoRange()
        self.plotCO2.enableAutoRange()
        self.plotCO.enableAutoRange()


    ################################

    def filterChanged(self):

        global filter_on,filter_window,status_text

        filter_on=self.filterToggle.isChecked()

        filter_window=self.filterBox.value()

        if filter_on:
            status_text=f"Filter ON ({filter_window})"
        else:
            status_text="Filter OFF"


    ################################

    def updatePlots(self):

        with lock:

            t=np.array(times)
            a=np.array(H2O)
            b=np.array(CO2)
            c=np.array(CO)

        if len(t)==0:
            return

        t=t-t[0]

        if filter_on:

            a=movingAvg(a,filter_window)
            b=movingAvg(b,filter_window)
            c=movingAvg(c,filter_window)

        self.curveH2O.setData(t,a)
        self.curveCO2.setData(t,b)
        self.curveCO.setData(t,c)


        if self.scrollToggle.isChecked():

            xmax=t[-1]
            xmin=max(0,xmax-SCROLL_WINDOW)

            self.plotH2O.setXRange(xmin,xmax)
            self.plotCO2.setXRange(xmin,xmax)
            self.plotCO.setXRange(xmin,xmax)


        self.statusLabel.setText(status_text)

        color="lime" if connected else "red"

        self.light.setStyleSheet(
        f"font-size:30px;color:{color}"
        )


########################################
# START THREAD
########################################

threading.Thread(
target=connectionLoop,
daemon=True
).start()


########################################
# RUN
########################################

pg.setConfigOption('background','#0b1a24')
pg.setConfigOption('foreground','w')

app=QApplication(sys.argv)

win=Dashboard()

win.show()

sys.exit(app.exec())
