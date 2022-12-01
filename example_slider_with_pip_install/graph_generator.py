import matplotlib as mpl
import matplotlib.pyplot as plt
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

import numpy as np  

# The parametrized function to be plotted
def f(t, amplitude, frequency):
    return amplitude * np.sin(2 * np.pi * frequency * t)      

class GraphGenerator(object):
    """class that generate Matplotlib graph."""

    def __init__(self):
        """Create empty structure plot. 
        
        """       
        super().__init__()

        self.fig, self.ax1 = plt.subplots(1, 1)
        
        t = np.linspace(0, 1, 1000)
        init_frequency=3.0
        init_amplitude=5.0
        
        self.line1, = self.ax1.plot(t, f(t, init_amplitude, init_frequency),label='line1')

        self.xmin,self.xmax = self.ax1.get_xlim()
        self.ymin,self.ymax = self.ax1.get_ylim()
        
        self.fig.subplots_adjust(left=0.06,top=0.96,right=0.93,bottom=0.2)
 
        self.ax1.set_xlim(self.xmin, self.xmax)
        self.ax1.set_ylim(self.ymin, self.ymax)   
        self.ax1.set_xlabel("Time [s]",fontsize=font_size_axis_title)
        