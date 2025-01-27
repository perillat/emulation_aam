import pylab
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.interactive(False)

width = 12 / 2.54
matplotlib.rcParams["figure.figsize"] = (width, 0.75 * width)
matplotlib.rcParams["figure.subplot.left"] = 0.05
matplotlib.rcParams["figure.subplot.right"] = 0.98
matplotlib.rcParams["figure.subplot.bottom"] = 0.01
matplotlib.rcParams["figure.subplot.top"] = 0.98
font_size = 8
matplotlib.rcParams["font.size"] = font_size
matplotlib.rcParams["axes.titlesize"] = font_size
matplotlib.rcParams["axes.labelsize"] = font_size
matplotlib.rcParams["xtick.labelsize"] = font_size
matplotlib.rcParams["ytick.labelsize"] = font_size
matplotlib.rcParams["legend.fontsize"] = font_size

plt.close('all')
