#avoid conflict between mouse provider and touch (very important with touch device)
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
from graph_generator import GraphGenerator
from kivy.clock import Clock
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

X = np.linspace(0, 10*np.pi, 1000)
Y = np.sin(X)
    

class Test(App):

    def build(self):  
        self.i=0
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        mygraph = GraphGenerator()
        
        self.screen.figure_wgt.figure = mygraph.fig
        self.screen.figure_wgt.axes = mygraph.ax1
        self.screen.figure_wgt.xmin=0
        self.screen.figure_wgt.xmax = 2*np.pi
        self.screen.figure_wgt.ymin=-1.1
        self.screen.figure_wgt.ymax = 1.1
        self.screen.figure_wgt.line1=mygraph.line1
        self.home()
       
        Clock.schedule_interval(self.update_graph,1/60)

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        
    def update_graph(self,_):
        if self.i<1000:
            xdata=np.append(self.screen.figure_wgt.line1.get_xdata(), X[self.i])
            self.screen.figure_wgt.line1.set_data(xdata,np.append(self.screen.figure_wgt.line1.get_ydata(), Y[self.i]))
            if self.i>2:
                self.screen.figure_wgt.xmax = np.max(xdata)
                if self.screen.figure_wgt.axes.get_xlim()[0]==self.screen.figure_wgt.xmin:
                    self.home()
                else:
                    self.screen.figure_wgt.figure.canvas.draw_idle()
                    self.screen.figure_wgt.figure.canvas.flush_events() 
           
            self.i+=1
        else:
            Clock.unschedule(self.update_graph)
        
Test().run()