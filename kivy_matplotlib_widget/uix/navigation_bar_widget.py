from matplotlib.backend_bases import NavigationToolbar2
from kivy.properties import ObjectProperty, OptionProperty,ListProperty,BooleanProperty,NumericProperty,StringProperty
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.clock import Clock
from kivy.factory import Factory
from kivy_matplotlib_widget.uix.hover_widget import add_hover
from kivy.core.window import Window
from kivy.metrics import dp 

from kivy_matplotlib_widget import fonts_path
from kivy.core.text import LabelBase
LabelBase.register(name="NavigationIcons",fn_regular= fonts_path + "NavigationIcons.ttf")


class MatplotNavToolbar(BoxLayout):

    """Figure Toolbar"""
    pan_btn = ObjectProperty(None)
    zoom_btn = ObjectProperty(None)
    home_btn = ObjectProperty(None)
    back_btn = ObjectProperty(None)
    forward_btn = ObjectProperty(None)
    info_lbl = ObjectProperty(None)
    _navtoolbar = None  # Internal NavToolbar logic
    figure_widget = ObjectProperty(None)

    def __init__(self, figure_widget=None, *args, **kwargs):
        super(MatplotNavToolbar, self).__init__(*args, **kwargs)
        self.figure_widget = figure_widget

    def on_figure_widget(self, obj, value):
        self.figure_widget.bind(figcanvas=self._canvas_ready)

    def _canvas_ready(self, obj, value):
        self._navtoolbar = _NavigationToolbar(value, self)
        self._navtoolbar.figure_widget = obj


class _NavigationToolbar(NavigationToolbar2):
    figure_widget = None

    def __init__(self, canvas, widget):
        self.widget = widget
        super(_NavigationToolbar, self).__init__(canvas)
        
    def on_kv_post(self):
        if self.figure_widget:
            self._init_toolbar()

    def _init_toolbar(self):
        print('init toolbar')
        self.widget.home_btn.bind(on_press=self.home)
        self.widget.pan_btn.bind(on_press=self.pan)
        self.widget.zoom_btn.bind(on_press=self.zoom) 
        self.widget.back_btn.bind(on_press=self.back)
        self.widget.forward_btn.bind(on_press=self.forward)

    def dynamic_update(self):
        self.canvas.draw()

    def draw_rubberband(self, event, x0, y0, x1, y1):
        self.figure_widget.draw_box(event, x0, y0, x1, y1)

    def set_message(self, s):
        self.widget.info_lbl.text = s

class KivyMatplotNavToolbar(RelativeLayout):

    """Figure Toolbar"""
    pan_btn = ObjectProperty(None)
    zoom_btn = ObjectProperty(None)
    home_btn = ObjectProperty(None)
    back_btn = ObjectProperty(None)
    forward_btn = ObjectProperty(None)
    info_lbl = ObjectProperty(None)
    _navtoolbar = None  # Internal NavToolbar logic
    figure_wgt = ObjectProperty(None)
    orientation_type = OptionProperty(
        "actionbar", options=["rail", "actionbar"])
    nav_icon = OptionProperty(
        "normal", options=["minimal", "normal","all","custom"])
    hover_mode = OptionProperty(
        "touch", options=["touch", "desktop"])    
    
    custom_icon = ListProperty([])
    show_cursor_data = BooleanProperty(False)
    cursor_data_font_size = NumericProperty(dp(12))
    cursor_data_font=StringProperty("Roboto")
    icon_font_size = NumericProperty(dp(36))
    nav_btn_size = NumericProperty(dp(80))
    compare_hover = BooleanProperty(False)
    drag_legend = BooleanProperty(False) #only if nav_icon is 'all'

    def __init__(self, figure_wgt=None, *args, **kwargs):
        super(KivyMatplotNavToolbar, self).__init__(*args, **kwargs)
        self.figure_wgt = figure_wgt
           
    def on_kv_post(self,_):
        if self.nav_icon=="minimal" and not self.custom_icon:

            #pan button
            self.add_nav_btn("pan",self.set_touch_mode,mode='pan',btn_type='group')

            #zoombox button
            self.add_nav_btn("zoom",self.set_touch_mode,mode='zoombox',btn_type='group')

        elif self.nav_icon=="normal" and not self.custom_icon:

            #home button
            self.add_nav_btn("home",self.home)

            #pan button
            self.add_nav_btn("pan",self.set_touch_mode,mode='pan',btn_type='group')

            #zoombox button
            self.add_nav_btn("zoom",self.set_touch_mode,mode='zoombox',btn_type='group')

            if self.hover_mode=="touch" and not self.compare_hover:
                #cursor button
                self.add_nav_btn("cursor",self.set_touch_mode,mode='cursor',btn_type='group')
            elif self.hover_mode=="touch":
                #nearest hover button
                self.add_nav_btn("hover",self.change_hover_type,mode='nearest',btn_type='hover_type')
                #compare hover button
                self.add_nav_btn("hover_compare",self.change_hover_type,mode='compare',btn_type='hover_type')                
                
            elif self.compare_hover:
                #nearest hover button
                self.add_nav_btn("hover",self.change_hover_type,mode='nearest',btn_type='hover_type')
                #compare hover button
                self.add_nav_btn("hover_compare",self.change_hover_type,mode='compare',btn_type='hover_type') 

        elif self.nav_icon=="all" and not self.custom_icon:

            #home button
            self.add_nav_btn("home",self.home)

            #home button
            self.add_nav_btn("back",self.back)

            #home button
            self.add_nav_btn("forward",self.forward)            
            
            #pan button
            self.add_nav_btn("pan",self.set_touch_mode,mode='pan',btn_type='group')

            #zoombox button
            self.add_nav_btn("zoom",self.set_touch_mode,mode='zoombox',btn_type='group')

            if self.hover_mode=="touch" and not self.compare_hover:
                #cursor button
                self.add_nav_btn("cursor",self.set_touch_mode,mode='cursor',btn_type='group')

            elif self.hover_mode=="touch":
                #nearest hover button
                self.add_nav_btn("hover",self.change_hover_type,mode='nearest',btn_type='group')
                #compare hover button
                self.add_nav_btn("hover_compare",self.change_hover_type,mode='compare',btn_type='group')                
                
            elif self.compare_hover:
                #nearest hover button
                self.add_nav_btn("hover",self.change_hover_type,mode='nearest',btn_type='group')
                #compare hover button
                self.add_nav_btn("hover_compare",self.change_hover_type,mode='compare',btn_type='group') 

            #minmax button
            self.add_nav_btn("minmax",self.set_touch_mode,mode='minmax',btn_type='group')

            #home button
            self.add_nav_btn("autoscale",self.autoscale)
            
            #add_drag_legend
            if self.drag_legend:
                self.add_nav_btn("drag_legend",self.set_touch_mode,mode='drag_legend',btn_type='group')

        elif self.custom_icon:
            pass
        
        if self.show_cursor_data:
            Window.bind(mouse_pos=self.on_motion) 

    def on_motion(self,*args):
        '''Kivy Event to trigger mouse event on motion
           `enter_notify_event`.
        '''
        if self.figure_wgt._pressed:  # Do not process this event if there's a touch_move
            return
        pos = args[1]
        newcoord = self.figure_wgt.to_widget(pos[0], pos[1])
        x = newcoord[0]
        y = newcoord[1]
        inside = self.figure_wgt.collide_point(x,y)
        if inside: 

            # will receive all motion events.
            if self.figure_wgt.figcanvas:
                #avoid in motion if touch is detected
                if not len(self.figure_wgt._touches)==0:
                    return
               
                #transform kivy x,y touch event to x,y data
                x_format,y_format=self.figure_wgt.get_data_xy(x,y)

                if x_format and y_format:
                    self.current_label.text=f"{x_format}\n{y_format}"
                else:
                    self.current_label.text=""
                
    def add_nav_btn(self,icon,fct,mode=None,btn_type=None):
        if btn_type=='group':
            if 'hover' in icon:
                btn = Factory.NavToggleButton(group= "hover_type")
                if self.hover_mode=="touch":
                    btn.bind(on_release=lambda x:self.set_touch_mode('cursor'))
                    
                elif mode == 'nearest':
                    btn.state='down'
                    
                    
            else:
                btn = Factory.NavToggleButton(group= "toolbar_btn")
            btn.orientation_type=self.orientation_type
        else:
            btn = Factory.NavButton()  
            btn.orientation_type=self.orientation_type
        btn.icon = icon
        btn.icon_font_size=self.icon_font_size
        btn.nav_btn_size=self.nav_btn_size
        if mode:
            btn.bind(on_release=lambda x:fct(mode))
        else:
            btn.bind(on_release=lambda x:fct())
            
        if mode == 'pan':
            #by default pan button is press down
            btn.state='down'

        self.ids.container.add_widget(btn)        
          
    def set_touch_mode(self,mode):
        self.figure_wgt.touch_mode=mode
    def home(self):
        if hasattr(self.figure_wgt,'main_home'):
            self.figure_wgt.main_home()
        else:
            self.figure_wgt.home()
    def back(self):
        self.figure_wgt.back()   
    def forward(self):
        self.figure_wgt.forward()  
    def autoscale(self):
        self.figure_wgt.autoscale()        
        
    def change_hover_type(self,hover_type):
        add_hover(self.figure_wgt,mode=self.hover_mode,hover_type=hover_type)


Factory.register('MatplotNavToolbar', MatplotNavToolbar)

Builder.load_string('''
#:import nav_icons kivy_matplotlib_widget.icon_definitions.nav_icons                    
                    
<MatplotNavToolbar>:
    orientation: 'vertical'
    home_btn: home_btn
    pan_btn: pan_btn
    zoom_btn: zoom_btn
    info_lbl: info_lbl
    back_btn: back_btn
    forward_btn: forward_btn
    Label:
        id: info_lbl
        size_hint: 1, 0.3    
    BoxLayout:
        size_hint: 1, 0.7
        Button:
            id: home_btn
            text: "Home"
        Button:
            id: back_btn
            text: "Back"
            font_name:"NavigationIcons"
        Button:
            id: forward_btn
            text: "Forward" 
            font_name:"NavigationIcons"
        ToggleButton:
            id: pan_btn
            text: "Pan"
            group: "toolbar_btn"
            font_name:"NavigationIcons"
        ToggleButton:
            id: zoom_btn
            text: "Zoom"
            group: "toolbar_btn"
            font_name:"NavigationIcons"
                    
<KivyMatplotNavToolbar>:
    current_label: info_lbl2 if root.orientation_type=='rail' else info_lbl
    info_lbl: info_lbl
    info_lbl2: info_lbl2
    size_hint:1 if not root.orientation_type=='rail' else None,None if not root.orientation_type=='rail' else 1
    height: root.nav_btn_size if not root.orientation_type!='rail' else root.nav_btn_size
    width:root.nav_btn_size if not root.orientation_type=='rail' else root.nav_btn_size
    BoxLayout:
        orientation:'vertical' if root.orientation_type=='rail' else 'horizontal'
        #size_hint: None, None
        #size: self.minimum_size
        canvas.before:
            Color:
                rgba: (1, 1, 1, 1)
            Rectangle:
                pos: self.pos
                size: self.size        
        BoxLayout:
            size_hint_y: None
            size_hint_x: None if root.orientation_type=='rail' else 1
            height: "0.01dp" if root.orientation_type=='rail'else root.nav_btn_size 
            width:root.nav_btn_size           
            Label:
                id: info_lbl
                color: 0,0,0,1
                font_size: root.cursor_data_font_size
                font_name:root.cursor_data_font
        BoxLayout:
            id:container
            orientation:'vertical' if root.orientation_type=='rail' else 'horizontal'
            size_hint_x:1 if root.orientation_type=='rail' else None
            size_hint_y:None if root.orientation_type=='rail' else 1
            height: root.nav_btn_size*len(self.children) if root.orientation_type=='rail'else root.nav_btn_size
            width: root.nav_btn_size if root.orientation_type=='rail'else root.nav_btn_size*len(self.children)

        BoxLayout: 
            size_hint_y: 1 if root.orientation_type=='rail' else None
            size_hint_x: None
            height:root.nav_btn_size
            width:root.nav_btn_size if root.orientation_type=='rail' else" 0.001dp"
            Label:
                id: info_lbl2
                color: 0,0,0,1
                font_size: root.cursor_data_font_size
                font_name:root.cursor_data_font
                

<NavToggleButton@ToggleButton>
    icon:"pan"
    icon_font_size: dp(36)
    nav_btn_size:dp(80)
    orientation_type:'rail'
    text: u"{}".format(nav_icons[self.icon]) if self.icon in nav_icons else ""
    group: "toolbar_btn"
    font_name:"NavigationIcons"
    font_size:root.icon_font_size
    color: 0,0,0,1 if self.state=='down' else 0.38
    size_hint:1 if root.orientation_type=='rail' else None,None if root.orientation_type=='rail' else 1
    height: root.nav_btn_size
    width:root.nav_btn_size 
    background_normal: ''
    background_down: ''
    background_color :1,1,1,1  
    on_release:
        self.state='down'     

<NavButton@Button>
    icon:"home"
    icon_font_size: dp(36)
    nav_btn_size:dp(80)
    orientation_type:'rail'
    size_hint:1 if root.orientation_type=='rail' else None,None if root.orientation_type=='rail' else 1
    text: u"{}".format(nav_icons[self.icon]) if self.icon in nav_icons else ""
    font_name:"NavigationIcons"
    font_size:root.icon_font_size
    color: 0,0,0,1
    height: root.nav_btn_size
    width:root.nav_btn_size 
    background_normal: ''
    background_color :1,1,1,1


        ''')