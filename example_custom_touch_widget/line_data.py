from kivy.graphics import Color
from kivy.uix.widget import Widget
from kivy.graphics import Line
from kivy.properties import BooleanProperty
from kivy.metrics import dp

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

from kivy.properties import (
    StringProperty,
    NumericProperty,
    ColorProperty
    )

from kivy.lang import Builder 

class LineData(Widget):
    is_drawing = BooleanProperty(False)
    text_box_pos = (-1000, -1000)
    
    def __init__(self,**kwargs):
        super(LineData, self).__init__(**kwargs)
        self.figure_wgt = None
        self.start_ydata = 0
        self.end_ydata = 0
        self.start_data = 0
        self.app_parent = None
        self.x_formatter = None
        self.y_formatter = None
        self.start_point = None

    def on_kv_post(self,_):
        with self.canvas:
            Color(1, 0.1, 0.1, 1, mode="rgba")
            self.line = Line(points=[], width=2)
            self.text_box = BoxText(
                pos=self.text_box_pos,
                pos_hint={'center_x': None, 'center_y': None},
                on_press=lambda x: print("stack_buttons",))

            self.card_line = Line(points=[], width=2)
        
        
        self.fbind('is_drawing',self.callback_drawing)

    def callback_drawing(self,instance,value):
        if self.figure_wgt.touch_mode=='line_data':
            self.text_box.opacity=1
            self.opacity=1
            
    def on_touch_down(self, touch):
        if self.figure_wgt.touch_mode=='line_data':
            if not self.figure_wgt.collide_point(touch.x,touch.y):
                self.opacity=0
            else:
                self.set_text_box_pos(touch.pos)
                self.is_drawing = True
                self.start_point = touch.pos
                self.line.points = [touch.x, touch.y]
                w, h = self.figure_wgt.size
                pos_y = (touch.pos[1]  )
                xfig = touch.pos[0] / w
                yfig = pos_y / h
                if yfig > 0.05 and xfig < 0.90:
                    xdata, ydata = self.figure_wgt.axes.transData.inverted().transform_point((touch.pos[0], pos_y))
                    self.start_ydata = ydata
                    self.start_data = xdata
                
    def on_touch_move(self, touch):
        if self.figure_wgt.touch_mode=='line_data':
            w, h = self.figure_wgt.size
            pos_y = (touch.pos[1]  )
            xfig = touch.pos[0] / w
            yfig = pos_y / h

            if yfig > 0.01 and xfig < 0.99:
                if self.is_drawing:
                    # set the start and end points of the line
                    if self.start_point is not None:
                        start_x, start_y = self.start_point
                        end_x, end_y = touch.pos
                        self.line.points = [start_x, start_y, end_x, end_y]
                xdata, ydata = self.figure_wgt.axes.transData.inverted().transform_point((touch.pos[0], pos_y))
                self.end_ydata = ydata
                self.end_data = xdata
                
                xrange = self.end_data - self.start_data
                if self.x_formatter is not None:
                    xrange = self.x_formatter(xrange)
                    
                yrange = ydata - self.start_ydata
                if self.y_formatter is not None:
                    yrange = self.y_formatter(yrange)

                self.text_box.text = f"Yrange: {str(yrange)}\nXrange: {str(xrange)}"
    
                
                self.set_text_box_pos(touch.pos)

    def on_touch_up(self, touch):
        self.is_drawing = False

    def set_text_box_pos(self, pos):
        # self.text_box.pos = (pos[0] + self.text_box_size_x/10, pos[1] + self.text_box_size_y/10)

        if pos[0] + dp(4) <self.figure_wgt.width+self.figure_wgt.pos[0] - self.text_box.width:
            self.text_box.pos = (pos[0] + + dp(4) , pos[1] + dp(4) )
        else:
            self.text_box.pos = (pos[0] - + dp(4)  - self.text_box.width, pos[1] + dp(4) )
            

class BoxText(BoxLayout):
    """ Hover with vertical text"""  
    text=StringProperty("")
    text_color=ColorProperty([0,0,0,1])
    font_name=StringProperty("Roboto")
    font_size = NumericProperty('15sp')
    background_color=ColorProperty([1,1,1,1])
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs) 

class LineDataFloatLayout(FloatLayout):
    def __init__(self, **kwargs):
        super(LineDataFloatLayout, self).__init__(**kwargs)
        
Builder.load_string('''
<LineDataFloatLayout>:
    size_hint: None,None
    height: dp(0.001)
    width:dp(0.001)    
    LineData:
        id:line_data
        
<BoxText>
    size_hint:None,None
    width:id_lable.texture_size[0] + dp(10)
    height:id_lable.texture_size[1]+ dp(10)
    canvas:
        Color: 
            rgba:root.background_color
        Rectangle:
            size:self.size
            pos:self.pos
        Color:
            rgba: 0,0,0,1
        Line:
            width: 1
            rectangle: self.x, self.y, self.width, self.height        
    
    Label:
        id:id_lable
        text:root.text
        color:root.text_color
        font_name:root.font_name
        font_size:root.font_size
''')