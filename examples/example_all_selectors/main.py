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
                text:"pan" 
                on_press:
                    app.set_touch_mode('pan')
                    self.state='down'    
                    
            ToggleButton:
                group:'touch_mode'
                text: 'rectangle selector'
                on_press: 
                    app.set_selector('rectangle')
                    app.set_touch_mode('selector')  
                    self.state='down'                    
                    
            ToggleButton:
                group:'touch_mode'
                text: 'lasso selector'
                on_press: 
                    app.set_selector('lasso')
                    app.set_touch_mode('selector')  
                    self.state='down'
                    
            ToggleButton:
                group:'touch_mode'
                text: 'ellipse selector'
                on_press: 
                    app.set_selector('ellipse')
                    app.set_touch_mode('selector')  
                    self.state='down'                    

            ToggleButton:
                group:'touch_mode'
                text: 'span selector'
                on_press: 
                    app.set_selector('span')
                    app.set_touch_mode('selector')  
                    self.state='down'   
                    
            Button:
                text:"clear selection"
                on_release:app.clear_selection()                    
            
        BoxLayout:
            MatplotFigureSubplot:
                id:figure_wgt
                current_selector:'lasso'

            MatplotFigure:
                id:figure_wgt2 
                current_selector:'lasso'
        
        BoxLayout:
            size_hint_y:0.1
            
            Label:
                text:'Number of selected points: ' + str(app.npts)
            Label:
                text:'Maximum value in selection: ' + app.max_value               
                
"""



class TestApp(App):
    npts = NumericProperty(0)
    max_value = StringProperty("")

    def build(self):
        self.screen=Builder.load_string(KV)
        return self.screen


    def on_start(self, *args):
        
        # Fixing random state for reproducibility
        np.random.seed(19680801)
        
        data = np.random.rand(100, 2)
        
        subplot_kw = dict(xlim=(0, 1), ylim=(0, 1), autoscale_on=False)
        fig, ax = plt.subplots(subplot_kw=subplot_kw)
        
        pts = ax.scatter(data[:, 0], data[:, 1], s=80)
        
        self.screen.figure_wgt.figure = fig
        self.screen.figure_wgt.set_collection()
        self.screen.figure_wgt.set_callback(self.callback_selection)
        self.screen.figure_wgt.set_callback_clear(self.callback_clear)
        
        xdata = np.linspace(0,9*np.pi, num=301)
        ydata = np.sin(xdata)*np.cos(xdata*2.4)

        fig2, ax2 = plt.subplots()
        line, = ax2.plot(xdata, ydata)
        self.point, = ax2.plot([],[], marker="o", color="crimson")
        self.text = ax2.text(0,0,"")
        self.screen.figure_wgt2.figure = fig2
        self.screen.figure_wgt2.set_line(line)
        self.screen.figure_wgt2.set_callback(self.callback_selection2)
        self.screen.figure_wgt2.set_callback_clear(self.callback_clear2)

    def set_selector(self,selector):
        self.screen.figure_wgt.current_selector = selector
        self.screen.figure_wgt2.current_selector = selector
        
    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode 
        self.screen.figure_wgt2.touch_mode=mode 
        
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
            ind: indice of selected pts
            collection: matplotlib collection instance
            fc: matplotlib collection facecolor
            ind_line: indice of selected pts (line)
            line: matplotlib line instance

        Returns
        -------
        None.

        """
        
        #get number of selected points
        self.npts= len(selectot_wgt.ind)
        
    def callback_selection2(self,selectot_wgt):
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
        
        #get maxium value in selection
        ind_line= selectot_wgt.ind_line  
        line_instance = selectot_wgt.line
        
        xdata,ydata = line_instance.get_data()
        xmasked = xdata[ind_line]
        ymasked = ydata[ind_line]

        if len(xmasked) > 0:
            xmax = xmasked[np.argmax(ymasked)]
            ymax = ymasked.max() 
            self.max_value= f"{ymax:.3f}"
            tx = " xmax: {:.3f}\n ymax {:.3f}".format(xmax,ymax)
            self.point.set_data([xmax],[ymax])
            self.text.set_text(tx)
            self.text.set_position((xmax,ymax))    
            
        self.screen.figure_wgt2.figure.canvas.draw_idle()

    def callback_clear(self):
        self.screen.figure_wgt.selector.resize_wgt.clear_selection()
        self.npts = 0
            
    def callback_clear2(self):
        
        self.screen.figure_wgt2.selector.resize_wgt.clear_selection()
        self.max_value=""
        self.text.set_text("")
        self.point.set_data([],[])
        self.screen.figure_wgt2.figure.canvas.draw_idle()      
        
    def clear_selection(self):
        self.screen.figure_wgt.selector.resize_wgt.clear_selection()
        self.npts = 0
        self.screen.figure_wgt2.selector.resize_wgt.clear_selection()
        self.max_value=""
        self.text.set_text("")
        self.point.set_data([],[])
        self.screen.figure_wgt2.figure.canvas.draw_idle()

if __name__ == '__main__':
    TestApp().run()