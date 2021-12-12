"""
Created on December 2021

@author: Nathalia Tomazio (nathalia.tomazio@alumni.usp.br) with insights from Paulo Jarschel

"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import oscDSOX3104A # oscilloscope 1GHz
# import oscAglDSO9404A # oscilloscope DSO9404 = 4GHz, big
import agilent816xb # laser
import controller # NI DAQ
import pickle
import keithley2400 # current controller for the heaters
import time
import sys

# --- define the objects for the laser, oscilloscope, and current controller --- #
laser = agilent816xb.Agilent816xb()  # laser 
# use the scope to real time visualization of the laser scan
osc = oscDSOX3104A.OSCDSOX3104A()  # DSOX3104A = 1GHz
keithley = keithley2400.Keithley2400SM() # current controller

#--- Initial config for the laser scan, scope visualization and DAQ acquisition ---#
# change these
scan_speed = 5 # in nm/s
wth_i = 1530 # start wavelength in nm - min 1450 nm
wth_f = 1570 # stop wavelength in nm - max 1650 nm
scan_time = (wth_f-wth_i)/scan_speed

laser.connectlaser()
laser.setState(0,1)
laser.setOutputTrigger(0,1,mode="SWST")
laser.setSweepState(0,"Stop") # just to ensure that the laser sweep from a previous run has been stopped before the next sweep starts
laser.setSweep(0,"CONT", wth_i, wth_f, 1, 0, 0, scan_speed)
laser.setPwr(0,7) # in dBm

#--- Initial config for the oscilloscope ---#
osc.connectOSC()
osc.stop() # just to restart the scope waveforms 

# laser.setSweepState(0,"Start") # enable the laser sweep 

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

#--- Initial config for the DAQ acquisition ---#
numChan = 4 #number of channels in DAQ
sampRate = 400e3/numChan

task = controller.Task()
task.add_channel("Dev1/ai0")    # laser trigger
task.add_channel("Dev1/ai1")    # cavity transmission
task.add_channel("Dev1/ai2")    # acetylene
task.add_channel("Dev1/ai3")    # mzi


# --- Config for the current controller (keithley) ---#
keithley.connectSM()
keithley.conf_apply_current()
# change this
keithley.set_compliance_voltage(10) # initialize the compliance voltage [Volts]

# --- Define important functions ---#

# --- Define function to measure the resistence ---#
def measResistence(curr, wait=2):
    """
    Measure resistence given a current level
        input:
            curr: current [mA] 
            wait: time for the temperature to stabilize [seconds] 
        output:
            resistence: [Ohm]
            dissipated power: [mW]
    """
    # initialize variables
    cond = 1
    tol = 0.01
    R = 0
    stdR = 0
    Power = 0

    # define the number of measurements taken to compute the averaged resistence
    Nmean = 10 

    keithley.set_source_current(curr*1e-3) # set a current in A
    time.sleep(wait) # wait for the temperature to stabilize 

    while cond > tol:
        # take the averaged resistence value      
        res = []
        for ii in range(Nmean):
            res.append(keithley.get_ohms()) # get the resistence in Ohm

        if abs(np.mean(res)) < 1e3: # if the resistence is smaller than 1k Ohm -> True
            cond = np.std(res)/np.mean(res)
            if cond < tol:
                R = np.mean(res)
                stdR = np.std(res)
                Power = (curr*1e-3)**2/np.mean(res)*1e3 # in mW
            else:
                print(f"resistence fluctuation measured @ {curr} mA is beyond toleration")
        else:
            print("no electrical contact - make sure the probes are touching the pads")
            sys.exit() # stop the code
    
    print(f"resistence @ {curr} mA is {R:.2f} +/- {stdR:.2f} Ohm")
    return R, Power


# --- define function to check whether the time delay is enough to acquire the resistence ---#
def CheckTime(curr=10,maxtime=20):
    """
    Check if the time to wait before resistence acquisition is enough
        input:
            curr: current [mA] 
            maxtime: max amount of time to be tested [seconds] 
        output:
           plot of the resistence vs wait time
    """
    I = curr*1e-3

    R = []
    wait = [i for i in range(maxtime+1)]
    for t in wait:
        keithley.set_source_current(I)
        time.sleep(t)
        print(f"{t} s")

        # take the averaged resistence value     
        res = []
        for ii in range(Nmean):
            res.append(keithley.get_ohms())
        R.append(np.mean(res))  

        keithley.set_source_current(0) 
        time.sleep(t) 

    plt.plot(wait, R, '-o')
    plt.xlabel("delay (s)")
    plt.ylabel("Resistence (Ohm)")
    plt.show()


# --- define function to plot power vs current ---#
def plotPwr(maxCurr, step, plot=True):
    """
    Plot power, resistence vs current curves for checking purposes
        input:
            maxCurr: max current for the plot [mA] 
            step: current increment for the plot [mA] 
        output:
           plot of the power, resistence vs current
    """
    current = [i for i in range(0,maxCurr+step,step)] # current list in mA

    # initialize variables
    R = []
    stdR = []
    Power = []

    for curr in current:
        res, pwr = measResistence(curr)
        R.append(res)
        stdR.append(res)
        Power.append((curr*1e-3)**2/res*1e3) # in mW
    
    keithley.set_source_current(0) # in A

    if plot:
        fig, ax = plt.subplots(2, sharex=True)
        ax[0].plot(current, R,'-o')
        ax[1].plot(current, Power, '-o')
        ax[1].set_xlabel("current (mA)")
        ax[0].set_ylabel("Resistence (Ohm)")
        ax[1].set_ylabel("Power (mW)")
        fig.tight_layout()
        plt.show()


# --- Set the compliance voltage - max voltage the source can apply to meet the current requested by the user ---#
# change these
maxCurr = 25 # in mA

R, MaxPower = measResistence(maxCurr)
maxVolt = R*maxCurr*1e-3 # in Volts 
keithley.set_compliance_voltage(np.ceil(maxVolt)+1) 
print(f"cmpl voltage is set to {np.ceil(maxVolt)+1} V")
keithley.set_source_current(0) # in A


# --- built a linearly spaced power vector ---#
# change these
step = 20
# PotLinear = np.linspace(0,round(MaxPower,3), step) # linearly spaced vector with dissipated power levels in mW
PotLinear = np.linspace(0, MaxPower, step)


# --- Obtain a current vector to meet the linearly spaced dissipated power vector and save the spectra ---#

# initialize variables
resGuess = R # resistence guess to calculate the current needed to meet the intended power
resistence = []
current = []
i = 0
wait = 2

# scan the power levels 
for p in PotLinear[0:5]:
    if p == 0:
        R, curr, Power = (0,0,0) # take the averaged resistence value 
    else:
        while np.abs(p-Power)/p > 0.01:  
            curr = np.sqrt(p*1e-3*resGuess)*1e3 # calculate current in mA 
            R, Power = measResistence(curr) # take the averaged resistence value 

            resGuess = R # update the resistence guess
            print(f"for iteraction # {i}, calculated power is off the target by {np.abs(p-Power)/p}")

    resistence.append(R)
    current.append(curr) 

    keithley.set_source_current(curr*1e-3) # set current in A
    time.sleep(wait) # wait for the temperature to stabilize
    
    laser.setSweepState(0,"Start") # enable the laser sweep

    # save spectrum 
    task.acquisition_mode = 'N Samples'
    task.rate = sampRate
    task.samples = int(sampRate*(scan_time+2))
    task.timeout = 1.5*scan_time
    print(f"Sampling rate: {sampRate} Pts/s")
    print(f"Trace length: {int(sampRate*(scan_time+2))}")
    task.config()
    r = task.read()
    task.close()

    laser.setSweepState(0,"Stop") # enable the laser sweep

    plot = False
    if plot:
        plt.plot(-0.25+r[0,:]/20, label = "laser trigger")
        plt.plot(0.9+r[1,:],label = "cav")
        plt.plot(0.5+r[2,:], label = "acetylene")
        plt.plot(r[3,:]/10, label = "MZI")
        # plt.legend()
        plt.show()

    df = pd.DataFrame({'trigger_laser': r[0,:], 'cav': r[1,:], 'acetylene': r[2,:], 'mzi': r[3,:]})
    # df.hvplot.line(y=['cav','acetylene','mzi'], width=1000, height=300, datashade=True, hover=False))

    # change these
    filedir = 'C:\\Users\\Lab\\Documents\\Nathalia Tomazio\\python codes\\transmission data\\C-band_heater control\\'
    filename = 'test_10DEZ21_chip2_R-2R-R_wg-ring gap 600 nm_ring-ring gap 500 nm_TE_heater1_'
    if i<10:
        compl = f'0{i}_{curr*1e3:.2f}mA_{p:.2e}mW'
    else:
        compl = f'{i}_{curr*1e3:.2f}mA_{p:.2e}mW'
    filepath = filedir + filename + compl
    print('saved data: '+filepath+'.pkl')
    # df.to_parquet(filepath+'.parq', compression='brotli')
    picklefile = open(f"{filepath}.pkl", 'wb')
    pickle.dump(df, picklefile)

    picklefile.close()

    i = i+1


#--- Save the heater power and current to a cvs file ---#
df0 = pd.DataFrame({'heater power (mW)': PotLinear[0:5], 'resistence (Ohm)': resistence, 'current (mA)': current})

save = True
if save: 
    filedir = 'C:\\Users\\Lab\\Documents\\Nathalia Tomazio\\python codes\\transmission data\\C-band_heater control\\'
    #change this
    filename = f'test_08DEZ21_chip2_R-2R-R_wg-ring gap 600 nm_ring-ring gap 500 nm_TE_heater1'
    filepath = filedir + filename
    df0.to_csv(filepath+'.csv')



# #--- Scan the current vector and save the spectra ---#
# i = 0
# for curr in current:
#     keithley.set_source_current(curr) # set current in A
#     time.sleep(wait) # wait for the temperature to stabilize
    
#     laser.setSweepState(0,"Start") # enable the laser sweep

#     # save spectrum 
#     task.acquisition_mode = 'N Samples'
#     task.rate = sampRate
#     task.samples = int(sampRate*(scan_time+2))
#     task.timeout = 1.5*scan_time
#     print(f"Sampling rate: {sampRate} Pts/s")
#     print(f"Trace length: {int(sampRate*(scan_time+2))}")
#     task.config()
#     r = task.read()
#     task.close()

#     laser.setSweepState(0,"Stop") # enable the laser sweep

#     plot = False
#     if plot:
#         plt.plot(-0.25+r[0,:]/20, label = "laser trigger")
#         plt.plot(0.9+r[1,:],label = "cav")
#         plt.plot(0.5+r[2,:], label = "acetylene")
#         plt.plot(r[3,:]/10, label = "MZI")
#         # plt.legend()
#         plt.show()

#     df = pd.DataFrame({'trigger_laser': r[0,:], 'cav': r[1,:], 'acetylene': r[2,:], 'mzi': r[3,:]})
#     # df.hvplot.line(y=['cav','acetylene','mzi'], width=1000, height=300, datashade=True, hover=False))

#     # change these
#     filedir = 'C:\\Users\\Lab\\Documents\\Nathalia Tomazio\\python codes\\transmission data\\C-band_heater control\\'
#     if i<10:
#         filename = f'08DEZ21_chip2_R-2R-R_wg-ring gap 800 nm_ring-ring gap 500 nm_TM_heater1_0{i}_{curr*1e3:.2f}mA_{PotLinear[i]:.2e}mW'
#     else:
#         filename = f'08DEZ21_chip2_R-2R-R_wg-ring gap 800 nm_ring-ring gap 500 nm_TM_heater1_{i}_{curr*1e3:.2f}mA_{PotLinear[i]:.2e}mW'
#     filepath = filedir + filename
#     print('saved data: '+filepath+'.pkl')
#     # df.to_parquet(filepath+'.parq', compression='brotli')
#     picklefile = open(f"{filepath}.pkl", 'wb')
#     pickle.dump(df, picklefile)

#     picklefile.close()

#     i = i+1
    
keithley.set_source_current(0) # set current in A
