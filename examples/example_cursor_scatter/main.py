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

KV = '''
#:import MatplotFigureScatter graph_widget_scatter

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
                on_press:
                    app.set_touch_mode('pan')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"cursor"  
                on_press:
                    app.set_touch_mode('cursor')
                    self.state='down'                
        MatplotFigureScatter:
            id:figure_wgt
            multi_xdata:True
            
        BoxLayout:
            size_hint_y:0.2

            ToggleButton:
                group:'xaxis_formatter'
                state:'down'
                text:"xaxis '%.0f'" 
                on_release:
                    app.set_xaxis_formatter(1)
                    self.state='down'    
                     
            ToggleButton:
                group:'xaxis_formatter'
                text:"xaxis '%.2f'" 
                on_release:
                    app.set_xaxis_formatter(2)
                    self.state='down'            

'''

#see all matplotib formatter at
#https://matplotlib.org/stable/api/ticker_api.html#tick-formatting
from matplotlib.ticker import FuncFormatter,FormatStrFormatter


def y_axis_formatter(x, pos):
    """custom y axis formatter
    
    Args:
        x : value axis
        pos: tick position
    """    
    if round(x,3)==0:
       return '%.0f' % (x)  
    elif abs(x)>1 and abs(x)<=10:
        return '%.2f' % (x)
    elif abs(x)>10 and abs(x)<=100:
        return '%.1f' % (x)  
    elif abs(x)>100:
        return '%.0f' % (x) 
    else:
        return '%.3f' % (x)   


class Test(App):

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        mygraph = GraphGenerator()
        
        self.screen.figure_wgt.figure = mygraph.fig
        self.screen.figure_wgt.scatter_label  = ['pt' + str(i) for i in mygraph.ptid]

        #register scatter instance if need to be update
        self.screen.figure_wgt.register_scatters([mygraph.scatter1])        
        self.screen.figure_wgt.register_lines([]) #create cursor

        ax=self.screen.figure_wgt.figure.axes[0]
        ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        self.screen.figure_wgt.cursor_xaxis_formatter = ax.xaxis.get_major_formatter()
        self.screen.figure_wgt.cursor_yaxis_formatter = FuncFormatter(y_axis_formatter)

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()

    def set_xaxis_formatter(self,value):
        ax=self.screen.figure_wgt.figure.axes[0]
        if value==1:            
            ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
            self.screen.figure_wgt.cursor_xaxis_formatter = ax.xaxis.get_major_formatter()
            ax.figure.canvas.draw_idle()
            ax.figure.canvas.flush_events()  
            
        elif value==2:
            ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
            self.screen.figure_wgt.cursor_xaxis_formatter = ax.xaxis.get_major_formatter()
            ax.figure.canvas.draw_idle()
            ax.figure.canvas.flush_events() 
        
Test().run()