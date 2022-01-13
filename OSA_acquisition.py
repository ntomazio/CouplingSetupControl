import aq63XX 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# osa_id = '143.106.72.187'#'nano-osa2-aq6370c.ifi.unicamp.br'
osa = aq63XX.AQ63XX()
osa.ConnectOSA(isgpib = True, address = 5)
# to prevent OSA from freezing to calibrate
osa.osa.write(':CALibration:ZERO off')
## Binary mode
osa.SetBinary(False)
osa.trace = "tra" # 20 dBm with filter
x_a,y_a = osa.GetData()
# osa.trace = "trb" #  20 dBm no filter
# x_b,y_b = osa.GetData()
# osa.trace = "trc" # 25 dBm with filter
# x_c,y_c = osa.GetData()
# osa.trace = "trd" # 25 dBm no filter
# x_d,y_d = osa.GetData()


df = pd.DataFrame({'wth': np.array(x_a), '20dBm with waveshaper':np.array(y_a)})
#  '20dBm no waveshaper': np.array(y_b),
#  '25dBm with waveshaper': np.array(y_c),
#  '25dBm no waveshaper': np.array(y_d)})

plt.plot(df['20dBm with waveshaper'], label = 'with_20')
# plt.plot(df['wth'],df['20dBm with waveshaper'], label = 'with_20')
# plt.plot(df['wth'],df['20dBm no waveshaper'], label = 'no_20')
# plt.plot(df['wth'],df['25dBm with waveshaper'], label = 'with_25')
# plt.plot(df['wth'],df['25dBm no waveshaper'], label = 'no_25')
plt.legend()
plt.show()

save = False
if save: 
    filedir = 'C:\\Users\\Lab\\Documents\\Nathalia Tomazio\\python codes\\transmission data\\C-band_heater control\\DOPO_signatures\\'
    #change this
    filename = f'21-12-21_chip1_R-R-R_wg-ring gap 600 nm_ring-ring gap 550 nm_TE_heater1_29.7mA_heater3_31.4mA_varying_waveshaper'
    filepath = filedir + filename
    df.to_csv(filepath+'.csv')


# 'wth22': 1e9*np.array(x_c), '22dBm':np.array(y_c),
# 'wth24': 1e9*np.array(x_d),'24dBm':np.array(y_d)}