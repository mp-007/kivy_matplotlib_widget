"""Basic example for kivy_matplotlib_widget

    This example don't use kivy_matplotlib_widget module in case you want to
    incorporate some widgets in your project and you want to customized stuffs.
    If you don't need custom used, please install the module with:
        
        pip install kivy-matplotlib-widget
    
Note:
    MatplotFigure is used when you have only 1 axis with lines only.
    
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


class Test(App):
    lines = []

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        fig, ax1 = plt.subplots(1, 1)

        ax1.plot([0,1,2,3,4], [1,2,8,9,4],label='line1')
        ax1.plot([2,8,10,15], [15,0,2,4],label='line2')
        
        self.screen.figure_wgt.figure = fig

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        
Test().run()