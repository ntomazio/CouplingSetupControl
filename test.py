import aq63XX 
import nidaqmx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
import controller # NI DAQ
import keithley2400 # current controller for the heaters
import pickle

_dev_read_T = "Dev1/ai1" # DAQ input channel (Transmission)
_dev_read_mzi = "Dev1/ai3" # DAQ input channel (MZI)
_dev_write = "Dev1/ao0" # DAQ output channel

# center_wav_osa  = 1555.8
# span_osa = 1.0
# wav_i_osa = center_wav_osa - span_osa*3/4
# wav_f_osa = wav_i_osa + span_osa

#auxiliary functions and custom errors
def _daq_write_voltage(voltage, dev_id = _dev_write):
    with nidaqmx.Task() as analog_output:
        analog_output.ao_channels.add_ao_voltage_chan(dev_id)
        analog_output.write(voltage)

def _daq_read_voltage(dev_id):
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(dev_id)
        task.timing.cfg_samp_clk_timing(rate = 100e3, sample_mode = nidaqmx.constants.AcquisitionType.FINITE)
        # t0=time.time()
        data = task.read(number_of_samples_per_channel=100)
        # t1=time.time()
        # print(f"it took {t1-t0:.6f} s to run")
        return np.mean(data)


        # return np.mean(task.read())
        # return np.mean(task.read(number_of_samples_per_channel=100))

# task = controller.Task()
# # task.add_channel("Dev1/ai0")    # laser trigger
# task.add_channel("Dev1/ai1")    # cavity transmission
# # task.add_channel("Dev1/ai2")    # acetylene
# task.add_channel("Dev1/ai3")    # mzi
# numChan = 2 # number of channels in DAQ
# sampRate = 400e3/numChan

# # _daq_write_voltage(1)
# task.acquisition_mode = 'N Samples'
# task.rate = sampRate
# task.samples = 100e3
# # task.timeout = 1.5*scan_time
# # print(f"Sampling rate: {sampRate} Pts/s")
# # print(f"Trace length: {int(sampRate*(scan_time+2))}")
# task.config()

# Vlow = -2
# Vhigh = 2
# step = 0.5
# ramp = np.arange(Vhigh, Vlow-step, -step)
# for v in ramp:
#     print(v)
#     _daq_write_voltage(v)
#     time.sleep(1)
#     # print(_daq_read_voltage(_dev_read_T))
#     # time.sleep(0.2)
#     # print(_daq_read_voltage(_dev_read_mzi))
#     # time.sleep(0.2)
#     _daq_read_voltage(_dev_read_T)


# r = task.read()
# task.close()

_daq_write_voltage(0)
time.sleep(1)
t0 = time.time()
data = _daq_read_voltage(_dev_read_T)
t1 = time.time()
print(f"it took {t1-t0:.6f} s to run")
