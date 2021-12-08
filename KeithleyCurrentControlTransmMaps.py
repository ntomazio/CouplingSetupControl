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

# change this
Nmean = 10 # number of measurements taken to compute the averaged resistence 


# --- Check whether the time delay is enough to acquire the resistence ---#
CheckTime = False
if CheckTime:
    keithley.conf_apply_current()
    keithley.set_compliance_voltage(10) # in Volts
     
    I = 10*1e-3 # provide the current in A

    R = []
    wait = [i for i in range(21)]
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

# change these
wait = 2 # in seconds, time delay for the temperature to stabilize 

# change these
maxCurr = 25 # in mA
step = 2 # in mA
curr = [i*1e-3 for i in range(0,maxCurr+step,step)] # current list in A


# --- Set the compliance voltage - max voltage the source can apply to meet the current requested by the user ---#
keithley.conf_apply_current()
keithley.set_compliance_voltage(10) # in Volts 
keithley.set_source_current(maxCurr*1e-3) 

time.sleep(wait) # wait for the temperature to stabilize 

# take the averaged resistence value 
maxRes = []
for ii in range(Nmean):
    maxRes.append(keithley.get_ohms()) # get the resistence in Ohms 
R = np.mean(maxRes)
stdR = np.std(maxRes)
print(f"resistence @ {maxCurr} mA (max current) =  {round(R,3)} +/- {round(stdR,3)} Ohms")

if R < 1e3: # if the resistence is smaller than 1k Ohm
    if stdR/R < 0.01:
        maxVolt = R*maxCurr*1e-3
        keithley.set_compliance_voltage(np.ceil(maxVolt)+1) # in Volts 
        print(f"cmpl voltage is set to {np.ceil(maxVolt)+1} V")
    else:
        print("resistence fluctuation is beyond toleration")
else: 
    print("no electrical contact - make sure the probes are touching the pads")


# --- Obtain the resistence and dissipated power as a function of current to ultimately built a linearly spaced power vector ---#
R = []
stdR = []
Power = []

curve = False 
if curve:
    for i in curr: 
        keithley.set_source_current(i) # in A
        if i == 0:
            R = [0]
            stdR = [0]
            Power = [0]
        else:
            time.sleep(wait) # wait for the temperature to stabilize 

            # take the averaged resistence value     
            res = []
            for ii in range(Nmean):
                res.append(keithley.get_ohms())

            if np.mean(res) < 1e3:
                if np.std(res)/np.mean(res) < 0.01:
                    R.append(np.mean(res))
                    stdR.append(np.std(res))
                    Power.append(i**2/np.mean(res)*1e3) # in mW
                else:
                    print(f"resistence fluctuation measured @ {i} A is beyond toleration")
            else:
                print("no electrical contact - make sure the probes are touching the pads")

    keithley.set_source_current(0) # in A

    plot = True
    if plot:
        fig, ax = plt.subplots(2, sharex=True)
        ax[0].plot(np.array(curr)*1e3, R,'-o')
        ax[1].plot(np.array(curr)*1e3, Power, '-o')
        ax[1].set_xlabel("current (mA)")
        ax[0].set_ylabel("Resistence (Ohm)")
        ax[1].set_ylabel("Power (mW)")
        fig.tight_layout()
        plt.show()

    MaxPower = Power[len(Power)-1] # in mW
    resGuess = np.mean(R[1::]) # resistence guess to calculate the current needed to meet the intended power

else: 
    keithley.set_source_current(maxCurr*1e-3) 
    time.sleep(wait) # wait for the temperature to stabilize 

    # take the averaged resistence value     
    res = []
    for ii in range(Nmean):
        res.append(keithley.get_ohms())

    if np.mean(res) < 1e3:
        if np.std(res)/np.mean(res) < 0.01:
            R = np.mean(res)
            stdR = np.std(res)
            MaxPower = (maxCurr*1e-3)**2/np.mean(res)*1e3 # in mW
        else:
            print(f"resistence fluctuation measured @ {maxCurr} mA is beyond toleration")
    else:
        print("no electrical contact - make sure the probes are touching the pads")

    keithley.set_source_current(0) # in A
    resGuess = R # resistence guess to calculate the current needed to meet the intended power


step = 20
PotLinear = np.linspace(0,round(MaxPower,3), step) # linearly spaced vector with dissipated power levels in mW


# --- Obtain a current vector to meet the linearly spaced dissipated power vector and save the spectra ---#
resistence = [0]
current = [0]
Power = 0
i = 0
for p in PotLinear[1::]:
    while np.abs(p-Power)/p > 0.01:  
        curr = np.sqrt(p*1e-3*resGuess) # calculate current in A 
        keithley.set_source_current(curr) # set current in A
        time.sleep(wait) # wait for the temperature to stabilize 

        # take the averaged resistence value     
        res = []
        for ii in range(Nmean):
            res.append(keithley.get_ohms())

        if np.mean(res) < 1e3:
            if np.std(res)/np.mean(res) < 0.01:
                R = np.mean(res)
                stdR = np.std(res)
                Power = curr**2/np.mean(res)*1e3 # in mW
            else:
                print(f"resistence fluctuation measured @ {curr} mA is beyond toleration")
        else:
            print("no electrical contact - make sure the probes are touching the pads")

        resGuess = R # update the resistence guess
        print(f"for iteraction # {i}, calculated power is off the target by {np.abs(p-Power)/p}")

    resistence.append(resGuess)
    current.append(np.sqrt(p*1e-3*resGuess)) # calculate current in A 

    i = i+1


#--- Save the heater power and current to a cvs file ---#
df0 = pd.DataFrame({'heater power (mW)': PotLinear, 'resistence (Ohm)': resistence, 'current (mA)': np.array(current)*1e3})

save = True
if save: 
    filedir = 'C:\\Users\\Lab\\Documents\\Nathalia Tomazio\\python codes\\transmission data\\C-band_heater control\\'
    #change this
    filename = f'08DEZ21_chip2_R-2R-R_wg-ring gap 800 nm_ring-ring gap 500 nm_TM_heater1'
    filepath = filedir + filename
    df0.to_csv(filepath+'.csv')



#--- Scan the current vector and save the spectra ---#
i = 0
for curr in current:
    keithley.set_source_current(curr) # set current in A
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
    filename = f'08DEZ21_chip2_R-2R-R_wg-ring gap 800 nm_ring-ring gap 500 nm_TM_heater1_{curr*1e3:.2f}mA_{PotLinear[i]:.2e}mW_{i}'
    filepath = filedir + filename
    print('saved data: '+filepath+'.pkl')
    # df.to_parquet(filepath+'.parq', compression='brotli')
    picklefile = open(f"{filepath}.pkl", 'wb')
    pickle.dump(df, picklefile)
    picklefile.close()

    i = i+1
    
keithley.set_source_current(0) # set current in A
