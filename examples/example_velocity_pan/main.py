"""Velocity pan example for kivy_matplotlib_widget

    
Note:
    MatplotFigure is used when you have only 1 axis with lines only.
    Velocity pan is managed for xaxis only
    
"""


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
import kivy_matplotlib_widget #register all widgets to kivy register

# Fixing random state for reproducibility
np.random.seed(19680801)

dt = 0.01
t = np.arange(0, 10, dt)
nse = np.random.randn(len(t))
r = np.exp(-t / 0.05)

cnse = np.convolve(nse, r) * dt
cnse = cnse[:len(t)]
s = 0.1 * np.sin(2 * np.pi * t) + cnse

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
                text:"velocity pan (x axis only)" 
                on_release:
                    app.set_touch_mode('pan')
                    self.state='down'
                    figure_wgt.velocity_panx=True
            ToggleButton:
                group:'touch_mode'
                text:"normal pan" 
                on_release:
                    app.set_touch_mode('pan')
                    self.state='down' 
                    figure_wgt.velocity_panx=False
            ToggleButton:
                group:'touch_mode'
                text:"zoom box"  
                on_release:
                    app.set_touch_mode('zoombox')
                    self.state='down'                
        MatplotFigure:
            id:figure_wgt
            fast_draw:False #recommanded for velocity pan
            velocity_panx:True
            auto_zoom:True
'''


class Test(App):
    lines = []

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        fig, ax1 = plt.subplots(1, 1)
        ax1.plot(t,s)
        ax1.set_xlim(t[0],t[50])
        ax1.set_ylim(min(s)-0.05,max(s)+0.05)

        self.screen.figure_wgt.figure = fig

        #set x lim (can pan or zoom over these values)
        self.screen.figure_wgt.stop_xlimits = [min(t),max(t)]

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        
Test().run()