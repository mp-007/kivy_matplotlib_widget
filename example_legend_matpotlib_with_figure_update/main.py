import matplotlib as mpl
import matplotlib.pyplot as plt
from kivy.metrics import dp

#optimized draw on Agg backend
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0
mpl.rcParams['agg.path.chunksize'] = 1000

font_size_axis_title=dp(13)
font_size_axis_tick=dp(12)        

seaborn_package=True
try:
    import seaborn as sns
except:
    seaborn_package=False
    
#avoid conflict between mouse provider and touch (very important with touch device)
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
from kivy.core.window import Window
import numpy as np
from random import randint
from legend_widget import MatplotlibInteractiveLegend

KV = '''
#:import MatplotFigure graph_widget

Screen
    figure_wgt:figure_wgt
    
    BoxLayout:
        orientation:'vertical'
        BoxLayout:
            size_hint_y:0.3
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
                text:"drag legend"  
                on_release:
                    app.set_touch_mode('drag_legend')
                    self.state='down'                     

        MatplotFigure:
            id:figure_wgt    
        BoxLayout:
            size_hint_y:0.2
            Button:
                text:"change graph"
                on_release:app.change_graph()            
            Button:
                text:"add line or scatter"
                on_release:app.add_line_or_scatter_graph()             
'''


class Test(App):
    current_figure=1

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):


        fig, ax = plt.subplots(1, 1)
        fig.subplots_adjust(right=0.7)
        
        
        for i in range(10):
            x=[randint(0, 9) for p in range(0, 10)]
            x.sort()
            y=[randint(0, 9) for p in range(0, 10)]
            ax.plot(x, y,label='line' + str(i+1))

        self.screen.figure_wgt.figure = ax.figure
        ax.legend(loc=(1.04, 0.2))
        
        MatplotlibInteractiveLegend(self.screen.figure_wgt)
   
    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode


    def home(self):
        self.screen.figure_wgt.home()

    def change_graph(self):   
        if self.current_figure==1:
            fig, ax = plt.subplots(1, 1)
    
            x = [2,4,5,7,6,8,9,11,12,12]
            y = [1,2,3,4,5,6,7,8,9,10]
            
            sc1 = ax.scatter(x, y, s=30, color='magenta', alpha=0.7, marker='x', picker=3,label='scatter')
            sc2 = ax.scatter(np.array(x)+2, np.array(y)+1, s=30, color='r', alpha=0.7, marker='x', picker=3,label='scatter2')
            sc3 = ax.scatter(np.array(x)+3, np.array(y)+3, s=30, color='k', alpha=0.7, marker='x', picker=3,label='scatter3')
            ax.legend(loc=4)
            
            self.screen.figure_wgt.figure = ax.figure
            self.screen.figure_wgt.fast_draw = False #update axis during pan/zoom
            
            MatplotlibInteractiveLegend(self.screen.figure_wgt)
            self.current_figure=2
            
        elif self.current_figure==2:
            fig, ax = plt.subplots(1, 1)
            fig.subplots_adjust(right=0.7)
            
            
            for i in range(10):
                x=[randint(0, 9) for p in range(0, 10)]
                x.sort()
                y=[randint(0, 9) for p in range(0, 10)]
                ax.plot(x, y,label='line' + str(i+1))
    
            self.screen.figure_wgt.figure = ax.figure
            ax.legend(loc=(1.04, 0.2))
            
            MatplotlibInteractiveLegend(self.screen.figure_wgt) 
            self.current_figure=1
            
    def add_line_or_scatter_graph(self): 
        if self.current_figure==1:
            ax=self.screen.figure_wgt.figure.axes[0]
            x=[randint(0, 9) for p in range(0, 10)]
            x.sort()
            y=[randint(0, 9) for p in range(0, 10)]
            ax.plot(x, y,label='line' + str(len(ax.get_lines())+1))
    
            self.screen.figure_wgt.figure = ax.figure
            ax.legend(loc=(1.04, 0.2))
            self.home()
            MatplotlibInteractiveLegend(self.screen.figure_wgt)
            
        elif self.current_figure==2:
            ax=self.screen.figure_wgt.figure.axes[0]
            x = np.array([2,4,5,7,6,8,9,11,12,13])+randint(7, 12)*0.1
            y = np.array([1,2,3,4,5,6,7,8,9,10])+randint(7, 12)*0.1
            
            sc_x = ax.scatter(x, y, s=30, color='magenta', alpha=0.7, marker='x', picker=3,label='scatter' + str(len(ax.collections)+1))  
            ax.legend(loc=4)
            self.home()
            MatplotlibInteractiveLegend(self.screen.figure_wgt)
Test().run()