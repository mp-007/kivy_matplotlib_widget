from kivy.app import App
from kivy.lang import Builder
import kivy_matplotlib_widget #registers all widgets in kivy factory
from matplotlib import pyplot as plt
from kivy.clock import Clock
from matplotlib.ticker import MaxNLocator

import matplotlib as mpl

#optimized draw on Agg backend
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0

#depending of the data. This can increase the graph rendering
#see matplotlib doc for more info
#https://matplotlib.org/stable/users/explain/artists/performance.html#splitting-lines-into-smaller-chunks
mpl.rcParams['agg.path.chunksize'] = 1000

import numpy as np

N = 100000
np.random.seed(19680801)
xdata = np.arange(N)
ydata = np.cumsum(np.random.randn(N))
ydata2 = np.cumsum(np.random.randn(N))
   
#max data per window. Less data in window = faster draw     
max_data_window = 10000 

#on every axis limit update, half of max_data_window will be visible
#ex: 10000/2 = 5000 data visible in axis limit
ratio_data = 2

KV = '''
Screen
    figure_wgt:figure_wgt
    BoxLayout:
        orientation:'vertical'
        BoxLayout:
            size_hint_y:0.2
            Button:
                text:"home"
                on_release:app.home()
            ToggleButton:
                group:'touch_mode'
                state:'down'
                text:"pan" 
                on_press:
                    app.set_touch_mode('pan')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"zoom box"  
                on_press:
                    app.set_touch_mode('zoombox')
                    self.state='down'  
                   
        MatplotFigure:
            id:figure_wgt
            fast_draw:True
'''

def activate_monitor_mode():
    """Activate kivy monitor mode (get fps rate information in top bar)"""
    from kivy.core.window import Window
    from kivy.modules import Modules
    from kivy.config import Config

    Config.set('modules', 'monitor', '')        
    Modules.activate_module('monitor',Window)

class uiApp(App):
    line1 = None
    line2 = None
    min_index=0
    max_index=1
    current_xmax_refresh=None
    def build(self):
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        activate_monitor_mode()
        fig, ax1 = plt.subplots(1, 1)
        self.line1, = plt.plot([], [],color="green", label = "Low")
        self.line2, = plt.plot([], [],color="red", label = "High")

        ax1.xaxis.set_major_locator(MaxNLocator(prune='lower',nbins=5))  

        self.current_xmax_refresh = xdata[max_data_window]

        xmin = 0
        xmax = self.current_xmax_refresh
 
        ax1.set_xlim(xmin, self.current_xmax_refresh)
        ax1.set_ylim(np.min(np.append(ydata,ydata2)), np.max(np.append(ydata,ydata2)))
        
        self.screen.figure_wgt.figure =fig 
        self.screen.figure_wgt.xmin =xmin 
        self.screen.figure_wgt.xmax = xmax 
        self.home()

        #start live data in 3 seconds
        Clock.schedule_once(self.update_graph_delay,3)
        
    def update_graph_delay(self, *args):   
        #update graph data every 1/60 seconds
        Clock.schedule_interval(self.update_graph,1/60)
        
    def update_graph(self, *args):
        """Update graph method using blit method
        
        """

        current_x=xdata[self.min_index:self.max_index] 
        current_y=ydata[self.min_index:self.max_index] 
        current_y2=ydata2[self.min_index:self.max_index] 

        if not self.max_index>N:

            self.line1.set_data(current_x,current_y)
            self.line2.set_data(current_x,current_y2)

            if self.screen.figure_wgt.axes.get_xlim()[0]==self.screen.figure_wgt.xmin:
                
                if current_x[-1]< self.current_xmax_refresh:   

                    myfig=self.screen.figure_wgt
                    ax=myfig.axes
                    #use blit method            
                    if myfig.background is None:
                        myfig.background_patch_copy.set_visible(True)
                        ax.figure.canvas.draw_idle()
                        ax.figure.canvas.flush_events()                   
                        myfig.background = ax.figure.canvas.copy_from_bbox(ax.figure.bbox)
                        myfig.background_patch_copy.set_visible(False)  
                    ax.figure.canvas.restore_region(myfig.background)
                   
                    for line in ax.lines:
                        ax.draw_artist(line)
                    ax.figure.canvas.blit(ax.bbox)
                    ax.figure.canvas.flush_events()                     
                else:
                    #update axis limit
                    
                    try:
                        self.current_xmax_refresh = xdata[self.max_index+int(max_data_window - max_data_window//ratio_data)]
                    except:
                        self.current_xmax_refresh = xdata[-1]
                    # self.current_xmax_refresh = new_x[max_data_window]
                    self.screen.figure_wgt.xmin = xdata[self.max_index-int(max_data_window//ratio_data)]
                    self.screen.figure_wgt.xmax =self.current_xmax_refresh 
                    myfig=self.screen.figure_wgt
                    ax=myfig.axes                     
                    myfig.background_patch_copy.set_visible(True)
                    ax.figure.canvas.draw_idle()
                    ax.figure.canvas.flush_events()                   
                    myfig.background = ax.figure.canvas.copy_from_bbox(ax.figure.bbox)
                    myfig.background_patch_copy.set_visible(False)                    
                    self.home()
            else:
                #minimum xlim as changed. pan or zoom if maybe detected
                #update axis limit stop
                myfig=self.screen.figure_wgt
                ax=myfig.axes
                #use blit method            
                if myfig.background is None:
                    myfig.background_patch_copy.set_visible(True)
                    ax.figure.canvas.draw_idle()
                    ax.figure.canvas.flush_events()                   
                    myfig.background = ax.figure.canvas.copy_from_bbox(ax.figure.bbox)
                    myfig.background_patch_copy.set_visible(False)  
                ax.figure.canvas.restore_region(myfig.background)
               
                for line in ax.lines:
                    ax.draw_artist(line)
                ax.figure.canvas.blit(ax.bbox)
                ax.figure.canvas.flush_events()               
           
            self.max_index+=20 #increase step value (each frame, add 20 data)
    
        else:
            Clock.unschedule(self.update_graph)
            myfig=self.screen.figure_wgt          
            myfig.xmin = 0#if double-click, show all data
        
    def home(self):
       self.screen.figure_wgt.home()
       
    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode
        
uiApp().run()
