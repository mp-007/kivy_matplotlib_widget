
from kivy.lang import Builder
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import DragBehavior
from kivy.factory import Factory as F
from kivy.metrics import dp


kv = '''

<LineSettingFloatLayout>:
    size_hint: None,None
    height: dp(0.001)
    width:dp(0.001)    
    LineSetting:
        id:line_setting

<LineSetting>:
    drag_rectangle: self.x, self.y, self.width, self.height
    drag_timeout: 10000000000000000
    drag_distance: 0
    orientation: 'horizontal'
    size_hint: None,None
    height:dp(44) if self.show_setting else dp(0.01)
    width:self.minimum_width if self.show_setting else dp(0.01)
    show_setting:False
    opacity: 1 if self.show_setting else 0
    disabled: False if self.show_setting else True

    ColorButton:
        size_hint_x:None
        width:dp(44)
        id: color_picker_button
        text:"Color"
        on_press: root.show_color_picker(self)
    MyButton:
        size_hint_x:None
        width:dp(44)        
        id: line_width_button
        text: 'Width'
        text2: '1'
        on_release: root.line_width_dropdown.open(self)
    MyButton:
        size_hint_x:None
        width:dp(44)        
        id: line_type_button
        text: 'Style'
        text2: '-'
        on_release: root.line_type_dropdown.open(self)

<CustomColorWheel>:
    color_button_ok:color_button_ok
    clr_picker:clr_picker
    mycolor:0,0,0,1
    ColorWheel:
        id :clr_picker
    
    BoxLayout:
        size_hint_x: 0.2
        orientation:'vertical'
        Widget:
            size_hint_y: 0.2
            canvas.before:
                Color:
                    rgba: root.mycolor
                Rectangle:
                    size: self.size
                    pos: self.pos  
        Widget
        Button:
            id: color_button_ok
            text: 'OK'
            size_hint_y: 0.2
            on_press: root.dismiss_color_popup()
        
<ColorButton@ButtonBehavior+BoxLayout>:
    text:''
    mycolor:0,0,0,1
    canvas.before:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            size: self.size
            pos: self.pos
        Color:
            rgba: 0,0,0,1
        Line:
            width: 1
            rectangle: self.x, self.y, self.width, self.height
    orientation:'vertical'
    padding:dp(4),0,dp(4),0
    Widget:
    Label:
        text:root.text
        color:0,0,0,1
    Widget:
        size_hint_y:None
        height:dp(2)
    BoxLayout:
        
        canvas.before:
            Color:
                rgba: root.mycolor
            Rectangle:
                size: self.size
                pos: self.pos        
    Widget:

<MyButton@ButtonBehavior+BoxLayout>:
    text:'text'
    text2:''
    mycolor:0,0,0,1
    canvas.before:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            size: self.size
            pos: self.pos
        Color:
            rgba: 0,0,0,1
        Line:
            width: 1
            rectangle: self.x, self.y, self.width, self.height
    orientation:'vertical'
    padding:dp(4),0,dp(4),0
    Widget:   
    BoxLayout:
        size_hint_y:None
        height:id_text.texture_size[1]
        Label:
            id:id_text
            text:root.text
            color:0,0,0,1
    Widget:
        size_hint_y:None
        height:dp(2)  
    BoxLayout:
        size_hint_y:None
        height:id_text2.texture_size[1]        
        Label:
            id:id_text2
            text:root.text2
            color:0,0,0,1      
    Widget:

<MyButton2@ButtonBehavior+BoxLayout>:
    text:'text'
    padding:1,1,1,1
    BoxLayout:
        canvas.before:
            Color:
                rgba: 1,1,1,1
            Rectangle:
                size: self.size
                pos: self.pos
            Color:
                rgba: 0,0,0,1
            Line:
                width: 1
                rectangle: self.x, self.y, self.width, self.height
        Label:
            text:root.text
            color:0,0,0,1
        
'''

Builder.load_string(kv)

class LineSettingFloatLayout(FloatLayout):
    def __init__(self, **kwargs):
        super(LineSettingFloatLayout, self).__init__(**kwargs)

class CustomColorWheel(BoxLayout):
    def __init__(self, line_setting, color_popup, **kwargs):
        super(CustomColorWheel, self).__init__(**kwargs)
        self.line_setting = line_setting
        self.color_popup = color_popup
        
    def on_kv_post(self,_):
        self.clr_picker.bind(color=self.on_color)

    def change_color(self, color):
        self.line_setting.change_color(color)

    def dismiss_color_popup(self):
        self.color_popup.dismiss()
        
    def on_color(self,instance, value):
        self.line_setting.ids.color_picker_button.mycolor = value
        self.line_setting.line_name.set_color(value)
        self.mycolor = value
        self.line_setting.figure_wgt.figure.canvas.draw_idle()
        self.line_setting.figure_wgt.figure.canvas.flush_events()    

class LineSetting(DragBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super(LineSetting, self).__init__(**kwargs)
        self.line_width_dropdown = self.create_line_width_dropdown()
        self.line_type_dropdown = self.create_line_type_dropdown()
        self.figure_wgt = None
        self.line_name = None
        self.color_popup=None


    def show_color_picker(self, button):
        if self.color_popup is None:
            color_popup = Popup(title='Color selection', size_hint=(0.4, 0.4))
            custom_color_wheel = CustomColorWheel(line_setting=self, color_popup=color_popup)
            color_popup.content = custom_color_wheel
        color_popup.content.mycolor = self.ids.color_picker_button.mycolor
        color_popup.open()

    def create_line_width_dropdown(self):
        dropdown = DropDown()
        for i in range(1, 5):
            btn = F.MyButton2(size_hint=(None,None), height=dp(44),width=dp(44))
            btn.text=str(i)            
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)
        dropdown.bind(on_select=lambda instance, x: self.on_width_select(x))
        return dropdown

    def on_width_select(self, selected_width):
        self.ids.line_width_button.text2 = selected_width
        self.line_name.set_linewidth(selected_width)
        self.figure_wgt.figure.canvas.draw_idle()
        self.figure_wgt.figure.canvas.flush_events()

    def create_line_type_dropdown(self):
        dropdown = DropDown()
        line_types = ['-', '--', '-.', ':']
        for line_type in line_types:
            btn = F.MyButton2(size_hint=(None,None), height=dp(44),width=dp(44))
            btn.text=line_type
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)
        dropdown.bind(on_select=lambda instance, x: self.on_line_type_select(x))
        return dropdown

    def on_line_type_select(self, selected_type):
        self.ids.line_type_button.text2 = selected_type
        self.line_name.set_linestyle(selected_type)
        self.figure_wgt.figure.canvas.draw_idle()
        self.figure_wgt.figure.canvas.flush_events()