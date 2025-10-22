
from kivy.config import Config

Config.set('input', 'mouse', 'mouse,disable_on_activity') #avoid double-click on touch device
Config.set('input', 'mouse', 'mouse,multitouch_on_demand') #disable red dot (user use mouse scroll for zooming)
Config.set('kivy', 'keyboard_mode', '') #disable keyboard mode

import multiprocessing as mp

import matplotlib.pyplot as plt
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (BooleanProperty, ColorProperty, NumericProperty,
                             StringProperty)

from kivy_matplotlib_widget.uix.hover_widget import (BaseHoverFloatLayout,
                                                     PlotlyHover,
                                                     TagCompareHover,
                                                     add_hover)
from kivy_matplotlib_widget.uix.legend_widget import \
    MatplotlibInteractiveLegend
from kivy_matplotlib_widget.uix.minmax_widget import add_minmax

KV = '''
Screen
    figure_wgt:figure_wgt
    
    BoxLayout:
        orientation:'vertical'
        
        canvas.before:
            Color:
                rgba: (1, 1, 1, 1)
            Rectangle:
                pos: self.pos
                size: self.size           
        KivyMatplotNavToolbar:
            id:nav_bar
            nav_icon:'all'
            hover_mode:'desktop'
            show_cursor_data:app.show_cursor_data
            compare_hover:app.compare_hover
            drag_legend:app.drag_legend
            figure_wgt:figure_wgt

        MatplotFigureSubplot:
            id:figure_wgt
            fast_draw:app.fast_draw
            auto_cursor:True
            interactive_axis:True
            max_hover_rate:app.max_hover_rate
            legend_do_scroll_x:app.legend_do_scroll_x
            hist_range:app.hist_range
            autoscale_tight:app.autoscale_tight  
            
'''

KV3D = '''
Screen
    figure_wgt_layout:figure_wgt_layout
    
    BoxLayout:
        orientation:'vertical'
        
        canvas.before:
            Color:
                rgba: (1, 1, 1, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        KivyMatplotNavToolbar:
            id:nav_bar
            nav_icon:'3D'
            figure_wgt_layout:figure_wgt_layout
        MatplotFigure3DLayout:
            id:figure_wgt_layout

'''

class GraphApp(App):
    figure = None
    figsize = None #figure size in pixel. inpu is a tuple ex: (1200,400)
    compare_hover = BooleanProperty(False)
    show_cursor_data = BooleanProperty(True)
    drag_legend = BooleanProperty(False)
    legend_do_scroll_x = BooleanProperty(True)
    max_hover_rate = NumericProperty(5/60,allownone=True) 
    fast_draw = BooleanProperty(False)
    hist_range = BooleanProperty(True)
    autoscale_tight = BooleanProperty(False)

    def __init__(self, 
                 figure,
                 show_cursor_data=True,
                 hover_widget=PlotlyHover,
                 compare_hover_widget=TagCompareHover,
                 compare_hover=False,
                 legend_instance=None, 
                 custom_handlers=None,
                 multi_legend=False,
                 drag_legend=False,
                 legend_do_scroll_x=True,
                 disable_interactive_legend=False,
                 max_hover_rate=5/60,
                 disable_hover=False,
                 fast_draw=True,
                 hist_range=True,
                 autoscale_tight=False,
                 register_cursor=None,
                 figsize=None,
                 **kwargs):
        """__init__ function class"""
        self.figure=figure
        self.hover_widget=hover_widget
        self.compare_hover_widget=compare_hover_widget
        self.legend_instance=legend_instance
        self.custom_handlers=custom_handlers
        self.multi_legend=multi_legend
        self.disable_interactive_legend=disable_interactive_legend
        self.disable_hover=disable_hover
        
        # print(self.figure.get())
        super(GraphApp, self).__init__(**kwargs)
        
        self.drag_legend=drag_legend
        self.show_cursor_data=show_cursor_data
        self.compare_hover=compare_hover
        self.legend_do_scroll_x=legend_do_scroll_x
        self.max_hover_rate=max_hover_rate
        self.fast_draw=fast_draw
        self.hist_range=hist_range
        self.autoscale_tight=autoscale_tight
        self.register_cursor=register_cursor
        self.figsize=figsize
        
    def build(self):
        if self.figsize:
            Window.size = self.figsize
         
        # Set minimum window size
        Window.minimum_width, Window.minimum_height = (200, 200)
            
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args): 
        if hasattr(self.figure,'get'):
            figure = self.figure.get()[0]
        else:
            figure= self.figure
            
        if isinstance(figure,list):
            self.screen.figure_wgt.figure = figure[0]

        else:
            self.screen.figure_wgt.figure = figure
            
        if self.register_cursor:
           self.screen.figure_wgt.register_cursor(pickables=self.register_cursor)
            
        if self.compare_hover:
            if self.compare_hover_widget:
                add_hover(self.screen.figure_wgt,mode='desktop',hover_type='compare',hover_widget=self.compare_hover_widget())
            else:
                add_hover(self.screen.figure_wgt,mode='desktop',hover_type='compare')
            
        if not self.disable_hover:
            if self.hover_widget:
                add_hover(self.screen.figure_wgt,mode='desktop',hover_widget=self.hover_widget())
            else:
                add_hover(self.screen.figure_wgt,mode='desktop')
        add_minmax(self.screen.figure_wgt)
        
        if not self.disable_interactive_legend:
            if len(self.screen.figure_wgt.figure.axes) > 0  and \
                (self.screen.figure_wgt.figure.axes[0].get_legend() or \
                 self.legend_instance):
    
                if self.multi_legend:
                    for i,current_legend_instance in enumerate(self.legend_instance):
                        if i==0:
                            MatplotlibInteractiveLegend(self.screen.figure_wgt,
                                                        legend_instance=current_legend_instance,
                                                        custom_handlers=self.custom_handlers[i])
                        else:
                            MatplotlibInteractiveLegend(self.screen.figure_wgt,
                                                        legend_instance=current_legend_instance,
                                                        custom_handlers=self.custom_handlers[i],
                                                        multi_legend=True)                        
    
                else:   
                    MatplotlibInteractiveLegend(self.screen.figure_wgt,
                                                legend_instance=self.legend_instance,
                                                custom_handlers=self.custom_handlers)

def app_window(plot_queue,**kwargs):

    GraphApp(plot_queue,**kwargs).run()
    
class GraphApp3D(App):
    figure = None
    figsize = None #figure size in pixel. inpu is a tuple ex: (1200,400)

    def __init__(self, 
                 figure,
                 figsize=None,
                 **kwargs):
        """__init__ function class"""
        self.figure=figure
        self.figsize=figsize
        
        # print(self.figure.get())
        super(GraphApp3D, self).__init__(**kwargs)
        
    def build(self):
        if self.figsize:
            Window.size = self.figsize
         
        # Set minimum window size
        Window.minimum_width, Window.minimum_height = (200, 200)        
        self.screen=Builder.load_string(KV3D)
        return self.screen

    def on_start(self, *args): 
        if hasattr(self.figure,'get'):
            figure = self.figure.get()[0]
        else:
            figure= self.figure
            
        if isinstance(figure,list):
            self.screen.figure_wgt_layout.figure_wgt.figure = figure[0]

        else:
            self.screen.figure_wgt_layout.figure_wgt.figure = figure

def app_window_3D(plot_queue,**kwargs):

    GraphApp3D(plot_queue,**kwargs).run() 
    
def interactive_graph(fig,**kwargs):
    """ Interactive grpah using multiprocessing method. 
    function need to be call in if __name__ == "__main__": method
    """
    # Create a queue to pass the Matplotlib instance object
    plot_queue = mp.Queue()
    
    #switch to agg backend
    plt.switch_backend('Agg')

    # Put the Matplotlib instance object into the queue
    plot_queue.put((fig,))

    # Create and start the subprocess
    p = mp.Process(target=app_window, args=(plot_queue,), kwargs=kwargs)
    p.start()
    
def interactive_graph_ipython(fig,**kwargs):
    app_window(fig,**kwargs)
    
def interactive_graph3D_ipython(fig,**kwargs):
    app_window_3D(fig,**kwargs)
    
def interactive_graph3D(fig,**kwargs):
    """ Interactive grpah using multiprocessing method. 
    function need to be call in if __name__ == "__main__": method
    """
    # Create a queue to pass the Matplotlib instance object
    plot_queue = mp.Queue()
    
    #switch to agg backend
    plt.switch_backend('Agg')

    # Put the Matplotlib instance object into the queue
    plot_queue.put((fig,))

    # Create and start the subprocess
    p = mp.Process(target=app_window_3D, args=(plot_queue,), kwargs=kwargs)
    p.start()

if __name__ == "__main__":
    fig, ax1 = plt.subplots(1, 1)
    
    line1, = ax1.plot([0,1,2,3,4], [1,2,8,9,4],label='line1')
    line2, = ax1.plot([2,8,10,15], [15,0,2,4],label='line2')
    
    ax1.legend()
    
    interactive_graph(fig,show_cursor_data=False,drag_legend=True)
    
    interactive_graph_ipython(fig,show_cursor_data=True)

    