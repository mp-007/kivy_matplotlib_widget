from kivy.utils import platform

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
from graph_generator import GraphGenerator

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from kivy.metrics import dp
import numpy as np
font_size_axis_title = dp(16)
font_size_axis_tick = dp(12)
linewidth = 2

from kivy_matplotlib_widget.uix.hover_widget import add_hover,HoverVerticalText,InfoHover,BaseHoverFloatLayout
from matplotlib.ticker import FormatStrFormatter
from kivy.properties import ColorProperty,NumericProperty,StringProperty


KV = '''
#:import MatplotFigureCustom graph_custom_widget

Screen
    figure_wgt:figure_wgt
    figure_wgt2:figure_wgt2
    figure_wgt3:figure_wgt3
    figure_wgt4:figure_wgt4
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
                text: 'Cursor'
                on_press: 
                    app.set_touch_mode('cursor')
                    self.state='down'
                    
        BoxLayout:    
            MatplotFigureCustom:
                id:figure_wgt
                
            MatplotFigureCustom:
                id:figure_wgt2  
                fast_draw:False 
                         
        BoxLayout:  
            MatplotFigureCustom:
                id:figure_wgt3  
                fast_draw:False

            MatplotFigureCustom:
                id:figure_wgt4   
                fast_draw:False

<PlotlyHover>
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
                        root.custom_label if root.custom_label else ''  
                    font_size:root.text_size
                    color: root.text_color
                    font_name : root.text_font      

'''

class PlotlyHover(BaseHoverFloatLayout):
    """ PlotlyHover adapt the background and the font color with the line or scatter color""" 
    text_color=ColorProperty([0,0,0,1])
    text_font=StringProperty("Roboto")
    text_size = NumericProperty(dp(14))
    hover_height = NumericProperty(dp(24))

    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)  
 

class Test(App):
    lines = []

    def build(self):
        self.screen=Builder.load_string(KV)
        return self.screen


    def on_start(self, *args):

        mygraph = GraphGenerator()
        self.screen.figure_wgt.axes= mygraph.ax1

        self.screen.figure_wgt.register_lines(self.screen.figure_wgt.axes.lines)
        self.screen.figure_wgt.figure = mygraph.fig
        self.screen.figure_wgt.cursor_xaxis_formatter = mdates.DateFormatter('%m-%d')
        self.screen.figure_wgt.cursor_yaxis_formatter = FormatStrFormatter('%.1f') 
        
        self.screen.figure_wgt.register_cursor()
        
        add_hover(self.screen.figure_wgt,mode='desktop',hover_widget=PlotlyHover())

        fig, ax = plt.subplots(1, 1)
        
        x = 4 + np.random.normal(0, 1.5, 200)
        
        ax.hist(x, bins=8, linewidth=0.5, edgecolor="white")
        
        fig.subplots_adjust(left=0.15,top=0.90,right=0.93,bottom=0.2) 
        ax.set_xlabel("axis_x",fontsize=font_size_axis_title)
        ax.set_ylabel("axis_y",fontsize=font_size_axis_title)#  
        
        
        self.screen.figure_wgt2.cursor_xaxis_formatter = FormatStrFormatter('%.1f')
        self.screen.figure_wgt2.cursor_yaxis_formatter = FormatStrFormatter('%.1f')  

        self.screen.figure_wgt2.axes= ax
        self.screen.figure_wgt2.register_lines([])
        self.screen.figure_wgt2.figure = fig
        self.screen.figure_wgt2.register_cursor()
        
        add_hover(self.screen.figure_wgt2,mode='desktop',hover_widget=InfoHover())
        
        fig3, ax3 = plt.subplots(1, 1)
        X, Y = np.meshgrid(np.linspace(-3, 3, 16), np.linspace(-3, 3, 16))
        Z = (1 - X/2 + X**5 + Y**3) * np.exp(-X**2 - Y**2)
        
        # plot
        ax3.imshow(Z,label=" ")

        fig3.subplots_adjust(left=0.13,top=0.90,right=0.93,bottom=0.2) 
        ax3.set_xlabel("axis_x",fontsize=font_size_axis_title)
        ax3.set_ylabel("axis_y",fontsize=font_size_axis_title)#  

        self.screen.figure_wgt3.cursor_xaxis_formatter = FormatStrFormatter('%.1f')
        self.screen.figure_wgt3.cursor_yaxis_formatter = FormatStrFormatter('%.1f') 
        
        self.screen.figure_wgt3.axes= ax3
        self.screen.figure_wgt3.register_lines([])
        self.screen.figure_wgt3.figure = fig3
        self.screen.figure_wgt3.register_cursor() 
        
        add_hover(self.screen.figure_wgt3,mode='desktop',hover_widget=InfoHover())
        
        x = [1, 2, 3, 4]
        y = np.linspace(0.2, 0.7, len(x))
        colors = plt.get_cmap('Blues')(y)
        
        percent=[]
        last_y=0
        sum_y=y.sum()
        for i in y:          
            percent.append(f"{np.round((i/sum_y)*100,1)}%")
        
        # plot
        with plt.style.context('_mpl-gallery-nogrid',after_reset=True):
            fig4, ax4 = plt.subplots()
            fig4.subplots_adjust(left=0.13,top=0.90,right=0.93,bottom=0.2) 

            wedges, texts = ax4.pie(x, labels=percent,labeldistance=None,colors=colors,radius=3, center=(4, 4),
                   wedgeprops={"linewidth": 1, "edgecolor": "white"}, frame=True)
            
            ax4.set(xlim=(0, 8), xticks=np.arange(1, 8),
                   ylim=(0, 8), yticks=np.arange(1, 8))
            ax4.xaxis.set_visible(False)
            ax4.yaxis.set_visible(False)

        self.screen.figure_wgt4.cursor_xaxis_formatter = FormatStrFormatter('%.1f')
        self.screen.figure_wgt4.cursor_yaxis_formatter = FormatStrFormatter('%.1f') 
        
        self.screen.figure_wgt4.axes= ax4
        self.screen.figure_wgt4.register_lines([])
        self.screen.figure_wgt4.figure = fig4
        self.screen.figure_wgt4.register_cursor() 

        add_hover(self.screen.figure_wgt4,mode='desktop',hover_widget=InfoHover())        

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode
        self.screen.figure_wgt2.touch_mode=mode
        self.screen.figure_wgt3.touch_mode=mode
        self.screen.figure_wgt4.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()



Test().run()