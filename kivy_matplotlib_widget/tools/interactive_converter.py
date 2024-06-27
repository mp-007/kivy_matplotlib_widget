from kivy.lang import Builder
from kivy.app import App
from kivy.properties import ColorProperty,NumericProperty,StringProperty
from kivy.metrics import dp

import matplotlib.pyplot as plt
import multiprocessing as mp   

from kivy_matplotlib_widget.uix.legend_widget import MatplotlibInteractiveLegend
from kivy_matplotlib_widget.uix.minmax_widget import add_minmax
from kivy_matplotlib_widget.uix.hover_widget import add_hover,BaseHoverFloatLayout

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
            show_cursor_data:'desktop'
            figure_wgt:figure_wgt

        MatplotFigureSubplot:
            id:figure_wgt
            auto_cursor:True
            interactive_axis:True
            
<PlotlyHover2>
    custom_color: [0,0,0,1]
    BoxLayout:
        id:main_box
        x:
            root.x_hover_pos + dp(4)
        y:
            root.y_hover_pos - root.hover_height/2
        size_hint: None, None
        height: label.texture_size[1]+ dp(4)
        width: 
            self.minimum_width + dp(12) if root.show_cursor \
            else dp(0.0001)            
        orientation:'vertical'
        padding: 0,-dp(1),0,0
        
        canvas:            
            Color:
                rgba: root.custom_color if root.custom_color else [0,0,0,1]
            Rectangle:
                pos: self.pos
                size: self.size
            Triangle:
                points:
                    [ \
                    root.x_hover_pos, root.y_hover_pos, \
                    main_box.x, root.y_hover_pos+ dp(4), \
                    main_box.x, root.y_hover_pos- dp(4)  \
                    ]
            SmoothLine:
                width:dp(1)
                points:
                    [ \
                    root.x_hover_pos, root.y_hover_pos, \
                    main_box.x, root.y_hover_pos \
                    ]                           
             
        BoxLayout:
            size_hint_x:None
            width:label.texture_size[0]
            padding: dp(12),0,0,0
            Label:
                id:label
                text: 
                    '(' + root.label_x_value  +','+ root.label_y_value +')'
                font_size:root.text_size
                color:
                    [0,0,0,1] if (root.custom_color[0]*0.299 + \
                    root.custom_color[1]*0.587 + root.custom_color[2]*0.114) > 186/255 \
                    else [1,1,1,1]
                font_name : root.text_font

                font_name : root.text_font
                
        FloatLayout:
            size_hint: None,None
            width: dp(0.01) 
            height: dp(0.01) 
            BoxLayout:
                size_hint:None,None
                x:main_box.x + main_box.width + dp(4)
                y:main_box.y + main_box.height/2 - label3.texture_size[1]/2
                width:label3.texture_size[0]
                height:label3.texture_size[1]
                Label:
                    id:label3
                    text: 
                        root.custom_label if root.custom_label and not '_child' in root.custom_label else ''  
                    font_size:root.text_size
                    color: root.text_color
                    font_name : root.text_font      
            
'''

class PlotlyHover2(BaseHoverFloatLayout):
    """ PlotlyHover adapt the background and the font color with the line or scatter color""" 
    text_color=ColorProperty([0,0,0,1])
    text_font=StringProperty("Roboto")
    text_size = NumericProperty(dp(14))
    hover_height = NumericProperty(dp(24))

    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)   

class Test(App):
    figure = None

    def __init__(self, figure=None, **kwargs):
        """__init__ function class"""
        self.figure=figure
        # print(self.figure.get())
        super(Test, self).__init__(**kwargs)
        
    def build(self):
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
            
        add_hover(self.screen.figure_wgt,mode='desktop',hover_widget=PlotlyHover2())
        add_minmax(self.screen.figure_wgt)
        if len(self.screen.figure_wgt.figure.axes) > 0  and self.screen.figure_wgt.figure.axes[0].get_legend():
            MatplotlibInteractiveLegend(self.screen.figure_wgt)

def main(plot_queue):

    Test(figure=plot_queue).run()
    
def interactive_graph(fig):
    # Create a queue to pass the Matplotlib instance object
    plot_queue = mp.Queue()
    
    #switch to agg backend
    plt.switch_backend('Agg')

    # Put the Matplotlib instance object into the queue
    plot_queue.put((fig,))

    # Create and start the subprocess
    p = mp.Process(target=main, args=(plot_queue,))
    p.start()
    
def interactive_graph_ipython(fig):
    main(fig)
    
if __name__ == "__main__":
    fig, ax1 = plt.subplots(1, 1)
    
    line1, = ax1.plot([0,1,2,3,4], [1,2,8,9,4],label='line1')
    line2, = ax1.plot([2,8,10,15], [15,0,2,4],label='line2')
    
    ax1.legend()
    
    interactive_graph(fig)
    
    interactive_graph_ipython(fig)
    