import aq63XX 
import nidaqmx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
import keithley2400 # current controller for the heaters
import pickle
import xarray as xr

_dev_read_T = "Dev1/ai1" # DAQ input channel (Transmission)
_dev_read_mzi = "Dev1/ai3" # DAQ input channel (MZI)
_dev_write = "Dev1/ao0" # DAQ output channel

center_wav_osa  = 1555.65
span_osa = 1.0
wav_i_osa = center_wav_osa - span_osa*1/2
wav_f_osa = wav_i_osa + span_osa

#auxiliary functions and custom errors
def _daq_write_voltage(voltage, dev_id = _dev_write):
    with nidaqmx.Task() as analog_output:
        analog_output.ao_channels.add_ao_voltage_chan(dev_id)
        analog_output.write(voltage)

def _daq_read_voltage(dev_id):
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(dev_id)
        # adjust the acquisition rate
        task.timing.cfg_samp_clk_timing(rate = 200e3, sample_mode = nidaqmx.constants.AcquisitionType.FINITE)
        return np.mean(task.read(number_of_samples_per_channel=100))

# class VoltageAboveRange(Exception):
#     def __init__(self, err_tshd, message = "Desired voltage is above range supported sensor."):
#         self.err_tshd = err_tshd
#         self.message = message
#         super().__init__(self.message)

# class VoltageBelowRange(Exception):
#     def __init__(self, err_tshd, message = "Desired voltage is below range supported sensor."):
#         self.err_tshd = err_tshd
#         self.message = message
#         super().__init__(self.message)


## Configure OSA
osa = aq63XX.AQ63XX()
osa.CloseOSA()
osa.ConnectOSA(isgpib = True, address = 5)
# to prevent OSA from freezing to calibrate
osa.osa.write(':CALibration:ZERO off')

## ASCII or BINARY mode
osa.SetBinary(False)

## create a vector for the OSA wavelengths
osa.SetStartWavelength(wav_i_osa)
osa.SetStopWavelength(wav_f_osa)
osa.SetSensMode("Mid")
osa.SingleSweep()
ended = False
while not ended:
    ended = osa.EndedSweep()
    time.sleep(0.1)
osa.trace = "tra" # 20 dBm with filter
x_a, y_a = osa.GetData()
lamda_osa = x_a


## Configure current
keithley3 = keithley2400.Keithley2400SM() # current controller
keithley3.connectSM(address=25)
keithley3.conf_apply_current()
# change this
keithley3.set_compliance_voltage(5) # initialize the compliance voltage [Volts]

keithley1 = keithley2400.Keithley2400SM() # current controller
keithley1.connectSM(address=24)
keithley1.conf_apply_current()
# change this
keithley1.set_compliance_voltage(5) # initialize the compliance voltage [Volts]

## take data
# current loops
current_vec1 = np.arange(30, 30.5, 0.1)
current_vec3 = np.arange(31, 31.5, 0.1)
# current_vec1 = [30.2]
# current_vec3 = [31.2]
# voltage ramp
step_volt = 0.1
volts = np.arange(2.0, -(2.0+step_volt), -step_volt)
# Initialize 4D array
mapOsayVh3h1 = np.zeros((len(current_vec1), len(current_vec3), len(volts), len(lamda_osa)))
mapTransmVh3h1 = np.zeros((len(current_vec1), len(current_vec3), len(volts), 2))

# t0 = time.time()

for ind_h1, curr1 in enumerate(current_vec1):
    keithley1.set_source_current(curr1*1e-3) # set current in heater 1
    time.sleep(2)
    
    for ind_h3, curr3 in enumerate(current_vec3):
        keithley3.set_source_current(curr3*1e-3) # set current in heater 3
        time.sleep(2)
        
        for ind_v, v0 in enumerate(volts):
            _daq_write_voltage(v0)
            print(f'iteration for heater 1 = {curr1:.2f} mA, heater 3 = {curr3:.2f} mA, and DAQ_voltage = {v0:.2f}')
            try:
                osa.SingleSweep()
                ended = False
                while not ended:
                    ended = osa.EndedSweep()
                    time.sleep(0.1)
                # osa.trace = "tra"
                x_a, y_a = osa.GetData()
            except:
                print(f"Data acquisition failed for heater 1 = {curr1:.2f} mA, heater 3 = {curr3:.2f} mA, and DAQ_voltage = {v0:.2f}")
                try:
                    print("2nd attempt")
                    osa.SingleSweep()
                    ended = False
                    while not ended:
                        ended = osa.EndedSweep()
                        time.sleep(0.1)
                    # osa.trace = "tra"
                    x_a, y_a = osa.GetData()
                except:
                    print(f"Data acquisition failed for heater 1 = {curr1:.2f} mA, heater 3 = {curr3:.2f} mA, and DAQ_voltage = {v0:.2f}")

            mapOsayVh3h1[ind_h1, ind_h3, ind_v] = y_a
            mapTransmVh3h1[ind_h1, ind_h3, ind_v, 0] = _daq_read_voltage(_dev_read_T)
            time.sleep(1)
            mapTransmVh3h1[ind_h1, ind_h3, ind_v, 1] = _daq_read_voltage(_dev_read_mzi)
            time.sleep(1)
        
        _daq_write_voltage(0)

        
map_complete1 = xr.DataArray(mapOsayVh3h1, coords=[current_vec1, current_vec3, volts, lamda_osa], dims=["h1_current", "h3_current", "DAQ_voltage", "Power_OSA"])
map_complete2 = xr.DataArray(mapTransmVh3h1, dims=["h1_current", "h3_current", "DAQ_voltage", "transmission"])

# _daq_write_voltage(0)
# osa.SingleSweep()
osa.CloseOSA()
print('success!')

# t1 = time.time()
# print(f"it took {t1-t0:.6f} s to run")

keithley1.set_source_current(0)
keithley3.set_source_current(0)

# Saving data
save = True
if save:
    filedir = 'C:\\Users\\Lab\\Documents\\Nathalia Tomazio\\python codes\\transmission data\\C-band_heater control\\R-R-R_molecule 600-550\\'
    filename = '22-01-13_chip1_R-R-R_wg-ring gap 600 nm_ring-ring gap 550 nm_TE_drop port_heaterMap_20dBm'
    filepath = filedir + filename
    print('saved data: '+filepath+'.nc')
    map_complete1.to_netcdf(filepath+'.nc')
    map_complete2.to_netcdf(filepath+'_transmission.nc')

# plt.plot(df.iloc[0], df.iloc[1])
# plt.show()
