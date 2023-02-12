from kivy.utils import platform

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
from graph_generator import GraphGenerator
from hover_widget import add_hover,HoverVerticalText,InfoHover
from matplotlib.ticker import FormatStrFormatter

KV = '''
#:import MatplotFigure graph_widget

Screen
    figure_wgt:figure_wgt
    figure_wgt2:figure_wgt2
    figure_wgt3:figure_wgt3
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
            ToggleButton:
                group:'touch_mode'
                text:"cursor"  
                on_release:
                    app.set_touch_mode('cursor')
                    self.state='down' 
    
        MatplotFigure:
            id:figure_wgt

        MatplotFigure:
            id:figure_wgt2 
                
        MatplotFigure:
            id:figure_wgt3               
'''

class Test(App):

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        mygraph = GraphGenerator()
        mygraph.fig.axes[0].set_title('General hover touch behavior (press cursor)')
        self.screen.figure_wgt.figure = mygraph.fig
        
        ax=self.screen.figure_wgt.figure.axes[0]
        self.screen.figure_wgt.register_lines(list(ax.get_lines()))
        
        #set x/y formatter for hover data
        self.screen.figure_wgt.cursor_xaxis_formatter = FormatStrFormatter('%.2f')
        self.screen.figure_wgt.cursor_yaxis_formatter = FormatStrFormatter('%.1f')  
        
        #add general hover to the figure (with normal touch mode)
        add_hover(self.screen.figure_wgt,mode='touch')
        
        mygraph2 = GraphGenerator()
        mygraph2.fig.axes[0].set_title('Set HoverVerticalText hover with desktop behavior')
        self.screen.figure_wgt2.figure = mygraph2.fig
        ax2=self.screen.figure_wgt2.figure.axes[0]
        self.screen.figure_wgt2.register_lines(list(ax2.get_lines()))
        
        #set x/y formatter for hover data
        self.screen.figure_wgt2.cursor_xaxis_formatter = FormatStrFormatter('%.2f')
        self.screen.figure_wgt2.cursor_yaxis_formatter = FormatStrFormatter('%.1f')       
   
        #add custom hover widget "HoverVerticalText" hover to the figure.
        #decktop mode will show the hover on mouse position
        add_hover(self.screen.figure_wgt2,mode='desktop',label_x='Time',label_y='Amplitude',hover_widget=HoverVerticalText())

        mygraph3 = GraphGenerator()
        mygraph3.fig.axes[0].set_title('Set InfoHover with desktop behavior')
        self.screen.figure_wgt3.figure = mygraph3.fig
        ax3=self.screen.figure_wgt3.figure.axes[0]
        self.screen.figure_wgt3.register_lines(list(ax3.get_lines()))
        
        #set x/y formatter for hover data
        self.screen.figure_wgt3.cursor_xaxis_formatter = FormatStrFormatter('%.1f')
        self.screen.figure_wgt3.cursor_yaxis_formatter = FormatStrFormatter('%.1f')  
            
        #add custom hover widget "InfoHover" hover to the figure.
        add_hover(self.screen.figure_wgt3,mode='desktop',hover_widget=InfoHover())
        

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode
        self.screen.figure_wgt2.touch_mode=mode
        self.screen.figure_wgt3.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        self.screen.figure_wgt2.home()
        self.screen.figure_wgt3.home()
        
Test().run()