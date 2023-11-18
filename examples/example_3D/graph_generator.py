import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
import numpy as np

from kivy.metrics import dp

#optimized draw on Agg backend
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0
mpl.rcParams['agg.path.chunksize'] = 1000

#define some matplotlib figure parameters
mpl.rcParams['font.family'] = 'Verdana'
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.linewidth'] = 1.0

font_size_axis_title=dp(13)
font_size_axis_tick=dp(12)        

class GraphGenerator(object):
    """class that generate Matplotlib graph."""

    def __init__(self):
        """Create empty structure plot. 
        
        """       
        super().__init__()

        # self.fig, self.ax1 = plt.subplots(1, 1)
        
        self.axes_3d = plt.axes(projection='3d')
 
        # Data for a three-dimensional line
        zline = np.linspace(0, 15, 1000)
        xline = np.sin(zline)
        yline = np.cos(zline)
        self.axes_3d.plot3D(xline, yline, zline, 'gray')
        
        self.fig = plt.gcf()

        # self.fig.subplots_adjust(left=0.13,top=0.96,right=0.93,bottom=0.2)
        
# axes_3d = plt.axes(projection='3d')
 
# # Data for a three-dimensional line
# zline = np.linspace(0, 15, 1000)
# xline = np.sin(zline)
# yline = np.cos(zline)
# axes_3d.plot3D(xline, yline, zline, 'gray')

# fig = plt.gcf()

# plt.show()