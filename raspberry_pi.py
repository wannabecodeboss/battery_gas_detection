import sys
import time
import threading
import numpy as np
import serial
import csv
import os

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import pyqtgraph as pg

########################################
# CONFIG
########################################

SERIAL_PORT = "/dev/serial0"
BAUD = 115200

SCROLL_WINDOW = 20
SAVE_FOLDER = "data"
os.makedirs(SAVE_FOLDER, exist_ok=True)

########################################
# STATE
########################################

times = []
H2 = []
CO2 = []
CO = []
TEMP = []

running = False
connected = False

lock = threading.Lock()

########################################
# CALIBRATION
########################################

calibrating = False
calibrated = False

calib_data = {"h2": [], "co2": [], "co": [], "temp": []}
offsets = {"h2": 0, "co2": 0, "co": 0, "temp": 0}

########################################
# SERIAL THREAD
########################################

def serialLoop():
    global connected

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
        connected = True
    except:
        print("Serial connection failed")
        return

    while True:
        try:
            line = ser.readline().decode().strip()
            if not line:
                continue

            vals = list(map(int, line.split(",")))
            if len(vals) != 5:
                continue

            t_ms, h2, co2, co, temp = vals
            t = t_ms / 1000.0

            # apply offsets
            h2 -= offsets["h2"]
            co2 -= offsets["co2"]
            co -= offsets["co"]
            temp -= offsets["temp"]

            with lock:
                if calibrating:
                    calib_data["h2"].append(h2)
                    calib_data["co2"].append(co2)
                    calib_data["co"].append(co)
                    calib_data["temp"].append(temp)

                times.append(t)
                H2.append(h2)
                CO2.append(co2)
                CO.append(co)
                TEMP.append(temp)

        except:
            pass

########################################
# GUI
########################################

class Dashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Raspberry Pi Gas Monitor")
        self.resize(1400, 900)

        main = QVBoxLayout()
        central = QWidget()
        central.setLayout(main)
        self.setCentralWidget(central)

        ##################################
        # PLOTS
        ##################################

        grid = QGridLayout()
        main.addLayout(grid)

        self.plotH2 = pg.PlotWidget(title="H2")
        self.plotCO2 = pg.PlotWidget(title="CO2")
        self.plotCO = pg.PlotWidget(title="CO")
        self.plotTEMP = pg.PlotWidget(title="Temperature")

        grid.addWidget(self.plotH2, 0, 0)
        grid.addWidget(self.plotCO2, 0, 1)
        grid.addWidget(self.plotCO, 1, 0)
        grid.addWidget(self.plotTEMP, 1, 1)

        self.pie = pg.PlotWidget(title="Gas Ratio")
        grid.addWidget(self.pie, 2, 0, 1, 2)

        self.curveH2 = self.plotH2.plot(pen='y')
        self.curveCO2 = self.plotCO2.plot(pen='c')
        self.curveCO = self.plotCO.plot(pen='m')
        self.curveTEMP = self.plotTEMP.plot(pen='r')

        ##################################
        # CONTROLS
        ##################################

        controls = QHBoxLayout()

        self.startBtn = QPushButton("Start")
        self.stopBtn = QPushButton("Stop")
        self.calibBtn = QPushButton("Calibrate (5s)")

        controls.addWidget(self.startBtn)
        controls.addWidget(self.stopBtn)
        controls.addWidget(self.calibBtn)

        main.addLayout(controls)

        ##################################
        # STATUS
        ##################################

        self.status = QLabel("Not calibrated")
        main.addWidget(self.status)

        ##################################
        # EVENTS
        ##################################

        self.startBtn.clicked.connect(self.start)
        self.stopBtn.clicked.connect(self.stop)
        self.calibBtn.clicked.connect(self.calibrate)

        ##################################
        # TIMER
        ##################################

        self.timer = QTimer()
        self.timer.timeout.connect(self.updatePlots)
        self.timer.start(40)

    ################################

    def start(self):
        global running

        if not calibrated:
            self.status.setText("Calibrate first")
            return

        running = True
        self.status.setText("Running")

    def stop(self):
        global running
        running = False
        self.status.setText("Stopped")

    ################################

    def calibrate(self):
        global calibrating, calibrated, calib_data

        if running:
            self.status.setText("Stop first")
            return

        calib_data = {"h2": [], "co2": [], "co": [], "temp": []}
        calibrating = True
        calibrated = False

        self.status.setText("Calibrating...")

        def finish():
            global calibrating, calibrated, offsets

            calibrating = False

            offsets["h2"] = np.mean(calib_data["h2"])
            offsets["co2"] = np.mean(calib_data["co2"])
            offsets["co"] = np.mean(calib_data["co"])
            offsets["temp"] = np.mean(calib_data["temp"])

            calibrated = True
            self.status.setText("Calibrated")

        QTimer.singleShot(5000, finish)

    ################################

    def updatePlots(self):
        with lock:
            t = np.array(times)
            a = np.array(H2)
            b = np.array(CO2)
            c = np.array(CO)
            d = np.array(TEMP)

        if len(t) == 0:
            return

        self.curveH2.setData(t, a)
        self.curveCO2.setData(t, b)
        self.curveCO.setData(t, c)
        self.curveTEMP.setData(t, d)

        ################################
        # PIE CHART
        ################################

        if len(a) > 0:
            total = a[-1] + b[-1] + c[-1]

            if total > 0:
                ratios = [a[-1]/total, b[-1]/total, c[-1]/total]

                self.pie.clear()
                angles = np.cumsum([0] + ratios) * 360

                colors = ['y', 'c', 'm']

                for i in range(3):
                    theta = np.linspace(
                        np.deg2rad(angles[i]),
                        np.deg2rad(angles[i+1]),
                        100
                    )

                    x = np.cos(theta)
                    y = np.sin(theta)

                    self.pie.plot(
                        np.append([0], x),
                        np.append([0], y),
                        fillLevel=0,
                        brush=pg.mkBrush(colors[i])
                    )

########################################
# START SERIAL THREAD
########################################

threading.Thread(target=serialLoop, daemon=True).start()

########################################
# RUN
########################################

pg.setConfigOption('background', '#0b1a24')
pg.setConfigOption('foreground', 'w')

app = QApplication(sys.argv)
win = Dashboard()
win.show()
sys.exit(app.exec())
