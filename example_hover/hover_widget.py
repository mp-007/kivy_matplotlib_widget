from kivy.uix.floatlayout import FloatLayout

from kivy.properties import (
    ObjectProperty,
    NumericProperty,
    StringProperty,
    BooleanProperty,
    ColorProperty
    )

from kivy.lang import Builder 
from kivy.core.window import Window 
from kivy.metrics import dp
        
        
def add_hover(figure_wgt,mode='touch',label_x='x',label_y='y',hover_widget=None):
    """ add hover to matpotlib figure
    
    Args:
        figure_wgt: figure widget from kivy_matplotlib_widget package
        mode : 'touch' (touch device) or 'desktop' (desktop with mouse)

    """

    if figure_wgt.hover_instance:
        figure_wgt.hover_instance.reset_hover()
        figure_wgt.hover_instance.label_x=label_x
        figure_wgt.hover_instance.label_y=label_y        
           
    else:
        if hover_widget is None:
            hover_widget = GeneralHover()
            
        hover_widget.x_hover_pos=figure_wgt.x
        hover_widget.y_hover_pos=figure_wgt.y 
        hover_widget.label_x=label_x
        hover_widget.label_y=label_y
        
        figure_wgt.parent.add_widget(hover_widget)
        figure_wgt.hover_instance=hover_widget      
        if mode=='desktop':
            figure_wgt.hover_on=True
            Window.bind(mouse_pos=figure_wgt.on_motion)  
    
        
class BaseHoverFloatLayout(FloatLayout):
    """ Touch egend kivy class"""
    figure_wgt = ObjectProperty(None)
    x_hover_pos = NumericProperty(1)
    y_hover_pos = NumericProperty(1)  
    ymin_line = NumericProperty(1) 
    ymax_line = NumericProperty(1) 
    hover_outside_bound = BooleanProperty(False)
    show_cursor = BooleanProperty(False)
    label_x = StringProperty('x')  
    label_y = StringProperty('y')  
    label_x_value = StringProperty('')  
    label_y_value = StringProperty('') 
    custom_label = StringProperty('',allownone=True) #futur used for dynamic label
    custom_color=ColorProperty([0,0,0,1],allownone=True) #futur used for dynamic color
    figwidth = NumericProperty(2) 
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)

    def reset_hover(self):
        """ reset hover attribute """
        self.x_hover_pos = 1
        self.y_hover_pos = 1
        self.ymin_line = 1  
        self.ymax_line = 1 

class GeneralHover(BaseHoverFloatLayout):
    """ GeneralHover """ 
    text_color=ColorProperty([0,0,0,1])
    text_font=StringProperty("Roboto")
    text_size = NumericProperty(dp(14))
    background_color=ColorProperty([0,0,1,0.3])
    hover_height = NumericProperty(dp(24))
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)    

class HoverVerticalText(BaseHoverFloatLayout):
    """ Hover with vertical text"""  
    text_color=ColorProperty([0,0,0,1])
    text_font=StringProperty("Roboto")
    text_size = NumericProperty(dp(14))
    background_color=ColorProperty([1,1,0,1])
    hover_height = NumericProperty(dp(48))
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)  

class InfoHover(BaseHoverFloatLayout):
    """ InfoHover adapt the background and the font color with the line or scatter color""" 
    text_color=ColorProperty([0,0,0,1])
    text_font=StringProperty("Roboto")
    text_size = NumericProperty(dp(14))
    hover_height = NumericProperty(dp(48))
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)            

    # def set_font_color(self):
    #                     0,0,0,1 if (self.custom_color[0]*0.299 + \
    #                     root.custom_color[1]*0.587 + root.custom_color[2]*0.114) > 186 \
    #                     else 1,1,1,1        

Builder.load_string('''

<BaseHoverFloatLayout>
    size_hint: None,None
    width: dp(0.01) 
    height: dp(0.01)
    opacity:1 if root.show_cursor and not root.hover_outside_bound else 0
       
<GeneralHover>
    BoxLayout:
        x:
            root.x_hover_pos + dp(4) if root.x_hover_pos + dp(4) < root.figwidth - label.texture_size[0] - self.padding[0] * 2 \
            else root.x_hover_pos - dp(4) - label.texture_size[0] - self.padding[0] * 2
        y:
            root.y_hover_pos + dp(4)
        size_hint: None, None
        padding: dp(4),0,dp(4),0
        height: root.hover_height
        width: 
            label.texture_size[0] + self.padding[0] * 2 if root.show_cursor \
            else dp(0.0001)            
            
        canvas:            
            Color:
                rgba: root.background_color
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(7)]  
        canvas.after:            
            Color:
                rgba: 0,0,1,1
            Ellipse:
                size: (dp(8),dp(8))
                pos: 
                    (root.x_hover_pos-dp(8/2), \
                     root.y_hover_pos-dp(8/2))
            Color:
                rgba: 0,0,1,1
            Line:
                width: dp(1)
        		points: 
                    root.x_hover_pos, \
           			root.ymin_line, \
       				root.x_hover_pos, \
       				root.ymax_line                
        Label:
            id:label
            text: 
                root.label_x + ': ' + root.label_x_value + ', ' + \
                root.label_y + ': ' + root.label_y_value    
            font_size:root.text_size
            color: root.text_color
            font_name : root.text_font

<HoverVerticalText>
    BoxLayout:
        x:
            root.x_hover_pos + dp(4) if root.x_hover_pos + dp(4) < root.figwidth - label.texture_size[0] - self.padding[0] * 2 \
            else root.x_hover_pos - dp(4) - max(label.texture_size[0],label2.texture_size[0]) - self.padding[0] * 2
        y:
            root.y_hover_pos + dp(4)
        size_hint: None, None
        height: root.hover_height
        width: 
            max(label.texture_size[0],label2.texture_size[0]) + dp(12) if root.show_cursor \
            else dp(0.0001)            
        orientation:'vertical'
        padding: 0,dp(4),0,dp(4)
        
        canvas:            
            Color:
                rgba: root.background_color
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(4)]  
            Color:
                rgba: 0,0,0,1
             
            Line:
                width: 1    
                rounded_rectangle:
                    (self.x, self.y, self.width, self.height,\
                    dp(4), dp(4), dp(4), dp(4),\
                    self.height)                 
                
                
        canvas.after:            
            Color:
                rgba: 0,0,0,1
            Rectangle:
                size: (dp(8),dp(8))
                pos: 
                    (root.x_hover_pos-dp(8/2), \
                     root.y_hover_pos-dp(8/2))
        
        BoxLayout:
            size_hint_x:None
            width:label.texture_size[0]
            padding: dp(12),0,0,0
            Label:
                id:label
                text: 
                    root.label_x + ': ' + root.label_x_value  
                font_size:root.text_size
                color: root.text_color
                font_name : root.text_font

        BoxLayout:
            size_hint_x:None
            width:label2.texture_size[0]   
            padding: dp(12),0,0,0
            Label:
                id:label2
                text:
                    root.label_y + ': ' + root.label_y_value    
                font_size:root.text_size
                color: root.text_color 
                font_name : root.text_font

<InfoHover>
    custom_color: [0,0,0,1]
    BoxLayout:
        id:main_box
        x:
            root.x_hover_pos + dp(4) if root.x_hover_pos + dp(4) < root.figwidth - label.texture_size[0] - self.padding[0] * 2 \
            else root.x_hover_pos - dp(4) - max(label.texture_size[0],label2.texture_size[0]) - self.padding[0] * 2
        y:
            root.y_hover_pos + dp(4)
        size_hint: None, None
        height: root.hover_height
        width: 
            max(label.texture_size[0],label2.texture_size[0]) + dp(12) if root.show_cursor \
            else dp(0.0001)            
        orientation:'vertical'
        padding: 0,dp(4),0,dp(4)
        
        canvas:            
            Color:
                rgba: root.custom_color if root.custom_color else [0,0,0,1]
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgba: 0,0,0,1
             
            Line:
                width: 1    
                rounded_rectangle:
                    (self.x, self.y, self.width, self.height,\
                    dp(4), dp(4), dp(4), dp(4),\
                    self.height)                 
                
                
        canvas.after:            
            Color:
                rgba: 0,0,0,1
            Rectangle:
                size: (dp(8),dp(8))
                pos: 
                    (root.x_hover_pos-dp(8/2), \
                     root.y_hover_pos-dp(8/2))
        
        BoxLayout:
            size_hint_x:None
            width:label.texture_size[0]
            padding: dp(12),0,0,0
            Label:
                id:label
                text: 
                    root.label_x + ': ' + root.label_x_value  
                font_size:root.text_size
                color:
                    [0,0,0,1] if (root.custom_color[0]*0.299 + \
                    root.custom_color[1]*0.587 + root.custom_color[2]*0.114) > 186/255 \
                    else [1,1,1,1]
                font_name : root.text_font

        BoxLayout:
            size_hint_x:None
            width:label2.texture_size[0]   
            padding: dp(12),0,0,0
            Label:
                id:label2
                text:
                    root.label_y + ': ' + root.label_y_value    
                font_size:root.text_size
                color:
                    [0,0,0,1] if (root.custom_color[0]*0.299 + \
                    root.custom_color[1]*0.587 + root.custom_color[2]*0.114) > 186/255 \
                    else [1,1,1,1]
                font_name : root.text_font
        FloatLayout:
            size_hint: None,None
            width: dp(0.01) 
            height: dp(0.01) 
            BoxLayout:
                x:main_box.x + main_box.width + label3.texture_size[0]/2 + dp(4)
                y:main_box.y + main_box.height - label3.texture_size[1]/2
                width:label3.texture_size[0]
                Label:
                    id:label3
                    text: 
                        root.custom_label if root.custom_label else ''  
                    font_size:root.text_size
                    color: root.text_color
                    font_name : root.text_font                
                    
        ''')
