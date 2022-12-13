from kivy.utils import platform

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
from kivy.metrics import dp

#optimized draw on Agg backend
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0
mpl.rcParams['agg.path.chunksize'] = 1000

#define some matplotlib figure parameters
mpl.rcParams['font.family'] = 'Verdana'
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['axes.linewidth'] = 1.0


KV = '''
#:import MatplotFigureTwinx graph_widget_twinx

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
                on_release:
                    app.set_touch_mode('pan')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"zoom box"  
                on_release:
                    app.set_touch_mode('zoombox')
                    self.state='down' 
            ToggleButton:
                group:'touch_mode'
                text:"cursor"  
                on_release:
                    app.set_touch_mode('cursor')
                    self.state='down'                       
        MatplotFigureTwinx:
            id:figure_wgt
'''


class Test(App):
    lines = []

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        fig,ax1 = plt.subplots(1,1)
        ax2 = ax1.twinx()
        x = np.linspace(0,2*np.pi,100)
        ax1.plot(x,np.sin(x),'b')
        ax1.set_xlabel('Scaleable axis')
        ax1.set_ylabel('Scaleable axis')
        ax2.plot(x,np.sin(x+1),'r')
        ax2.set_ylabel('Static axis',weight='bold')
            
        self.screen.figure_wgt.figure = fig
        self.screen.figure_wgt.fast_draw=False
        
        self.lines=fig.axes[0].lines + fig.axes[1].lines
        self.screen.figure_wgt.register_lines(self.lines)

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        
Test().run()