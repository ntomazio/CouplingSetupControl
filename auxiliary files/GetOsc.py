# -*- coding: utf-8 -*-
"""
Created on Mon August 5 12:00:00 2019

@author: Paulo Jarschel
"""

import os
import time
import threading
import numpy as np
import matplotlib.pyplot as plt
# import oscDSOX3104A
import oscAglDSO9404A


# ---- Wrap as class to facilitate threaded loop (avoid globals) ---- #
class Measure:
    # ---- Definitions ---- #
    # Change these
    filedir = "C:\\Users\\Vagner\\Documents\\Erick\\Mode_conversion_HOM\\2019-09-11\\"
    filename = "1219_2617_-45_POn.txt"
    # filename = "file_st400_pmp500_stokes_pumpON_1450_2720.txt"

    # Choose one oscilloscope
    # osc = oscDSOX3104A.OSCDSOX3104A()  # DSOX3104 = 1GHz, small
    osc = oscAglDSO9404A.OSCDSO9404A()  # DSO9404 = 4GHz, big

    # Oscilloscope parameters
    osc_channels = [1, 2, 3, 4]
    channels_to_plot = [1]
    main_channel = 1

    # Internal
    oscstart = 0
    oscstop = 0
    oscy = []
    oscx = []

    fig = None
    axspec = None

    def __init__(self):
        self.initdevicess()
        self.prepare()
        self.prepareplots()

    def __del__(self):
        self.close()

    # ---- Create/init devices ---- #
    def initdevicess(self):
        self.osc.connectOSC()
        time.sleep(0.1)
        self.osc.initOSC(binarymode=True)
        time.sleep(0.1)
        tscale = self.osc.getTimeScale()
        tf = 10 * tscale
        self.osc.osc.timeout = 10 * 1000 * tf

    # ---- Prepare ---- #
    def prepare(self):
        pass

    # ---- Prepare plots ---- #
    def prepareplots(self):
        self.fig, self.axspec = plt.subplots(1, 1)
        self.axspec.set_xlabel("Time (s)")
        self.axspec.set_ylabel("Voltage (V)")
        self.axspec.set_title("Stokes")
        self.fig.tight_layout()

    # ---- Measure Loop ---- #
    def startloop(self):
        # print("Loop started")
        self.startmeas()

    # Measure
    def startmeas(self):
        self.oscy = []
        self.oscx = []

        self.osc.single()
        self.measure()

    def measure(self):
        if self.osc.singleFinished(self.main_channel):
            self.oscstart = self.osc.getStartTime()
            self.oscstop = self.osc.getStopTime()
            self.oscy = []
            for c in range(len(self.osc_channels)):
                self.oscy.append(self.osc.getData(self.osc_channels[c]))
            self.oscx = np.linspace(self.oscstart, self.oscstop, len(self.oscy[0]))

            self.savespecs(self.oscx, self.oscy)
            self.updateplots()

        else:
            timer = threading.Timer(0.1, self.measure)
            timer.start()

    # Plot
    def updateplots(self):
        # print("Plotting")
        self.axspec.clear()

        for channel in self.channels_to_plot:
            i = self.osc_channels.index(channel)
            if i < len(self.oscy):
                self.axspec.plot(self.oscx, self.oscy[i])
            else:
                self.axspec.plot(self.oscx, np.zeros([len(self.oscx)]))

        self.axspec.set_xlabel("Time (s)")
        self.axspec.set_ylabel("Voltage (V)")

        # self.fig.tight_layout()
        # plt.pause(0.001)
        plt.draw()

    def savespecs(self, x, y):
        filepath = self.filedir + self.filename
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as file:
            file.write("Time (s)")
            for c in range(len(y)):
                file.write(f"\tChannel{self.osc_channels[c]}")
            file.write("\n")

            for i in range(len(x)):
                file.write(f"{x[i]:.5f}")
                for c in range(len(y)):
                    file.write(f"\t{y[c][i]:.5f}")
                file.write("\n")
            file.close()

    def close(self):
        # ---- Close devices ---- #
        # self.pm.close()
        # self.osc.closeOSC()
        # self.edfa_pump.closeEDFA()
        # self.edfa_stokes.closeEDFA()
        pass


# ---- Create measure object and start measurement ---- #
measmnt = Measure()
measmnt.startloop()

# ---- Show Plots ---- #
plt.show()
