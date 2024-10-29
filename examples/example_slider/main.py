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
from graph_generator import GraphGenerator,f
import numpy as np
from kivy.clock import Clock
from functools import partial
import kivy_matplotlib_widget #register all widgets to kivy register
from kivy.uix.slider import Slider

KV = '''

Screen
    figure_wgt:figure_wgt
    slider_amp:slider_amp
    slider_freq:slider_freq
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
        BoxLayout:
            BoxLayout:
                size_hint_x:0.2
                orientation:'vertical'
                canvas.before:
                    Color:
                        rgba:1,1,1,1
                    Rectangle:
                        pos:self.pos
                        size:self.size 
                BoxLayout:
                    size_hint_y:0.06
                    Label:
                        text: "Amplitude"
                        color:0,0,0,1                      
                BoxLayout: 
                    MySlider:               
                        id: slider_amp
                        padding:0
                        orientation:'vertical'
                        min: 0.1
                        max: 10
                        step: 0.1
                        value_track:True
                        value_track_color:[0, 0, 1, 0.5]
                        value:5
    
                BoxLayout:
                    size_hint_y:0.25       
                    Label:
                        text: "{:.1f}".format(slider_amp.value)
                        color:0,0,0,1                        
            
            BoxLayout:
                padding:-dp(20),0,0,0
                MatplotFigure:
                    id:figure_wgt
                    minzoom:dp(20)
        BoxLayout:
            size_hint_y:0.2
            canvas.before:
                Color:
                    rgba:1,1,1,1
                Rectangle:
                    pos:self.pos
                    size:self.size
                    
            BoxLayout:
                size_hint_x:0.28
                Label:
                    text: "Frequency [Hz]"
                    color:0,0,0,1                
            BoxLayout: 
                MySlider:               
                    id: slider_freq
                    padding:0
                    min: 0.1
                    max: 30
                    step: 0.1
                    value_track:True
                    value_track_color:[0, 0, 1, 0.5]
                    value:3

            BoxLayout:
                size_hint_x:0.08        
                Label:
                    text: "{:.1f}".format(slider_freq.value)
                    color:0,0,0,1
                    
<MySlider@Slider>:
    canvas.before:
        Color:
            rgb: 0, 0, 1
        BorderImage:
            border: self.border_horizontal if self.orientation == 'horizontal' else self.border_vertical
            pos: (self.x + self.padding, self.center_y - self.background_width / 2) if self.orientation == 'horizontal' else (self.center_x - self.background_width / 2, self.y + self.padding)
            size: (self.width - self.padding * 2, self.background_width) if self.orientation == 'horizontal' else (self.background_width, self.height - self.padding * 2)
            source: (self.background_disabled_horizontal if self.orientation == 'horizontal' else self.background_disabled_vertical) if self.disabled else (self.background_horizontal if self.orientation == 'horizontal' else self.background_vertical)      
'''


class Test(App):
    lines = []
    current_idx= 0

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        mygraph = GraphGenerator()
        
        self.screen.figure_wgt.figure = mygraph.fig
        self.screen.figure_wgt.axes = mygraph.ax1
        self.screen.figure_wgt.xmin = mygraph.xmin
        self.screen.figure_wgt.xmax = mygraph.xmax
        self.screen.figure_wgt.ymin = mygraph.ymin
        self.screen.figure_wgt.ymax = mygraph.ymax
        self.screen.figure_wgt.fast_draw = False #update axis during pan/zoom
        
        #register lines instance if need to be update
        self.lines.append(mygraph.line1)
        
        self.screen.slider_freq.bind(value=self.update_freq)
        self.screen.slider_amp.bind(value=self.update_amp)
        
        

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def update_freq(self,instance,val):
        self.lines[0].set_ydata(f(self.lines[0].get_xdata(), self.screen.slider_amp.value, val))
        self.screen.figure_wgt.axes.figure.canvas.draw_idle()
        self.screen.figure_wgt.axes.figure.canvas.flush_events()   
        
    def update_amp(self,instance,val):
        self.lines[0].set_ydata(f(self.lines[0].get_xdata(), val, self.screen.slider_freq.value))
        self.screen.figure_wgt.axes.figure.canvas.draw_idle()
        self.screen.figure_wgt.axes.figure.canvas.flush_events()               
                   
    def home(self):
        self.screen.figure_wgt.home()
        
Test().run()