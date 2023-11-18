from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout

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
import numpy as np
        
        
def add_hover(figure_wgt,mode='touch',label_x='x',label_y='y',hover_widget=None,hover_type='nearest'):
    """ add hover to matpotlib figure
    
    Args:
        figure_wgt: figure widget from kivy_matplotlib_widget package
        mode : 'touch' (touch device) or 'desktop' (desktop with mouse)

    """

    if figure_wgt.hover_instance:
       
        if hover_type=='compare':
            if not figure_wgt.compare_hover_instance:
                if hover_widget is None:
                    hover_widget = GeneralCompareHover()  
                hover_widget.x_hover_pos=figure_wgt.x
                hover_widget.y_hover_pos=figure_wgt.y 
                hover_widget.label_x=label_x
                hover_widget.label_y=label_y
                figure_wgt.parent.add_widget(hover_widget)
                figure_wgt.compare_hover_instance = hover_widget                    
            figure_wgt.compare_hover_instance.create_child(figure_wgt.lines)            
            figure_wgt.hover_instance = figure_wgt.compare_hover_instance
            figure_wgt.compare_xdata=True 
            if figure_wgt.nearest_hover_instance:
                figure_wgt.nearest_hover_instance.show_cursor=False
            
        else:

            if not figure_wgt.nearest_hover_instance:
                if hover_widget is None:
                    hover_widget = GeneralHover() 
                hover_widget.x_hover_pos=figure_wgt.x
                hover_widget.y_hover_pos=figure_wgt.y 
                hover_widget.label_x=label_x
                hover_widget.label_y=label_y
                figure_wgt.parent.add_widget(hover_widget)                    
                figure_wgt.nearest_hover_instance = hover_widget
                
            figure_wgt.hover_instance = figure_wgt.nearest_hover_instance                    
            figure_wgt.hover_instance.reset_hover()
            figure_wgt.hover_instance.label_x=label_x
            figure_wgt.hover_instance.label_y=label_y
            figure_wgt.compare_xdata=False 
            if figure_wgt.compare_hover_instance:
                figure_wgt.compare_hover_instance.show_cursor=False                     
    else:
        if hover_widget is None:
            if hover_type=='compare':
                hover_widget = GeneralCompareHover()
            else:
                hover_widget = GeneralHover()
         
        if hover_type=='compare':
            hover_widget.create_child(figure_wgt.lines)
            figure_wgt.compare_hover_instance = hover_widget
            figure_wgt.compare_xdata=True 
        else:
            figure_wgt.nearest_hover_instance = hover_widget
            figure_wgt.compare_xdata=False

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

class GeneralCompareHover(BaseHoverFloatLayout):
    """ GeneralCompareHover""" 
    text_color=ColorProperty([0,0,0,1])
    text_font=StringProperty("Roboto")
    text_size = NumericProperty(dp(14))
    background_color=ColorProperty([1,1,1,1])
    hover_height = NumericProperty(dp(48))
    y_touch_pos = NumericProperty(1)    
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs) 
        self.children_names=[]
        self.children_list=[]

    def create_child(self,lines):
        if len(self.ids.main_box.children)>2:
            #clear all added childrens
            for i in range(len(self.ids.main_box.children)-2):
                self.ids.main_box.remove_widget(self.ids.main_box.children[0])

        self.children_names=[]
        self.children_list=[]        
        for i,line in enumerate(lines):
            label=line.get_label()
            if i==0:
               self.ids.comparehoverbox.label_y=label
               mywidget = self.ids.comparehoverbox
            else:
                mywidget=CompareHoverBox()
                mywidget.label_y=label
                self.ids.main_box.add_widget(mywidget)
            self.children_names.append(label)
            self.children_list.append(mywidget)

class CompareHoverBox(BoxLayout):
    """ Hover with vertical text""" 
    text_color=ColorProperty([0,0,0,1])
    text_font=StringProperty("Roboto")
    text_size = NumericProperty(dp(14))    
    label_y = StringProperty('y')
    label_y_value = StringProperty('y')
    x_hover_pos = NumericProperty(1)
    y_hover_pos = NumericProperty(1)
    show_widget = BooleanProperty(False)
    custom_color=ColorProperty([0,0,0,1],allownone=True)

    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)       



class TagCompareHover(BaseHoverFloatLayout):
    """ TagCompareHover""" 
    text_color=ColorProperty([0,0,0,1])
    text_font=StringProperty("Roboto")
    text_size = NumericProperty(dp(14))
    background_color=ColorProperty([1,1,1,1])
    hover_height = NumericProperty(dp(48))
    y_touch_pos = NumericProperty(1)    
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs) 
        self.children_names=[]
        self.children_list=[]

    def create_child(self,lines):
        if len(self.ids.main_box.children)>2:
            #clear all added childrens
            for i in range(len(self.ids.main_box.children)-2):
                self.ids.main_box.remove_widget(self.ids.main_box.children[0])

        self.children_names=[]
        self.children_list=[]        
        for i,line in enumerate(lines):
            label=line.get_label()
            if i==0:
               self.ids.ycomparehoverbox.label_y=label
               mywidget = self.ids.ycomparehoverbox
            else:
                mywidget=TagCompareHoverBox()
                mywidget.label_y=label
                self.ids.main_box.add_widget(mywidget)
            self.children_names.append(label)
            self.children_list.append(mywidget)
            
    def overlap_check(self):
        if len(self.ids.main_box.children)>2:
            y_pos_list=[]
            child_list=[]
            for child in self.ids.main_box.children[:-1]:
                child.hover_offset=0
                y_pos_list.append(child.y_hover_pos)
                child_list.append(child)
            heigh_child = child.ids.label.texture_size[1]+dp(6)
            sorting_args= np.argsort(y_pos_list)

            for index in range(len(sorting_args)-1):
                #chneck overlap
                if y_pos_list[sorting_args[index+1]]-heigh_child/2 <= y_pos_list[sorting_args[index]]+heigh_child/2 and \
                    child_list[sorting_args[index+1]].show_widget:
                    offset = -((y_pos_list[sorting_args[index+1]]-heigh_child/2) - (y_pos_list[sorting_args[index]]+heigh_child/2))

                    y_pos_list[sorting_args[index+1]] +=offset
                    child_list[sorting_args[index+1]].hover_offset = offset

class TagCompareHoverBox(FloatLayout):
    """ Hover with vertical text""" 
    text_color=ColorProperty([0,0,0,1])
    text_font=StringProperty("Roboto")
    text_size = NumericProperty(dp(14))    
    label_y = StringProperty('y')
    label_y_value = StringProperty('y')
    x_hover_pos = NumericProperty(1)
    y_hover_pos = NumericProperty(1)
    show_widget = BooleanProperty(False)
    custom_color=ColorProperty([0,0,0,1],allownone=True)
    hover_offset = NumericProperty(0)

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
                size_hint:None,None
                x:main_box.x + main_box.width + dp(4)
                y:main_box.y + main_box.height - label3.texture_size[1]
                width:label3.texture_size[0]
                height:label3.texture_size[1]
                Label:
                    id:label3
                    text: 
                        root.custom_label if root.custom_label else ''  
                    font_size:root.text_size
                    color: root.text_color
                    font_name : root.text_font     
                    
<GeneralCompareHover>
    custom_color: [0,0,0,1]    
    
    BoxLayout:
        id:main_box
        x:
            root.x_hover_pos + dp(4) if root.x_hover_pos + dp(4) < root.figwidth - self.width  - self.padding[0] * 2 \
            else root.x_hover_pos - dp(4) - self.width - self.padding[0] * 2
        y:
            root.ymin_line + dp(4) if abs(root.y_touch_pos -root.ymin_line) > abs(root.y_touch_pos -root.ymax_line) else root.ymax_line - dp(4) - self.height
        size_hint: None, None
        height: self.minimum_height
        width: 
            self.minimum_width + dp(12) if root.show_cursor \
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
                rgba: 0,0,1,1
            Line:
                width: dp(1)
        		points: 
                    root.x_hover_pos, \
           			root.ymin_line, \
       				root.x_hover_pos, \
       				root.ymax_line
        
        
        BoxLayout:
            size_hint:None,None
            width:label.texture_size[0] + dp(12)
            height:label.texture_size[1] + dp(12)
            padding: dp(12),0,0,0
            Label:
                id:label
                text: 
                    root.label_x + ': ' + root.label_x_value  
                font_size:root.text_size
                font_name : root.text_font
                color: root.text_color
                
        CompareHoverBox: 
            id:comparehoverbox              
                
<CompareHoverBox>
    size_hint:None,None
    width:label.texture_size[0] + dp(12) + dp(24) if self.show_widget else dp(12)
    height:label.texture_size[1] + dp(12) if self.show_widget else dp(0.01)
    opacity:1 if self.show_widget else 0
    padding: dp(12),0,0,0
    Widget:
        size_hint_x:None
        width:dp(16)
        canvas:            
            Color:
                rgba: root.custom_color if root.custom_color else [0,0,0,1]
            Rectangle:
                pos: self.pos[0],self.pos[1]+self.height/2-dp(6)
                size: dp(12),dp(12)    
    Label:
        id:label
        text: root.label_y + ': ' + root.label_y_value  
        color: root.text_color
        font_size:root.text_size
        font_name : root.text_font  

<TagCompareHover>
    custom_color: [0,0,0,1]    
    
    BoxLayout:
        id:main_box
        x:
            root.x_hover_pos if root.x_hover_pos + dp(4) < root.figwidth - self.width  - self.padding[0] * 2 \
            else root.x_hover_pos - self.width - self.padding[0] * 2
        y:
            root.ymin_line if abs(root.y_touch_pos -root.ymin_line) > abs(root.y_touch_pos -root.ymax_line) else root.ymax_line - self.height
        size_hint: None, None
        height: root.hover_height
        width: 
            self.minimum_width + dp(12) if root.show_cursor \
            else dp(0.0001)
        orientation:'vertical'
        padding: 0,dp(4),0,dp(4)
                                
        canvas.after:            
            Color:
                rgba: 0,0,1,0
            Line:
                width: dp(1)
        		points: 
                    root.x_hover_pos, \
           			root.ymin_line, \
       				root.x_hover_pos, \
       				root.ymax_line
        
        
        FloatLayout:
            size_hint:None,None
            width:dp(0.01)
            height:dp(0.01)
            BoxLayout:            
                size_hint:None,None
                width:label.texture_size[0] + dp(8)
                height:label.texture_size[1] + dp(6)
                x: root.x_hover_pos - label.texture_size[0]/2 - dp(4)
                y: root.ymin_line - label.texture_size[1] - dp(10)
                canvas.before:            
                    Color:
                        rgba: [0,0,0,1]
                    Rectangle:
                        pos: self.pos
                        size: self.size  
                    Triangle:
                        points:
                            [ \
                            root.x_hover_pos -dp(4), root.ymin_line-dp(4), \
                            root.x_hover_pos, root.ymin_line, \
                            root.x_hover_pos +dp(4), root.ymin_line-dp(4) \
                            ]
                        
                Label:
                    id:label
                    text: 
                        root.label_x_value  
                    font_size:root.text_size
                    font_name : root.text_font
                    color: [1,1,1,1]
                
        TagCompareHoverBox: 
            id:ycomparehoverbox 

                
<TagCompareHoverBox>
    size_hint:None,None
    width:dp(0.01)
    height:dp(0.01)
    BoxLayout:
        id:main_box
        size_hint:None,None
        width:label.texture_size[0] + dp(8) if root.show_widget else dp(8)
        height:label.texture_size[1] + dp(6) if root.show_widget else dp(0.01)
        opacity:1 if root.show_widget else 0
        padding: dp(2),0,0,0
        x: root.x_hover_pos + dp(4)
        y: root.y_hover_pos - label.texture_size[1]/2-dp(3) + root.hover_offset
    
        canvas.before:            
            Color:
                rgba: root.custom_color if root.custom_color else [0,0,0,1]
            Rectangle:
                pos: self.pos
                size: self.size  

            Triangle:
                points:
                    [ \
                    root.x_hover_pos, root.y_hover_pos, \
                    main_box.x, root.y_hover_pos+ dp(4) + root.hover_offset, \
                    main_box.x, root.y_hover_pos- dp(4)  + root.hover_offset \
                    ]
            SmoothLine:
                width:dp(1)
                points:
                    [ \
                    root.x_hover_pos, root.y_hover_pos, \
                    main_box.x, root.y_hover_pos + root.hover_offset \
                    ]                
        Label:
            id:label
            text: root.label_y_value  
            color:
                [0,0,0,1] if (root.custom_color[0]*0.299 + \
                root.custom_color[1]*0.587 + root.custom_color[2]*0.114) > 186/255 \
                else [1,1,1,1]
            font_size:root.text_size
            font_name : root.text_font  
            
        FloatLayout:
            size_hint: None,None
            width: dp(0.01) 
            height: dp(0.01) 
            BoxLayout:
                size_hint:None,None
                x:main_box.x + main_box.width + dp(2)
                y:main_box.y + main_box.height/2-label2.texture_size[1]/2
                width:label2.texture_size[0]
                height:label2.texture_size[1]
                canvas.before:            
                    Color:
                        rgba: [1,1,1,0.7]
                    Rectangle:
                        pos: self.pos
                        size: self.size                 
                Label:
                    id:label2
                    text: root.label_y 
                    font_size:root.text_size
                    color: [0,0,0,1]
                    font_name : root.text_font              
              
        ''')
