from kivy.utils import platform

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
from kivy.metrics import dp

#optimized draw on Agg backend
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0
mpl.rcParams['agg.path.chunksize'] = 1000

#define some matplotlib figure parameters
mpl.rcParams['font.family'] = 'Verdana'
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['axes.linewidth'] = 1.0


KV = '''
#:import MatplotFigureTwinx graph_widget_twinx

Screen
    figure_wgt:figure_wgt
    BoxLayout:
        orientation:'vertical'
        BoxLayout:
            size_hint_y:0.2
            Button:
                text:"home"
                on_release:app.home()
            Button:
                text:"back"
                on_release:app.back()  
            Button:
                text:"forward"
                on_release:app.forward()                
            ToggleButton:
                group:'touch_mode'
                state:'down'
                text:"pan" 
                on_press:
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
        BoxLayout:
            size_hint_y:0.2                    
            ToggleButton:
                group:'touch_mode'
                text:"pan_x" 
                on_press:
                    app.set_touch_mode('pan_x')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"pan_y" 
                on_press:
                    app.set_touch_mode('pan_y')
                    self.state='down'                    
            ToggleButton:
                group:'touch_mode'
                text:"adjust_x"  
                on_press:
                    app.set_touch_mode('adjust_x')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"adjust_y"  
                on_press:
                    app.set_touch_mode('adjust_y')
                    self.state='down' 

            ToggleButton:
                text:"zoom_x"  
                on_press:
                    app.set_zoom_behavior('zoom_x',self.state)                     
            ToggleButton:
                text:"zoom_y"  
                on_press:
                    app.set_zoom_behavior('zoom_y',self.state)                     
        MatplotFigureTwinx:
            id:figure_wgt
            fast_draw:False
            
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
    lines = []

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        fig,ax1 = plt.subplots(1,1)
        ax2 = ax1.twinx()
        x = np.linspace(0,2*np.pi,100)
        ax1.plot(x,np.sin(x),'b')
        ax1.set_xlabel('Scaleable axis')
        ax1.set_ylabel('Scaleable axis')
        ax2.plot(x,np.sin(x+1),'r')
        ax2.set_ylabel('Static axis',weight='bold')
            
        self.screen.figure_wgt.figure = fig
        
        self.lines=fig.axes[0].lines + fig.axes[1].lines
        self.screen.figure_wgt.register_lines(self.lines)

        ax=self.screen.figure_wgt.figure.axes[0]
        ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        self.screen.figure_wgt.cursor_xaxis_formatter = ax.xaxis.get_major_formatter()
        self.screen.figure_wgt.cursor_yaxis_formatter = FuncFormatter(y_axis_formatter)        
        self.screen.figure_wgt.cursor_yaxis2_formatter = FormatStrFormatter('%.1f')

    def set_touch_mode(self,mode):
        if mode == 'adjust_y':
            #hide cursor before adust y axis (cursor position is not updatd for right axis)
            self.screen.figure_wgt.set_cross_hair_visible(False)
            self.screen.figure_wgt.figure.canvas.draw_idle()
            self.screen.figure_wgt.figure.canvas.flush_events()              
        self.screen.figure_wgt.touch_mode=mode
        
    def set_zoom_behavior(self,mode,state):
        boolean_val=True
        if state=='down':
            boolean_val=False
        if mode=='zoom_x':
            self.screen.figure_wgt.do_zoom_y=boolean_val
        elif mode=='zoom_y':
            self.screen.figure_wgt.do_zoom_x=boolean_val  
            
    def home(self):
        self.screen.figure_wgt.home()
    def back(self):
        self.screen.figure_wgt.back()   
    def forward(self):
        self.screen.figure_wgt.forward() 
        
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