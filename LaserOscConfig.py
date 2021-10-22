"""
Created on October 2021

@author: Nathalia Tomazio (nathalia.tomazio@alumni.usp.br) with insights from Paulo Jarschel
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import oscDSOX3104A # oscilloscope 1GHz
# import oscAglDSO9404A # oscilloscope DSO9404 = 4GHz, big
import agilent816xb # laser 
import pickle
import ivi # the code uses the ivi package only to acquire the waveform

# --- define the objects for the laser and oscilloscope --- #
# change these
laser = agilent816xb.Agilent816xb()  # laser 
osc = oscDSOX3104A.OSCDSOX3104A()  # DSOX3104A = 1GHz
scope = ivi.agilent.agilentDSOX3104A('USB0::0x0957::0x17A0::MY52490398::INSTR')  # DSOX3104A = 1GHz
# osc = oscAglDSO9404A.OSCDSO9404A()  # DSO9404 = 4GHz, big scope


# --- Initial config for the laser scan ---#
# change these
scan_speed = 5 # in nm/s
wth_i = 1500 # start wavelength in nm
wth_f = 1600 # stop wavelength in nm
scan_time = (wth_f-wth_i)/scan_speed

laser.connectlaser()
laser.setState(0,1)
laser.setOutputTrigger(0,1)
laser.setSweepState(0,"Stop") # just to ensure that the laser sweep from a previous run has been stopped before the next sweep starts
laser.setSweep(0,"CONT", wth_i, wth_f, 1, 0, 0, scan_speed)
laser.setPwr(0,1e-3) # in W

# --- Initial config for the oscilloscope ---#
# change these
linewidth = 0.8e-3 # resonance linewidth in nm (110 MHz)
linewidth_pts = 15 # sampling pts within a resonance linewidth 
sampling_rate = scan_speed*linewidth_pts/linewidth

osc.connectOSC()
osc.stop() # just to restart the scope waveforms 

laser.setSweepState(0,"Start") # enable the laser sweep 

osc.run()
osc.setTimeScale(scan_time/10)
osc.setStartTime(scan_time/2)
osc.setSampRate(sampling_rate)
sampling_rate = osc.getSampRate()
sampling_pts = osc.getTraceLength()

print(f"Sampling rate: {sampling_rate} Pts/s")
print(f"Trace length: {sampling_pts}")

osc.setChannel(1,1) # trigger - laser TTL signal
osc.setEdgeTrigger(1, level=1000e-3) # level in V
osc.setChannel(2,1) # DUT signal
osc.setChannel(3,1) # acetylene
osc.setChannel(4,1) # MZI

# Oscilloscope parameters
osc_channels = [1, 2, 3, 4]
main_channel = 1

# --- Define the function to acquire the waveforms in the scope ---#
def Acquisition(data_crop=False, plot=True, save=False):
    
    # osc.single()
    # finished=False
    # print("Scanning...")
    # while not finished:
    #     finished = osc.singleFinished(main_channel)
    # print("Scan complete!")


    # oscstart = osc.getStartTime()
    # oscstop = osc.getStopTime()


    ch1_data = scope.channels[0].measurement.fetch_waveform()
    ch2_data = scope.channels[1].measurement.fetch_waveform()
    ch3_data = scope.channels[2].measurement.fetch_waveform()
    ch4_data = scope.channels[3].measurement.fetch_waveform()
    # ch1_data = osc.getData(1)
    # ch2_data = osc.getData(2)
    # ch3_data = osc.getData(3)
    # ch4_data = osc.getData(4)

    # osc_time = np.linspace(oscstart, oscstop, len(ch1_data))

    df = pd.DataFrame({'time':ch1_data.x, 'trigger_laser': ch1_data.y, 'cav': ch2_data.y, 'acetylene': ch3_data.y, 'mzi': ch4_data.y})

    # cropping the data might be necessary for the module wavelength_calibration.py to correctly identify the acetylene/hcn ref peaks  
    if data_crop:
        imin, imax = len(df)/2, len(df)
        df = df.iloc[int(imin):int(imax),:].copy()
        df.reset_index(drop=True, inplace=True)
        print('Dataframe memory usage:' + f'  {round(df.shape[1]*df.memory_usage(index=False).mean()/1e6,2)} MB' )
    
    if plot:
        fig, axspec = plt.subplots(3, sharex=True)
        axspec[0].plot(df['time'].values, df['trigger_laser'].values)
        axspec[1].plot(df['time'].values, df['acetylene'].values)
        axspec[2].plot(df['time'].values, df['mzi'].values)
        axspec[2].set_xlabel("Time (s)")
        axspec[0].set_ylabel("Voltage (V)")
        axspec[1].set_ylabel("Voltage (V)")
        axspec[2].set_ylabel("Voltage (V)")
        axspec[0].set_title("Laser Trigger")
        axspec[1].set_title("Acetylene")
        axspec[2].set_title("mzi")
        fig.tight_layout()

        plt.show()

    if save:
        # change these
        filedir = 'C:\\Users\\Lab\\Documents\\Nathalia Tomazio\\python codes\\transmission data\\'
        filename = 'test_2'
        filepath = filedir + filename
        print('saved data: '+filepath+'.pkl')
        # df.to_parquet(filepath+'.parq', compression='brotli')
        picklefile = open(f"{filepath}.pkl", 'wb')
        pickle.dump(df, picklefile)
        picklefile.close()
        #test
        
    return df


