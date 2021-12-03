import random
from itertools import count
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

plt.style.use('fivethirtyeight')

x_vals = []
y_vals_1 = []
y_vals_2 = []

index = count()

def animate(i):
    x_vals.append(next(index))
    # y_vals_1.append(random.randint(0, 5))
    # y_vals_2.append(random.randint(0, 5))
    y_vals_1.append(random.randint(0, 5))
    y_vals_2.append(random.randint(0, 5))
    plt.cla()

    plt.plot(x_vals, y_vals_1, label='chan 1')
    plt.plot(x_vals, y_vals_2, label='chan 2')
    plt.xlim([max(0, i-10), i+5])
    plt.ylim([-0.1, 6])
    plt.legend(loc='upper left')
    
ani = FuncAnimation(plt.gcf(), animate, interval=500)

plt.tight_layout()
plt.show()