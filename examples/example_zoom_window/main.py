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
import time
    

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
                text:"Rectangle selector" 
                on_press:
                    app.set_touch_mode('selector')
                    self.state='down'

            ToggleButton:
                group:'touch_mode'
                text:"pan" 
                on_press:
                    app.set_touch_mode('pan')
                    self.state='down'
                    
        BoxLayout:            
            MatplotFigureSubplot:
                id:figure_wgt
                current_selector:'rectangle'

            MatplotFigureSubplot:
                id:figure_wgt2
                             
                
"""


class TestApp(App):
    last_callback_time=None  

    def build(self):
        self.screen=Builder.load_string(KV)
        return self.screen


    def on_start(self, *args):
        
        # Fixing random state for reproducibility
        np.random.seed(19680801)
        
        figsrc, axsrc = plt.subplots(figsize=(3.7, 3.7))
        figzoom, axzoom = plt.subplots(figsize=(3.7, 3.7))
        axsrc.set(xlim=(0, 1), ylim=(0, 1), autoscale_on=False,
                  title='Click to zoom')
        axzoom.set(xlim=(0, 1), ylim=(0, 1), autoscale_on=False,
                   title='Zoom window')
        
        x, y, s, c = np.random.rand(4, 200)
        s *= 200
        
        axsrc.scatter(x, y, s, c)
        axzoom.scatter(x, y, s, c)
    
        self.screen.figure_wgt.figure = figsrc
        self.screen.figure_wgt.touch_mode='selector' 
        
        # self.screen.figure_wgt.current_selector = 'rectangle'
        self.screen.figure_wgt.set_callback(self.callback_selection)
        self.screen.figure_wgt.set_callback_clear(self.callback_clear)
        
        self.screen.figure_wgt2.figure = figzoom

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode 
        
    def home(self):
        self.screen.figure_wgt.home() 
        self.screen.figure_wgt2.home()          
        
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
                return
            else:
                # print( time.time() - self.last_callback_time)
                self.last_callback_time=None

        xmin = min(np.array(selectot_wgt.verts)[:,0])
        xmax = max(np.array(selectot_wgt.verts)[:,0])

        ymin = min(np.array(selectot_wgt.verts)[:,1])
        ymax = max(np.array(selectot_wgt.verts)[:,1])
        
        self.screen.figure_wgt2.figure.axes[0].set_xlim(xmin,xmax)
        self.screen.figure_wgt2.figure.axes[0].set_ylim(ymin,ymax)

        self.screen.figure_wgt2.figure.canvas.draw_idle()

    def callback_clear(self):
        
        self.screen.figure_wgt.selector.resize_wgt.clear_selection()
        self.screen.figure_wgt.figure.canvas.draw_idle()      


if __name__ == '__main__':
    TestApp().run()