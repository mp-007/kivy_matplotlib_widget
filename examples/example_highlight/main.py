"""Highlight example

note: to activate the highlight, you need to set a hover and 
you need set highlight_hover:True in your figure widget
    
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
plt.switch_backend('Agg')
import numpy as np
from kivy_matplotlib_widget.uix.hover_widget import add_hover,HightChartHover

#remove font_manager "debug" from matplotib
import logging
logging.getLogger('matplotlib.font_manager').disabled = True

# Create data using NumPy
x = np.arange(1, 11)
y1 = np.random.randn(10)
y2 = np.random.randn(10) + np.arange(1, 11)
y3 = np.random.randn(10) + np.arange(11, 21)
y4 = np.random.randn(10) + np.arange(6, 16)
y5 = np.random.randn(10) + np.arange(4, 14) + np.array([0, 0, 0, 0, 0, 0, 0, -3, -8, -6])
y6 = np.random.randn(10) + np.arange(2, 12)
y7 = np.random.randn(10) + np.arange(5, 15)
y8 = np.random.randn(10) + np.arange(4, 14)

# Store the data in a dictionary (similar to a DataFrame)
data = {
    'x': x,
    'y1': y1,
    'y2': y2,
    'y3': y3,
    'y4': y4,
    'y5': y5,
    'y6': y6,
    'y7': y7,
    'y8': y8
}

# Change the style of the plot
plt.style.use('seaborn-darkgrid')

# Set figure size
fig = plt.figure(figsize=(8, 6))

# Plot the data
i = 1
for key in data:
    if key != 'x':  # Exclude 'x' from the loop
        plt.plot(data['x'], data[key], label='line' + str(i))
        i += 1
 
# Change x axis limit
plt.xlim(0,12)


KV = '''
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
            auto_cursor:True
            highlight_hover:True
            #highlight_prop:{'linewidth':8}
            #highlight_prop:{'linewidth':8,'color':'y','alpha':0.5}
            #highlight_alpha:1.0

        BoxLayout:
            size_hint_y:0.2
            ToggleButton:
                group:'highlight'
                state:'down'
                text:"highlight 1" 
                on_release:
                    app.set_highlight(1)
                    self.state='down'  
            ToggleButton:
                group:'highlight'
                text:"highlight 2"  
                on_release:
                    app.set_highlight(2)
                    self.state='down'   
            ToggleButton:
                group:'highlight'
                text:"highlight 3"  
                on_release:
                    app.set_highlight(3)
                    self.state='down'                      
            
'''


class Test(App):
    lines = []

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):

        self.screen.figure_wgt.figure = fig     
        
        #highlight can be activate also in touch mode. 
        #In this case, you need to activate the cursor mode to make it work
        add_hover(self.screen.figure_wgt,mode='desktop',hover_widget=HightChartHover())

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        
    def set_highlight(self,num):
        if num==1:
            # To set this highlight directly in kv 
            # (note:highlight_alpha is by defaul 0.2 and normally the line property alpha is 1.0)
            """
            MatplotFigure:
                id:figure_wgt
                auto_cursor:True
                highlight_hover:True
            """
            self.screen.figure_wgt.highlight_prop={'linewidth':1,'alpha':1.0}
            self.screen.figure_wgt.highlight_alpha=0.2
        elif num==2:
            # To set this highlight directly in kv 
            # (note:this highlight change the linewidth of the selected line
            """
            MatplotFigure:
                id:figure_wgt
                auto_cursor:True
                highlight_hover:True
                highlight_prop:{'linewidth':8}
                
            """            
            self.screen.figure_wgt.highlight_prop={'linewidth':8,'alpha':1.0}
            self.screen.figure_wgt.highlight_alpha=0.2
        elif num==3:
            # To set this highlight directly in kv 
            # (note:this highlight will create a new transparent yellow line over each selected line)
            """
            MatplotFigure:
                id:figure_wgt
                auto_cursor:True
                highlight_hover:True
                highlight_prop:{'linewidth':8,'color':'y','alpha':0.5}
                highlight_alpha:1.0
                
            """              
            self.screen.figure_wgt.highlight_prop={'linewidth':8,'color':'y','alpha':0.5}
            self.screen.figure_wgt.highlight_alpha=1.0
        
Test().run()