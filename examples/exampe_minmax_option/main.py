from kivy.utils import platform

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_on_activity')
    Config.set('kivy', 'keyboard_mode', '') #disable keyboard mode
    
else:
    #if using android keyboard or kivy keyboard, it's maybe better to use softinput_mode = "below_target"
    from kivy.core.window import Window
    Window.keyboard_anim_args = {"d":.2,"t":"linear"}
    Window.softinput_mode = "below_target"

from kivy.lang import Builder
from kivy.app import App

import matplotlib.pyplot as plt

from kivy.metrics import dp
import numpy as np

from kivy_matplotlib_widget.uix.hover_widget import add_hover,BaseHoverFloatLayout
from matplotlib.ticker import FormatStrFormatter
from kivy.properties import ColorProperty,NumericProperty,StringProperty
from matplotlib import gridspec
from numpy.random import rand
from matplotlib.ticker import NullFormatter, MaxNLocator, FuncFormatter, ScalarFormatter
import matplotlib.dates as mdates
import datetime

from numpy import linspace
from kivy_matplotlib_widget.uix.minmax_widget import add_minmax

KV = '''
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
            text:"min/max" 
            on_release:
                app.set_touch_mode('minmax')
                self.state='down'  
                
        ToggleButton:
            group:'touch_mode'
            text:"pan" 
            on_release:
                app.set_touch_mode('pan')
                self.state='down'    
        ToggleButton:
            group:'touch_mode'
            text: 'ZoomBox'
            on_press: 
                app.set_touch_mode('zoombox')
                self.state='down'
                    
    BoxLayout: 
        ScreenManager:
            id:sm
            Screen1:
            Screen2:
            Screen3:
            Screen4:

    BoxLayout:
        size_hint_y:0.1
        Button:
            text:"previous screen"
            on_release:app.previous_screen()
        Button:
            text:"next screen"
            on_release:app.next_screen()
                
<Screen1@Screen>
    name:'screen1'  
    figure_wgt:figure_wgt                  
    MatplotFigure:
        id:figure_wgt
        fast_draw:False
        interactive_axis:True
        
<Screen2@Screen> 
    name:'screen2'  
    figure_wgt:figure_wgt                  
    MatplotFigureSubplot:
        id:figure_wgt
        fast_draw:False
        interactive_axis:True
      
<Screen3@Screen> 
    name:'screen3'  
    figure_wgt:figure_wgt                  
    MatplotFigureSubplot:
        id:figure_wgt
        fast_draw:True
        interactive_axis:True
       
<Screen4@Screen> 
    name:'screen4'  
    figure_wgt:figure_wgt   

    BoxLayout:
              
        MatplotFigureSubplot:
            id:figure_wgt
            fast_draw:True
            interactive_axis:True

        BoxLayout:
            size_hint_x:0.3
            padding:0,0,dp(10),0
            orientation:'vertical'
            canvas.before:
                Color:
                    rgba:1,1,1,1
                Rectangle:
                    pos:self.pos
                    size:self.size 
                        
            BoxLayout:
                orientation:'vertical'  
                Widget:
                BoxLayout:
                    orientation:'vertical'                    
                    BoxLayout:
                        size_hint_y:None
                        height:label_second.texture_size[1]
                        Label:
                            id:label_second
                            text: "Second"
                            color:0,0,0,1                     
                    CheckBox:
                        color:0,0,0,1
        				state:'down'
                        group:'time_unit'
        				on_press:	
        					self.state='down'	
                            app.set_unit('second')
                    Widget:

                BoxLayout:
                    orientation:'vertical'              							               							
                    BoxLayout:
                        size_hint_y:None
                        height:label_minute.texture_size[1]
                        Label:
                            id:label_minute
                            text: "Minute"
                            color:0,0,0,1   
                    CheckBox:
        				color:0,0,0,1
        				group:'time_unit'
        				on_press:	
        					self.state='down'
                            app.set_unit('minute')                     
                    Widget:
                            
                BoxLayout:
                    orientation:'vertical'              							               							
                    BoxLayout:
                        size_hint_y:None
                        height:label_hour.texture_size[1]
                        Label:
                            id:label_hour
                            text: "Hour"
                            color:0,0,0,1   
                    CheckBox:
            			color:0,0,0,1
            			group:'time_unit'
        				on_press:	
        					self.state='down'
                            app.set_unit('hour')                     
                    Widget:                      
                Widget:

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


def minute_axis(x, pos):
    """convert time axis in minute
    
    Args:
        x : value axis
        pos: tick position
    """        
    return '%.1f' % (x/60)

def hour_axis(x, pos):
    """convert time axis in hour
    
    Args:
        x : value axis
        pos: tick position
    """        
    return '%.2f' % (x/3600)

def minute2second(x):
    """convert minute to second
    
    Args:
        x : value axis
        pos: tick position
    """        
    return float(x)*60

def hour2second(x):
    """convert hour to second
    
    Args:
        x : value axis
        pos: tick position
    """        
    return float(x)*3600

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
    lines = []

    def build(self):
        self.graph_app = Builder.load_string(KV)
        return self.graph_app


    def on_start(self, *args):

# =============================================================================
#         figure 1 - screen1
# =============================================================================
        fig, ax1 = plt.subplots(1, 1)

        line1, = ax1.plot([0,1,2,3,4], [1,2,8,9,4],label='line1')
        line2, = ax1.plot([2,8,10,15], [15,0,2,4],label='line2')

        fig.subplots_adjust(left=0.13,top=0.96,right=0.93,bottom=0.2)
  
        ax1.set_xlabel("axis_x",fontsize=dp(13))
        ax1.set_ylabel("axis_y",fontsize=dp(13))#
                
        screen1=self.graph_app.ids.sm.get_screen('screen1')
        screen1.figure_wgt.figure = fig
        screen1.figure_wgt.cursor_xaxis_formatter = FormatStrFormatter('%.1f') 
        screen1.figure_wgt.cursor_yaxis_formatter = FormatStrFormatter('%.1f') 
        
        screen1.figure_wgt.register_lines(list(ax1.get_lines()))
        
        #add general hover to the figure (with normal touch mode)
        add_hover(screen1.figure_wgt,mode='desktop')
        
        add_minmax(screen1.figure_wgt)

# =============================================================================
#         figure 2 - screen2
# =============================================================================
        x = np.linspace(0, 2 * np.pi, 400)
        y = np.sin(x ** 2)
        
        fig2, ax2 = plt.subplots()
        
        ax2.plot(x,y,label='1')
        # ax.set_xlim(2,10)

        ax2.set(xlabel='x-label', ylabel='y-label')
        ax3 = ax2.twinx()
        ax4 = ax3.twiny()
        ax4.plot(x+1,y-1,label='2')

                
        screen2=self.graph_app.ids.sm.get_screen('screen2')
        screen2.figure_wgt.figure = fig2
        screen2.figure_wgt.cursor_xaxis_formatter = FormatStrFormatter('%.1f') 
        screen2.figure_wgt.cursor_yaxis_formatter = FormatStrFormatter('%.1f') 
        
        screen2.figure_wgt.register_cursor()
        
        add_hover(screen2.figure_wgt,mode='desktop',hover_widget=PlotlyHover2())

        add_minmax(screen2.figure_wgt)
                

# =============================================================================
#         figure 3 - screen3
# =============================================================================

        fig3, ax5 = plt.subplots(1, 1)
        
        base = datetime.datetime(2005, 2, 1)
        dates = np.array([base + datetime.timedelta(hours=(2 * i))
                          for i in range(732)])
        N = len(dates)
        np.random.seed(19680801)
        y = np.cumsum(np.random.randn(N))
        new_datetime = []
        for mytime in dates:
            new_datetime.append(mdates.date2num(mytime))
            
        line1, = ax5.plot(new_datetime, y,label='line1', linewidth=1,
                                            color='#118812')
        
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        ax5.xaxis.set_major_locator(locator)
        ax5.xaxis.set_major_formatter(formatter)

                
        screen3=self.graph_app.ids.sm.get_screen('screen3')
        screen3.figure_wgt.figure = fig3
        screen3.figure_wgt.cursor_xaxis_formatter = mdates.DateFormatter('%m-%d')
        screen3.figure_wgt.cursor_yaxis_formatter = FormatStrFormatter('%.1f') 
        
        screen3.figure_wgt.register_cursor()
        
        add_hover(screen3.figure_wgt,mode='desktop',hover_widget=PlotlyHover2())
        
        def format_date2num(x):
            """convert time axis in second
            
            Args:
                x : value axis
                pos: tick position
            """        
            return mdates.date2num(datetime.datetime.strptime(x,'%Y-%m-%d'))
        
        add_minmax(screen3.figure_wgt,
                   xaxis_formatter = mdates.DateFormatter('%Y-%m-%d'),
                   invert_xaxis_formatter = format_date2num)
# =============================================================================
#         figure 4 - screen4
# =============================================================================
        x = np.arange(12000)
        N = len(x)
        np.random.seed(19680801)
        y = np.cumsum(np.random.randn(N))
        
        fig4, ax6 = plt.subplots(1, 1)

        ax6.plot(x,y)
       
        screen4=self.graph_app.ids.sm.get_screen('screen4')
        screen4.figure_wgt.figure = fig4
        screen4.figure_wgt.cursor_xaxis_formatter = FormatStrFormatter('%.1f') 
        screen4.figure_wgt.cursor_yaxis_formatter = FormatStrFormatter('%.1f') 
        
        screen4.figure_wgt.register_cursor()
        
        add_hover(screen4.figure_wgt,mode='desktop',hover_widget=PlotlyHover2())

        add_minmax(screen4.figure_wgt)

        #set minmax touch_mode as default
        self.set_touch_mode('minmax')
        
    def set_touch_mode(self,mode):
        for screen in self.graph_app.ids.sm.screens:
            if hasattr(screen,'figure_wgt'):
                screen.figure_wgt.touch_mode=mode

    def home(self):
        screen=self.graph_app.ids.sm.current_screen
        screen.figure_wgt.main_home()
        
    def previous_screen(self):
        screen_name=self.graph_app.ids.sm.current
        screen_number = int(screen_name[-1])
        if screen_number<=1:
            screen_number=4
        else:
            screen_number-=1
            
        self.graph_app.ids.sm.current = 'screen' + str(screen_number)        
        
    def next_screen(self):
        screen_name=self.graph_app.ids.sm.current
        screen_number = int(screen_name[-1])
        if screen_number>=4:
            screen_number=1
        else:
            screen_number+=1
            
        self.graph_app.ids.sm.current = 'screen' + str(screen_number)


    def set_unit(self,unit):
        screen4 = self.graph_app.ids.sm.current_screen
        if unit == 'minute':
            formatter = FuncFormatter(minute_axis)
            screen4.figure_wgt.figure.axes[0].xaxis.set_major_formatter(formatter)
            screen4.figure_wgt.text_instance.invert_xaxis_formatter = minute2second
        elif unit == 'hour':
            formatter = FuncFormatter(hour_axis)
            screen4.figure_wgt.figure.axes[0].xaxis.set_major_formatter(formatter)
            screen4.figure_wgt.text_instance.invert_xaxis_formatter = hour2second
        else:
            formatter = ScalarFormatter() #default matplotlib formatter
            screen4.figure_wgt.figure.axes[0].xaxis.set_major_formatter(formatter)
            screen4.figure_wgt.text_instance.invert_xaxis_formatter = None  
            
        screen4.figure_wgt.figure.canvas.draw_idle()
        screen4.figure_wgt.figure.canvas.flush_events()       

Test().run()