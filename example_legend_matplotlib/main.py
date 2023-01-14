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
    figure_wgt1:figure_wgt1
    figure_wgt2:figure_wgt2
    figure_wgt3:figure_wgt3
    figure_wgt4:figure_wgt4
    
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

        BoxLayout:
            orientation:'vertical'
            BoxLayout:
                MatplotFigure:
                    id:figure_wgt1
                    legend_do_scroll_x:False
                MatplotFigure:
                    id:figure_wgt2
            BoxLayout:
                MatplotFigure:
                    id:figure_wgt3

                MatplotFigure:
                    id:figure_wgt4                  
            
'''


class Test(App):
    lines = []
    instance_dict = dict()

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

        self.screen.figure_wgt1.figure = ax.figure
        ax.legend(loc=(1.04, -0.2))
        
        MatplotlibInteractiveLegend(self.screen.figure_wgt1)
        
        fig2, ax2 = plt.subplots(1, 1)

        x = [2,4,5,7,6,8,9,11,12,12]
        y = [1,2,3,4,5,6,7,8,9,10]
        
        sc1 = ax2.scatter(x, y, s=30, color='magenta', alpha=0.7, marker='x', picker=3,label='scatter')
        sc2 = ax2.scatter(np.array(x)+2, np.array(y)+1, s=30, color='r', alpha=0.7, marker='x', picker=3,label='scatter2')
        sc3 = ax2.scatter(np.array(x)+3, np.array(y)+3, s=30, color='k', alpha=0.7, marker='x', picker=3,label='scatter3')
        ax2.legend(loc=4)
        
        self.screen.figure_wgt2.figure = ax2.figure
        self.screen.figure_wgt2.fast_draw = False #update axis during pan/zoom
        
        MatplotlibInteractiveLegend(self.screen.figure_wgt2)
        
        fig3, ax3 = plt.subplots(1, 1)
        x = np.linspace(0, 1)
        
        # Plot the lines y=x**n for n=1..4.
        for n in range(1, 5):
            ax3.plot(x, x**n, label="n={0}".format(n))
        ax3.legend(loc="upper left",
                    ncol=2, shadow=True, title="Legend", fancybox=True)
        ax3.get_legend().get_title().set_color("red")

        self.screen.figure_wgt3.figure = ax3.figure
        
        MatplotlibInteractiveLegend(self.screen.figure_wgt3)

        fig4, ax4 = plt.subplots(1, 1)
        if seaborn_package:
            df = sns.load_dataset("penguins")
            sns.barplot(ax=ax4,data=df, x="island", y="body_mass_g", hue="sex")
        self.screen.figure_wgt4.figure = ax4.figure
        self.screen.figure_wgt4.fast_draw = False #update axis during pan/zoom 
        ax4.legend(title="sex",loc=1)                            
        MatplotlibInteractiveLegend(self.screen.figure_wgt4,legend_handles='variante')
        
           
    def set_touch_mode(self,mode):
        self.screen.figure_wgt1.touch_mode=mode
        self.screen.figure_wgt2.touch_mode=mode
        self.screen.figure_wgt3.touch_mode=mode
        self.screen.figure_wgt4.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        
Test().run()