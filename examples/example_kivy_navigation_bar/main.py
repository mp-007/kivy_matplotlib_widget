
from kivy.utils import platform

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_on_activity')
    Config.set('kivy', 'keyboard_mode', '') #disable keyboard mode

from kivy.lang import Builder
from kivy.app import App

import numpy as np
from kivy.metrics import dp
from kivy_matplotlib_widget.uix.legend_widget import MatplotlibInteractiveLegend
from kivy_matplotlib_widget.uix.minmax_widget import add_minmax
from kivy_matplotlib_widget.uix.hover_widget import add_hover

import matplotlib.pyplot as plt

KV = '''
Screen
    figure_wgt:figure_wgt
    nav_bar:nav_bar
    BoxLayout:
        orientation:'vertical'
        BoxLayout:
            orientation:'horizontal' if nav_bar.orientation_type=='rail' else 'vertical' 
            canvas.before:
                Color:
                    rgba: (1, 1, 1, 1)
                Rectangle:
                    pos: self.pos
                    size: self.size           
            KivyMatplotNavToolbar:
                id:nav_bar
                nav_icon:'all'
                show_cursor_data:'desktop'
                figure_wgt:figure_wgt
    
            MatplotFigureSubplot:
                id:figure_wgt
                auto_cursor:True
                interactive_axis:True

        BoxLayout:
            size_hint_y:0.1
            Button:
                text:'add data'
                on_press:app.add_data()  
        BoxLayout:
            size_hint_y:0.1
            Button:
                text:'add data scatter'
                on_press:app.add_scatter()  
        BoxLayout:
            size_hint_y:0.1
            Button:
                text:'flip navigation bar'
                on_press:app.flip_navigation_bar()                  
'''

def autoscale_based_on_visible(lines):
    """ autoscale based on specific matplotlib lines
    
     Args:
        lines (list of line) : list of matplotlib line class

    Returns:
        min_y(float),max_y(float)
    """
    i=0
    y=[]
    x=[]  
   
    for line in lines:        

        if line.get_visible() and len(line.get_ydata())!=0:

            if i==0:  
                ydata=line.get_ydata()
                y = ydata
                if len(ydata)!=0: 
                    x = line.get_xdata()
            else:
                ydata=line.get_ydata()
                y = np.hstack([y,ydata])
                if len(x)==0:
                    if len(ydata)!=0: 
                        x = line.get_xdata() 
                else:
                   x = np.hstack([x,line.get_xdata()]) 
            i+=1
 
    if len(y)!=0:
        return min(x),max(x),min(y),max(y)
    else:
        if len(x)!=0:
            return min(lines[0].get_xdata()),max(lines[0].get_xdata()),0,1
        else:
            return 0,1,0,1

class Test(App):
    lines = []

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        fig, ax1 = plt.subplots(1, 1)

        line1, = ax1.plot([0,1,2,3,4], [1,2,8,9,4],label='line1')
        line2, = ax1.plot([2,8,10,15], [15,0,2,4],label='line2')
        
        scatter = ax1.scatter([0,8,10,11], [12,0,3,8],label='scatter')

        fig.tight_layout(rect=[0, 0.03, 1, 0.95],pad=dp(7))
        
        self.screen.figure_wgt.figure = fig
        
        ###adjust graph
        ax = self.screen.figure_wgt.figure.axes[0]

        add_hover(self.screen.figure_wgt,mode='touch')
        add_minmax(self.screen.figure_wgt)
        
        ax.legend(loc=4)
        
        MatplotlibInteractiveLegend(self.screen.figure_wgt)
        self.screen.figure_wgt.figure.tight_layout(rect=[0, 0.1, 1, 0.95])


    def flip_navigation_bar(self):
        if self.screen.nav_bar.orientation_type =='rail':
            self.screen.nav_bar.orientation_type ='actionbar'
        else:
            self.screen.nav_bar.orientation_type ='rail' 
    
    def add_data(self):
        x,y = self.screen.figure_wgt.axes.lines[0].get_data()
        self.screen.figure_wgt.axes.lines[0].set_data(np.append(x,x[-1]+1),np.append(y,y[-1]+1))
        self.screen.figure_wgt.figure.canvas.draw()
        
    def add_scatter(self):
        data = self.screen.figure_wgt.axes.collections[0].get_offsets()
        x,y = data[:,0], data[:,1]
        self.screen.figure_wgt.axes.collections[0].set_offsets(np.vstack([np.append(x,x[-1]+1),np.append(y,y[-1]+1)]).T)
        self.screen.figure_wgt.axes.relim()
        self.screen.figure_wgt.axes.autoscale_view()
        ax=self.screen.figure_wgt.axes

        self.screen.figure_wgt.figure.canvas.draw()        

        
Test().run()