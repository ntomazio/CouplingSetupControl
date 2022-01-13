"""
Created on October 2021

@author: Nathalia Tomazio (nathalia.tomazio@alumni.usp.br) & Laís Fujii with insights from Paulo Jarschel

DAQ (max acquisition rate = 400 kSa/s) is used to acquire the data
Oscilloscope is used to view the data in real-time (it does not have the acquisition rate to properly resolve the SiN cavity resonances)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import oscDSOX3104A # oscilloscope 1GHz
# import oscAglDSO9404A # oscilloscope DSO9404 = 4GHz, big
import agilent816xb # laser
import pickle
import ivi # the code uses the ivi package only to acquire the waveform
import controller # NI DAQ
import random
from itertools import count
from matplotlib.animation import FuncAnimation

# --- define the objects for the laser and oscilloscope --- #
# change these
laser = agilent816xb.Agilent816xb()  # laser 
# use the scope to real time visualization of the laser scan
osc = oscDSOX3104A.OSCDSOX3104A()  # DSOX3104A = 1GHz
# scope = ivi.agilent.agilentDSOX3104A('USB0::0x0957::0x17A0::MY52490398::INSTR')  # DSOX3104A = 1GHz
# osc = oscAglDSO9404A.OSCDSO9404A()  # DSO9404 = 4GHz, big scope


# --- Initial config for the laser scan ---#
# change these
scan_speed = 5 # in nm/s
wth_i = 1554 # start wavelength in nm - min 1450 nm
wth_f = 1560 # stop wavelength in nm - max 1650 nm
scan_time = (wth_f-wth_i)/scan_speed

laser.connectlaser()
laser.setState(0,1)
laser.setOutputTrigger(0,1,mode="SWST")
laser.setSweepState(0,"Stop") # just to ensure that the laser sweep from a previous run has been stopped before the next sweep starts
laser.setSweep(0,"CONT", wth_i, wth_f, 1, 0, 0, scan_speed)
laser.setPwr(0,7) # in dBm

# --- Initial config for the oscilloscope ---#
# change these
# linewidth = 0.8e-3 # resonance linewidth in nm (110 MHz)
# linewidth_pts = 100 # sampling pts within a resonance linewidth 
# sampling_rate = scan_speed*linewidth_pts/linewidth
# print(sampling_rate)

osc.connectOSC()
osc.stop() # just to restart the scope waveforms 

laser.setSweepState(0,"Start") # enable the laser sweep 

osc.run()

osc.setTimeScale(scan_time/10)
osc.setStartTime(0) # scan_time/2
# osc.setSampRate(sampling_rate)
sampling_rate = osc.getSampRate()
sampling_pts = osc.getTraceLength()
# print(f"Sampling rate: {sampling_rate} Pts/s")
# print(f"Trace length: {sampling_pts}")

osc.setChannel(1,1) # trigger - laser TTL signal
osc.setEdgeTrigger(1, level=1000e-3) # level in V
osc.setChannel(2,1) # DUT signal
osc.setChannel(3,1) # acetylene
osc.setChannel(4,1) # MZI

numChan = 4 #number of channels in DAQ
sampRate = 400e3/numChan

task = controller.Task()
task.add_channel("Dev1/ai0")    # laser trigger
task.add_channel("Dev1/ai1")    # cavity transmission
task.add_channel("Dev1/ai2")    # acetylene
task.add_channel("Dev1/ai3")    # mzi

# dynamic plot config
plt.style.use('default')
# plt.style.use('fivethirtyeight')

# x_vals   = []
# y_vals_0 = []
# y_vals_1 = []
# y_vals_2 = []
# y_vals_3 = []

# index = count()

# def animate(i):
#     task.config()
#     r = task.read()
#     # x_vals.append(next(index))
#     # y_vals_1.append(random.randint(0, 5))
#     # y_vals_2.append(random.randint(0, 5))
#     y_vals_0 = r[0]
#     y_vals_1 = r[1]
#     y_vals_2 = r[2]
#     y_vals_3 = r[3]
#     plt.cla()

#     plt.plot(y_vals_0/y_vals_0.max(), label='laser trigger')
#     plt.plot(y_vals_1/y_vals_1.max(), label='cav')
#     plt.plot(y_vals_2/y_vals_2.max(), label='acetylene')
#     plt.plot(y_vals_3/y_vals_3.max(), label='mzi')
#     # plt.xlim([1, len(y_vals_0)])
#     # plt.ylim([-0.1, 6])
#     plt.legend(loc='upper left')


DAQ = True
if DAQ:
    DynamicPlot = False
    if DynamicPlot:
        task.acquisition_mode = 'Continuous Samples'
        task.rate = sampRate
        interval = 100
        task.samples = int(sampRate*1e-3*interval)
        ani = FuncAnimation(plt.gcf(), animate, interval=interval)
        plt.tight_layout()
        plt.show()
        task.close()
    else:
        task.acquisition_mode = 'N Samples'
        task.rate = sampRate
        task.samples = int(sampRate*(scan_time+2))
        task.timeout = 1.5*scan_time
        print(f"Sampling rate: {sampRate} Pts/s")
        print(f"Trace length: {int(sampRate*(scan_time+2))}")
        task.config()
        r = task.read()
        task.close()


    plot = True
    if plot:
        plt.plot(-0.25+r[0,:]/20, label = "laser trigger")
        plt.plot(0.9+r[1,:],label = "cav")
        plt.plot(0.5+r[2,:], label = "acetylene")
        plt.plot(r[3,:]/10, label = "MZI")
        # plt.legend()
        plt.show()

    df = pd.DataFrame({'trigger_laser': r[0,:], 'cav': r[1,:], 'acetylene': r[2,:], 'mzi': r[3,:]})
    # df.hvplot.line(y=['cav','acetylene','mzi'], width=1000, height=300, datashade=True, hover=False))

    # change this to false in case you do not want to save the file  
    save = False
    if save:
        # change these
        filedir = 'C:\\Users\\Lab\\Documents\\Nathalia Tomazio\\python codes\\transmission data\\broadband spectra\\'
        filename = 'test_02DEZ21_chip2_3 coupled rings R-2R-R_wg-ring gap 800 nm_ring-ring gap 750 nm_broadband_TM_through port'
        filepath = filedir + filename
        print('saved data: '+filepath+'.pkl')
        # df.to_parquet(filepath+'.parq', compression='brotli')
        picklefile = open(f"{filepath}.pkl", 'wb')
        pickle.dump(df, picklefile)
        picklefile.close()

