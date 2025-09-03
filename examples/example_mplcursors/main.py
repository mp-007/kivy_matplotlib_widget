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
from graph_generator import GraphGenerator

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from kivy.metrics import dp
import numpy as np
font_size_axis_title = dp(16)
font_size_axis_tick = dp(12)
linewidth = 2

from kivy_matplotlib_widget.uix.hover_widget import (add_hover,
                                                     HoverVerticalText,
                                                     InfoHover,
                                                     BaseHoverFloatLayout,
                                                     PlotlyHover)
from matplotlib.ticker import FormatStrFormatter
from kivy.properties import ColorProperty,NumericProperty,StringProperty

#remove font_manager "debug" from matplotib
import logging
logging.getLogger('matplotlib.font_manager').disabled = True

KV = '''
#:import MatplotFigureCustom graph_custom_widget

Screen
    figure_wgt:figure_wgt
    figure_wgt2:figure_wgt2
    figure_wgt3:figure_wgt3
    figure_wgt4:figure_wgt4
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
                text: 'Cursor'
                on_press: 
                    app.set_touch_mode('cursor')
                    self.state='down'
                    
        BoxLayout:    
            MatplotFigureCustom:
                id:figure_wgt
                
            MatplotFigureCustom:
                id:figure_wgt2  
                fast_draw:False 
                         
        BoxLayout:  
            MatplotFigureCustom:
                id:figure_wgt3  
                fast_draw:False

            MatplotFigureCustom:
                id:figure_wgt4   
                fast_draw:False 

'''

class Test(App):
    lines = []

    def build(self):
        self.screen=Builder.load_string(KV)
        return self.screen


    def on_start(self, *args):

        mygraph = GraphGenerator()
        self.screen.figure_wgt.axes= mygraph.ax1

        self.screen.figure_wgt.figure = mygraph.fig
        self.screen.figure_wgt.cursor_xaxis_formatter = mdates.DateFormatter('%m-%d')
        self.screen.figure_wgt.cursor_yaxis_formatter = FormatStrFormatter('%.1f') 
        
        self.screen.figure_wgt.register_lines(self.screen.figure_wgt.axes.lines)
        self.screen.figure_wgt.register_cursor()
        
        add_hover(self.screen.figure_wgt,mode='desktop',hover_widget=PlotlyHover())

        fig, ax = plt.subplots(1, 1)
        
        x = 4 + np.random.normal(0, 1.5, 200)
        
        ax.hist(x, bins=8, linewidth=0.5, edgecolor="white")
        
        fig.subplots_adjust(left=0.15,top=0.90,right=0.93,bottom=0.2) 
        ax.set_xlabel("axis_x",fontsize=font_size_axis_title)
        ax.set_ylabel("axis_y",fontsize=font_size_axis_title)#  
        
        
        self.screen.figure_wgt2.cursor_xaxis_formatter = FormatStrFormatter('%.1f')
        self.screen.figure_wgt2.cursor_yaxis_formatter = FormatStrFormatter('%.1f')  

        self.screen.figure_wgt2.axes= ax
        
        self.screen.figure_wgt2.figure = fig
        self.screen.figure_wgt2.register_lines([])
        self.screen.figure_wgt2.register_cursor()
        
        add_hover(self.screen.figure_wgt2,mode='desktop',hover_widget=InfoHover())
        
        fig3, ax3 = plt.subplots(1, 1)
        X, Y = np.meshgrid(np.linspace(-3, 3, 16), np.linspace(-3, 3, 16))
        Z = (1 - X/2 + X**5 + Y**3) * np.exp(-X**2 - Y**2)
        
        # plot
        ax3.imshow(Z,label=" ")

        fig3.subplots_adjust(left=0.13,top=0.90,right=0.93,bottom=0.2) 
        ax3.set_xlabel("axis_x",fontsize=font_size_axis_title)
        ax3.set_ylabel("axis_y",fontsize=font_size_axis_title)#  

        self.screen.figure_wgt3.cursor_xaxis_formatter = FormatStrFormatter('%.1f')
        self.screen.figure_wgt3.cursor_yaxis_formatter = FormatStrFormatter('%.1f') 
        
        self.screen.figure_wgt3.axes= ax3
        
        self.screen.figure_wgt3.figure = fig3
        self.screen.figure_wgt3.register_lines([])
        self.screen.figure_wgt3.register_cursor() 
        
        add_hover(self.screen.figure_wgt3,mode='desktop',hover_widget=InfoHover())
        
        x = [1, 2, 3, 4]
        y = np.linspace(0.2, 0.7, len(x))
        colors = plt.get_cmap('Blues')(y)
        
        percent=[]
        last_y=0
        sum_y=y.sum()
        for i in y:          
            percent.append(f"{np.round((i/sum_y)*100,1)}%")
        
        # plot
        with plt.style.context('_mpl-gallery-nogrid',after_reset=True):
            fig4, ax4 = plt.subplots()
            fig4.subplots_adjust(left=0.13,top=0.90,right=0.93,bottom=0.2) 

            wedges, texts = ax4.pie(x, labels=percent,labeldistance=None,colors=colors,radius=3, center=(4, 4),
                   wedgeprops={"linewidth": 1, "edgecolor": "white"}, frame=True)
            
            ax4.set(xlim=(0, 8), xticks=np.arange(1, 8),
                   ylim=(0, 8), yticks=np.arange(1, 8))
            ax4.xaxis.set_visible(False)
            ax4.yaxis.set_visible(False)

        self.screen.figure_wgt4.cursor_xaxis_formatter = FormatStrFormatter('%.1f')
        self.screen.figure_wgt4.cursor_yaxis_formatter = FormatStrFormatter('%.1f') 
        
        self.screen.figure_wgt4.axes= ax4
        
        self.screen.figure_wgt4.figure = fig4
        self.screen.figure_wgt4.register_lines([])
        self.screen.figure_wgt4.register_cursor() 

        add_hover(self.screen.figure_wgt4,mode='desktop',hover_widget=InfoHover())        

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode
        self.screen.figure_wgt2.touch_mode=mode
        self.screen.figure_wgt3.touch_mode=mode
        self.screen.figure_wgt4.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()



Test().run()