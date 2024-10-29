from kivy.utils import platform
from kivy.config import Config

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    Config.set('input', 'mouse', 'mouse,disable_on_activity')
else:
    #for android, we remove mouse input to not get extra touch 
    Config.remove_option('input', 'mouse')

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
#:import MatplotFigureGeneral graph_widget_general
#:import MatplotNavToolbar navigation_bar_widget

Screen
    figure_wgt:figure_wgt
    BoxLayout:
        orientation:'vertical' 
        MatplotNavToolbar:
            id: navbar_wgt
            size_hint: 1, 0.2
            figure_widget: figure_wgt              
        MatplotFigureGeneral:
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
        
        self.screen.ids.navbar_wgt._navtoolbar._init_toolbar()
        
        #if user want to hide cursor label
        # self.screen.ids.navbar_wgt.ids.info_lbl.height=dp(0.01)
        # self.screen.ids.navbar_wgt.ids.info_lbl.opacity=0
        # self.screen.ids.navbar_wgt.ids.info_lbl.size_hint_y=None

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        
Test().run()