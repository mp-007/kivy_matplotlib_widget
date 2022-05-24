#avoid conflict between mouse provider and touch (very important with touch device)
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
from graph_generator import GraphGenerator

KV = '''
#:import MatplotFigure graph_widget_3d

Screen
    figure_wgt:figure_wgt
    BoxLayout:
        orientation:'vertical'  
            
        MatplotFigure:
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