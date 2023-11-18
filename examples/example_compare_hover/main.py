from kivy.utils import platform

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
from graph_generator import GraphGenerator
from hover_widget import add_hover,HoverVerticalText,InfoHover,TagCompareHover
from matplotlib.ticker import FormatStrFormatter

KV = '''
#:import MatplotFigure graph_widget

Screen
    figure_wgt:figure_wgt
    figure_wgt2:figure_wgt2
    BoxLayout:
        orientation:'vertical'
        BoxLayout:
            size_hint_y:0.15
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
            size_hint_y:0.15
            ToggleButton:
                group:'hover_mode'
                text:"nearest hover"  
                on_release:
                    app.change_hover_type('nearest')
                    self.state='down' 
            ToggleButton:
                group:'hover_mode'
                text:"compare hover"  
                state:'down'
                on_release:
                    app.change_hover_type('compare')
                    self.state='down'                    

        MatplotFigure:
            id:figure_wgt 

        MatplotFigure:
            id:figure_wgt2                   
'''

class Test(App):

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        mygraph = GraphGenerator()
        self.screen.figure_wgt.figure = mygraph.fig
        
        ax=self.screen.figure_wgt.figure.axes[0]
        self.screen.figure_wgt.register_lines(list(ax.get_lines()))
        ax.set_title('General compare hover')
        
        #set x/y formatter for hover data
        self.screen.figure_wgt.cursor_xaxis_formatter = FormatStrFormatter('%.2f')
        self.screen.figure_wgt.cursor_yaxis_formatter = FormatStrFormatter('%.1f')  
        
        #add compare hover
        add_hover(self.screen.figure_wgt,mode='desktop',hover_type='compare')        

        ##figure2
        mygraph2 = GraphGenerator()
        self.screen.figure_wgt2.figure = mygraph2.fig
        
        ax=self.screen.figure_wgt2.figure.axes[0]
        self.screen.figure_wgt2.register_lines(list(ax.get_lines()))
        ax.set_title('Tag compare hover')
        
        #set x/y formatter for hover data
        self.screen.figure_wgt2.cursor_xaxis_formatter = FormatStrFormatter('%.2f')
        self.screen.figure_wgt2.cursor_yaxis_formatter = FormatStrFormatter('%.1f')  
        
        #add compare hover
        add_hover(self.screen.figure_wgt2,mode='desktop',hover_type='compare',hover_widget=TagCompareHover()) 
        
    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode
        self.screen.figure_wgt2.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        self.screen.figure_wgt2.home()
        
    def change_hover_type(self,hover_type):
        add_hover(self.screen.figure_wgt,mode='desktop',hover_type=hover_type)
        add_hover(self.screen.figure_wgt2,mode='desktop',hover_type=hover_type)
        
Test().run()