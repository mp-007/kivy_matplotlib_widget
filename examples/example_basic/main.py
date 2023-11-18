
from kivy.utils import platform

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
from graph_generator import GraphGenerator

import numpy as np

KV = '''
#:import MatplotFigure graph_widget

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
        MatplotFigure:
            id:figure_wgt
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
        mygraph = GraphGenerator()
        
        self.screen.figure_wgt.figure = mygraph.fig
        
        ###adjust graph
        ax = self.screen.figure_wgt.figure.axes[0]
        
        #get min/max of all lines
        xmin,xmax,ymin,ymax = autoscale_based_on_visible(ax.lines)
        
        ax.set_xlim(xmin,(xmax-xmin)*2 + xmin)
        ax.set_ylim(ymin - (ymax-ymin),(ymax-ymin) + ymax)
        

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        
Test().run()