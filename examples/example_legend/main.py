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
from graph_generator import GraphGenerator
import kivy_matplotlib_widget  #register all widgets to kivy register

KV = '''

Screen
    figure_wgt:figure_wgt
    legend_wgt:legend_wgt
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
            MatplotFigure:
                id:figure_wgt
            LegendRv:
                id:legend_wgt
                figure_wgt:figure_wgt
                size_hint_x:0.3  
                text_color: 1,0,1,1
                text_font:'DejaVuSans'
                text_font_size:dp(24)
                box_height:dp(60)
        BoxLayout:
            size_hint_y:0.2
            Button:
                text:"add plot"
                on_release:app.add_plot()    
            Button:
                text:"remove plot"
                on_release:app.remove_last_plot()                   
'''


class Test(App):
    lines = []

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        mygraph = GraphGenerator()
        
        self.screen.figure_wgt.figure = mygraph.fig
        
        #register lines instance if need to be update
        for line in self.screen.figure_wgt.axes.lines:
            self.lines.append(line)
        
        self.screen.legend_wgt.set_data(self.lines)

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        
    def add_plot(self):
        from random import randint

        x=[randint(0, 9) for p in range(0, 10)]
        x.sort()
        y=[randint(0, 9) for p in range(0, 10)]
        label_id = str(len(self.screen.legend_wgt.data)+1)      
        added_line,=self.screen.figure_wgt.axes.plot(x, y,label='line' + label_id)
        self.screen.legend_wgt.add_data(added_line)

    def remove_last_plot(self):
        #remove last line
        if len(self.screen.figure_wgt.axes.lines)!=0:
            last_line = self.screen.figure_wgt.axes.lines[-1]
            self.screen.legend_wgt.remove_data(last_line)
        
Test().run()