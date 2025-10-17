from kivy.utils import platform
from kivy.config import Config

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    Config.set('input', 'mouse', 'mouse,disable_on_activity')
else:
    #for android, we remove mouse input to not get extra touch 
    Config.remove_option('input', 'mouse')

import matplotlib.pyplot as plt
import numpy as np
from kivy.lang import Builder
from kivy.properties import NumericProperty,StringProperty
from kivy.app import App
import kivy_matplotlib_widget
from kivy_matplotlib_widget.uix.hover_widget import add_hover,HightChartHover
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from kivy.core.window import Window
import time

desired_ratio = 16 / 9
win_width=1000
Window.size = (win_width,int(win_width / desired_ratio) )  

KV = """
Screen
    figure_wgt:figure_wgt
    figure_wgt2:figure_wgt2
    BoxLayout:
        
        orientation:'vertical'
        BoxLayout:
            size_hint_y:0.2
            Button:
                text:"home"
                on_press:app.home()

            ToggleButton:
                group:'touch_mode'
                state:'down'
                text:"pan x" 
                on_press:
                    app.set_touch_mode('pan_x')
                    self.state='down'

        BoxLayout:
            size_hint_y:0.1
            Button:
                text:"1m"
                on_press:app.set_range_step("1m")

            Button:
                text:"6m"
                on_press:app.set_range_step("6m")

            Button:
                text:"1y"
                on_press:app.set_range_step("1y")

            Button:
                text:"None"
                on_press:app.set_range_step(None)
                    
        BoxLayout:
            MatplotFigureSubplot:
                id:figure_wgt
                fast_draw:False
                autoscale_tight:True
                autoscale_axis:'x'
                auto_cursor:True
        BoxLayout:
            size_hint_y:0.2
            MatplotFigureSubplot:
                id:figure_wgt2
                current_selector:'span' 
                autoscale_tight:True
                autoscale_axis:'x'
                
"""

# Change the style of plot (matplolib<3.6 can use "seaborn-darkgrid")
plt.style.use('seaborn-v0_8-darkgrid')

class TestApp(App):
    last_callback_time=None  
    
    def build(self):
        self.screen=Builder.load_string(KV)
        return self.screen


    def on_start(self, *args):     
        
        import numpy as np

        # Create datetime array with daily intervals
        start_date = '2015-02-17'
        end_date = '2017-02-16'
        xdata = np.arange(
            np.datetime64(start_date),
            np.datetime64(end_date) + np.timedelta64(1, 'D'),
            np.timedelta64(1, 'D')
        )
        
        # Parameters for the sinusoidal wave
        num_days = len(xdata)
        x = np.linspace(0, 2 * np.pi, num_days)  # Create a range of values for the sine wave
        amplitude = 30  # Amplitude of the sine wave
        baseline = 120  # Baseline value
        noise_strength = 20  # Strength of random noise
        
        # Generate the sinusoidal random array
        ydata = baseline + amplitude * np.sin(x) + np.random.uniform(-noise_strength, noise_strength, size=num_days)


        fig, ax = plt.subplots()
        ax.plot(xdata, ydata,label='line1')
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_formatter(formatter)

        self.screen.figure_wgt.figure = fig
        self.screen.figure_wgt.touch_mode="pan_x"
        self.screen.figure_wgt.cursor_xaxis_formatter = mdates.DateFormatter("%Y-%m-%#d")
        
        self.screen.figure_wgt.autoscale()
        
        add_hover(self.screen.figure_wgt,mode='desktop',hover_widget=HightChartHover())
        
        fig2, ax2 = plt.subplots()
        fig2.subplots_adjust(bottom=0.3, top=0.99)
        line, = ax2.plot(xdata, ydata)
        ax2.xaxis.set_major_locator(locator)
        ax2.xaxis.set_major_formatter(formatter) 
        ax2.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        ax2.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        ax2.grid(False)
        plt.subplots_adjust(bottom=0.2)
        self.screen.figure_wgt2.figure = fig2  
        self.screen.figure_wgt2.touch_mode='selector' 
       
        
        self.screen.figure_wgt2.set_line(line)
        self.screen.figure_wgt2.set_callback(self.callback_selection)
        self.screen.figure_wgt2.set_callback_clear(self.callback_clear)
        self.screen.figure_wgt2.selector.resize_wgt.span_color="blue"
        
        self.screen.figure_wgt2.autoscale()

    def set_range_step(self,step):
        selector = self.screen.figure_wgt2.selector.resize_wgt
        xlim = selector.ax.get_xlim()
        figure_wgt = self.screen.figure_wgt
        left_bound = float(figure_wgt.x +selector.ax.bbox.bounds[0])
        right_bound = float(figure_wgt.x +selector.ax.bbox.bounds[2] +selector.ax.bbox.bounds[0] )
        top_bound = float(figure_wgt.y +selector.ax.bbox.bounds[3] + selector.ax.bbox.bounds[1])
        bottom_bound = float(figure_wgt.y +selector.ax.bbox.bounds[1])
        
        width = right_bound-left_bound
        
        if step=="1m":

            left_bound,right_bound = selector.to_widget(left_bound,right_bound)
            selector.x = left_bound
            
            new_date =  mdates.date2num(mdates.num2date(xlim[0]) + timedelta(days=30))

            xy = selector.ax.transData.transform([(new_date, 0)]) 
            xy2 = selector.ax.transData.transform([(xlim[0], 0)])

            # selector.width = float(xy[0][0]) - figure_wgt.x
            selector.y = bottom_bound - figure_wgt.y
            selector.size = (float(xy[0][0]) - float(xy2[0][0]),top_bound-bottom_bound) 
                    
            selector.opacity=1
            selector.verts = selector._get_box_data()
            self.callback_selection(selector)            
        elif step=="6m":
            left_bound,right_bound = selector.to_widget(left_bound,right_bound)
            selector.x = left_bound
            
            new_date = mdates.date2num(mdates.num2date(xlim[0]) + timedelta(days=6*30))

            xy = selector.ax.transData.transform([(new_date, 0)]) 
            xy2 = selector.ax.transData.transform([(xlim[0], 0)])

            selector.y = bottom_bound - figure_wgt.y
            selector.size = (float(xy[0][0]) - float(xy2[0][0]),top_bound-bottom_bound)
            selector.opacity=1
            selector.verts = selector._get_box_data()
            self.callback_selection(selector)            
        elif step=="1y":
            left_bound,right_bound = selector.to_widget(left_bound,right_bound)
            selector.x = left_bound
            
            new_date = mdates.date2num(mdates.num2date(xlim[0]) + timedelta(days=365))

            xy = selector.ax.transData.transform([(new_date, 0)]) 
            xy2 = selector.ax.transData.transform([(xlim[0], 0)])

            # selector.width = float(xy[0][0]) - figure_wgt.x
            selector.y = bottom_bound - figure_wgt.y
            selector.size = (float(xy[0][0]) - float(xy2[0][0]),top_bound-bottom_bound)
            selector.opacity=1
            selector.verts = selector._get_box_data()
            self.callback_selection(selector)
        else:
            self.callback_clear()  
            
    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode 
        
    def home(self):
        self.screen.figure_wgt.home() 
        self.screen.figure_wgt2.home()  
        self.callback_clear()        
        
    def callback_selection(self,selectot_wgt):
        """

        Parameters
        ----------
        selectot_wgt : rectangle widget
            USEFUL attributes:
            verts: axis coordinate of selector rectangle box
            ind: indice of selected pts (scatter)
            collection: matplotlib collection instance
            fc: matplotlib collection facecolor
            ind_line: indice of selected pts (line)
            line: matplotlib line instance

        Returns
        -------
        None.

        """
        max_callback_rate = None #set a value here (ex: 1/30) if the graph update is laggy. Can happen with big data
        #trick to improve dynamic callback fps
        if max_callback_rate is not None:
            if self.last_callback_time is None:
                self.last_callback_time = time.time()
                
            elif time.time() - self.last_callback_time < max_callback_rate:
                print('skip')
                return
            else:
                # print( time.time() - self.last_callback_time)
                self.last_callback_time=None
                
        xmin = min(np.array(selectot_wgt.verts)[:,0])
        xmax = max(np.array(selectot_wgt.verts)[:,0])
        
        self.screen.figure_wgt.figure.axes[0].set_xlim(xmin,xmax)

        self.screen.figure_wgt.figure.canvas.draw_idle()

    def callback_clear(self):
        
        self.screen.figure_wgt2.selector.resize_wgt.clear_selection()
        self.screen.figure_wgt2.figure.canvas.draw_idle()      


if __name__ == '__main__':
    TestApp().run()