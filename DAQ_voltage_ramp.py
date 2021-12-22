import aq63XX 
import nidaqmx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
import keithley2400 # current controller for the heaters
import pickle

_dev_read = "Dev1/ai0" # DAQ input channel
_dev_write = "Dev1/ao0" # DAQ output channel

center_wav_osa  = 1555.8
span_osa = 1.0
wav_i_osa = center_wav_osa - span_osa*3/4
wav_f_osa = wav_i_osa + span_osa

#auxiliary functions and custom errors
def _daq_write_voltage(voltage, dev_id = _dev_write):
    with nidaqmx.Task() as analog_output:
        analog_output.ao_channels.add_ao_voltage_chan(dev_id)
        analog_output.write(voltage)

def _daq_read_voltage(dev_id = _dev_read):
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(dev_id)
        return np.mean(task.read(number_of_samples_per_channel=3))

class VoltageAboveRange(Exception):
    def __init__(self, err_tshd, message = "Desired voltage is above range supported sensor."):
        self.err_tshd = err_tshd
        self.message = message
        super().__init__(self.message)

class VoltageBelowRange(Exception):
    def __init__(self, err_tshd, message = "Desired voltage is below range supported sensor."):
        self.err_tshd = err_tshd
        self.message = message
        super().__init__(self.message)


## Configure OSA
osa = aq63XX.AQ63XX()
osa.CloseOSA()
osa.ConnectOSA(isgpib = True, address = 5)

# Binary mode
osa.binary = True
# self.osa.write("format:data real,32")

osa.SetStartWavelength(wav_i_osa)
osa.SetStopWavelength(wav_f_osa)
osa.SetSensMode("Mid")
osa.SingleSweep()
time.sleep(1)
osa.trace = "tra" # 20 dBm with filter
x_a, y_a = osa.GetData()
map1 = np.vstack((x_a, y_a))

## Configure current

keithley1 = keithley2400.Keithley2400SM() # current controller
keithley1.connectSM(address=25)
keithley1.conf_apply_current()
# change this
keithley1.set_compliance_voltage(5) # initialize the compliance voltage [Volts]

keithley2 = keithley2400.Keithley2400SM() # current controller
keithley2.connectSM(address=24)
keithley2.conf_apply_current()
# change this
keithley2.set_compliance_voltage(5) # initialize the compliance voltage [Volts]

current_vec1 = np.arange(29.9, 30.1, 0.05)
current_vec2 = np.arange(31.0, 32.0, 0.05)
for curr2 in current_vec2:
    keithley1.set_source_current(curr2*1e-3) # set current in A
    time.sleep(2)
    for curr1 in current_vec1:
        keithley2.set_source_current(curr1*1e-3) # set current in A
        time.sleep(2)
        ## voltage ramp
        volts = np.arange(4.2, 1.5, -0.1)
        for v0 in volts:
            _daq_write_voltage(v0)
            osa.SingleSweep()
            time.sleep(1)
            osa.trace = "tra"
            x_a, y_a = osa.GetData()
            time.sleep(2)
            map1 = np.vstack((map1, y_a))
        
        _daq_write_voltage(0)
        
df = pd.DataFrame(map1)

_daq_write_voltage(0)
osa.SingleSweep()
osa.CloseOSA()
print('success!')

## Saving data
filedir = 'C:\\Users\\Lab\\Documents\\Nathalia Tomazio\\python codes\\transmission data\\broadband spectra\\'
filename = '21-12-22_chip1_R-R-R_wg-ring gap 600 nm_ring-ring gap 550 nm_broadband_TE_drop port_heaterMap_10dBm'
filepath = filedir + filename
print('saved data: '+filepath+'.pkl')
# df.to_parquet(filepath+'.parq', compression='brotli')
picklefile = open(f"{filepath}.pkl", 'wb')
pickle.dump(df, picklefile)
picklefile.close()
# plt.plot(df.iloc[0], df.iloc[1])
# plt.show()
