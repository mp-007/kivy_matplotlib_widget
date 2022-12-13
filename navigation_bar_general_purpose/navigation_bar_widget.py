from matplotlib.backend_bases import NavigationToolbar2
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

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

from kivy.factory import Factory
Factory.register('MatplotNavToolbar', MatplotNavToolbar)

Builder.load_string('''
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
        Button:
            id: forward_btn
            text: "Forward"            
        ToggleButton:
            id: pan_btn
            text: "Pan"
            group: "toolbar_btn"
        ToggleButton:
            id: zoom_btn
            text: "Zoom"
            group: "toolbar_btn"

        ''')