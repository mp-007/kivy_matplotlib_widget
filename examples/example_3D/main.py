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

KV = '''
#:import MatplotFigure3D graph_widget_3d

Screen
    figure_wgt:figure_wgt
    BoxLayout:
        orientation:'vertical'  
            
        MatplotFigure3D:
            id:figure_wgt

'''

class Test(App):
    lines = []

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        mygraph = GraphGenerator()
        
        self.screen.figure_wgt.figure = mygraph.fig
        
Test().run()