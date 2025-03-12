from kivy.utils import platform
from kivy.config import Config

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    Config.set('input', 'mouse', 'mouse,disable_on_activity')
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand') #disable red dot
else:
    #for android, we remove mouse input to not get extra touch 
    Config.remove_option('input', 'mouse')

from kivy.lang import Builder
from kivy.app import App
from graph_generator import GraphGenerator
import kivy_matplotlib_widget

KV = '''

Screen
    figure_wgt_layout:figure_wgt_layout
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
                text:"rotate" 
                on_release:
                    app.set_touch_mode('rotate')
                    self.state='down'                
            ToggleButton:
                group:'touch_mode'
                text:"pan axis" 
                on_release:
                    app.set_touch_mode('pan')
                    self.state='down' 
            ToggleButton:
                group:'touch_mode'
                text:"pan figure" 
                on_release:
                    app.set_touch_mode('figure_zoom_pan')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"cursor"  
                on_release:
                    app.set_touch_mode('cursor')
                    self.state='down'         

                
   
        
        BoxLayout:
            canvas.before:
                Color:
                    rgba: (1, 1, 1, 1)
                Rectangle:
                    pos: self.pos
                    size: self.size
            MatplotFigure3DLayout:
                id:figure_wgt_layout
                
                  

'''

class Test(App):
    lines = []

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        mygraph = GraphGenerator()
        
        self.screen.figure_wgt_layout.figure_wgt.figure = mygraph.fig

    def set_touch_mode(self,mode):
        self.screen.figure_wgt_layout.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt_layout.figure_wgt.home()
        
Test().run()