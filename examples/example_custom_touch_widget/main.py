from kivy.utils import platform

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
from graph_generator import GraphGenerator

import matplotlib.dates as mdates


KV = '''
#:import MatplotFigureCustom graph_custom_widget

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
                text: 'line_setting'
                on_press: 
                    app.set_touch_mode('line_setting')
                    self.state='down'
                    
            ToggleButton:
                group:'touch_mode'
                text: 'line_data'
                on_press: 
                    app.set_touch_mode('line_data')  
                    self.state='down'
            
        MatplotFigureCustom:
            id:figure_wgt
 
'''


def custom_delta_date_formatter(x):
    """custom formatter with no second
    
    Args:
        x : value
    """ 
    return f"{mdates.num2timedelta(x)}"[:-10]

def yrange_formatter(x):
    """custom y range formatter (round at 2 digits)
    
    Args:
        x : value
    """ 
    return round((x), 2)

class Test(App):
    lines = []

    def build(self):
        self.screen=Builder.load_string(KV)
        return self.screen


    def on_start(self, *args):


        mygraph = GraphGenerator()
        self.screen.figure_wgt.axes= mygraph.ax1
        for line in self.screen.figure_wgt.axes.lines:
            self.lines.append(line)

        self.screen.figure_wgt.register_lines(self.lines)
        self.screen.figure_wgt.figure = mygraph.fig
        
        self.screen.figure_wgt.line_data_widget.x_formatter = custom_delta_date_formatter
        self.screen.figure_wgt.line_data_widget.y_formatter = yrange_formatter
 
    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()



Test().run()