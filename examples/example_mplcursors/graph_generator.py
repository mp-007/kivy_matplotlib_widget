import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import numpy as np

from kivy.metrics import dp

font_size_axis_title = dp(16)
font_size_axis_tick = dp(12)
linewidth = 2

# optimized draw on Agg backend
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0
mpl.rcParams['agg.path.chunksize'] = 1000

# define some matplotlib figure parameters
mpl.rcParams['font.family'] = 'Verdana'
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['xtick.labelsize'] = font_size_axis_tick
mpl.rcParams['ytick.labelsize'] = font_size_axis_tick


class GraphGenerator(object):
    """class that generate Matplotlib graph."""

    def __init__(self):
        """Create empty structure plot.

        """
        super().__init__()


        self.fig, self.ax1 = plt.subplots(1, 1)
        
        base = datetime.datetime(2005, 2, 1)
        dates = np.array([base + datetime.timedelta(hours=(2 * i))
                          for i in range(732)])
        N = len(dates)
        np.random.seed(19680801)
        y = np.cumsum(np.random.randn(N))
        new_datetime = []
        for mytime in dates:
            new_datetime.append(mdates.date2num(mytime))
            
        self.line1, = self.ax1.plot(new_datetime, y,label='line1', linewidth=linewidth,
                                            color='#118812')

        self.fig.subplots_adjust(left=0.16,top=0.90,right=0.93,bottom=0.2) 
        self.ax1.set_xlabel("axis_x",fontsize=font_size_axis_title)
        self.ax1.set_ylabel("axis_y",fontsize=font_size_axis_title)#

        locator = mdates.AutoDateLocator()
        self.formatter = mdates.ConciseDateFormatter(locator)
        self.ax1.xaxis.set_major_locator(locator)
        self.ax1.xaxis.set_major_formatter(self.formatter)

        xmin,xmax = self.ax1.get_xlim()
        self.ax1.set_xlim(xmin,xmax)
