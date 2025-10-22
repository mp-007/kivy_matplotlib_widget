""" MatplotFigure is based on https://github.com/jeysonmc/kivy_matplotlib
and kivy scatter
"""

import math
import copy

import matplotlib
matplotlib.use('Agg')
from kivy.graphics.texture import Texture
from kivy.graphics.transformation import Matrix
from kivy.lang import Builder
from kivy.properties import ObjectProperty, ListProperty, BooleanProperty, BoundedNumericProperty, AliasProperty, \
    NumericProperty
from kivy.uix.widget import Widget
from kivy.vector import Vector
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.transforms import Bbox
from matplotlib.backend_bases import ResizeEvent
from matplotlib.backend_bases import MouseEvent
from kivy.metrics import dp
import numpy as np
from kivy.base import EventLoop

class MatplotFigureGeneral(Widget):
    """Widget to show a matplotlib figure in kivy.
    The figure is rendered internally in an AGG backend then
    the rgba data is obtained and blitted into a kivy texture.
    """

    figure = ObjectProperty(None)
    _box_pos = ListProperty([0, 0])
    _box_size = ListProperty([0, 0])
    _img_texture = ObjectProperty(None)
    _alpha_box = NumericProperty(0)
    _bitmap = None
    _pressed = False
    do_update=False
    figcanvas = ObjectProperty(None)
    translation_touches = BoundedNumericProperty(1, min=1)
    do_scale = BooleanProperty(True)
    scale_min = NumericProperty(0.01)
    scale_max = NumericProperty(1e20)
    transform = ObjectProperty(Matrix())
    _alpha_hor = NumericProperty(0)
    _alpha_ver = NumericProperty(0)
    pos_x_rect_hor=NumericProperty(0)
    pos_y_rect_hor=NumericProperty(0)
    pos_x_rect_ver=NumericProperty(0)
    pos_y_rect_ver=NumericProperty(0)
    invert_rect_ver = BooleanProperty(False)
    invert_rect_hor = BooleanProperty(False)

    def on_figure(self, obj, value):
        self.figcanvas = _FigureCanvas(self.figure, self)
        self.figcanvas._isDrawn = False
        l, b, w, h = self.figure.bbox.bounds
        w = int(math.ceil(w))
        h = int(math.ceil(h))
        self.width = w
        self.height = h

        # Texture
        self._img_texture = Texture.create(size=(w, h))

    def __init__(self, **kwargs):
        super(MatplotFigureGeneral, self).__init__(**kwargs)

        #figure info
        self.figure = None
        self.axes = None
        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None

        #option
        self.zoompan = None
        self.fast_draw=True
        self.draw_left_spline=False #available only when fast_draw is True
        self.touch_mode='pan'
        self.hover_on = False
        self.xsorted = True #to manage x sorted data (if numpy is used)
        self.minzoom = dp(20) #minimum pixel distance to apply zoom

        #zoom box coordonnate
        self.x0_box = None
        self.y0_box = None
        self.x1_box = None
        self.y1_box = None

        #clear touches on touch up
        self._touches = []
        self._last_touch_pos = {}

        #background
        self.background=None
        self.background_patch_copy=None

        EventLoop.window.bind(mouse_pos=self.on_mouse_move)
        self.bind(size=self._onSize)


    def reset_touch(self) -> None:
        """ reset touch

        Return:
            None
        """
        self._touches = []
        self._last_touch_pos = {}

    def _draw_bitmap(self):
        """ draw bitmap method. based on kivy scatter method"""
        if self._bitmap is None:
            print("No bitmap!")
            return
        self._img_texture = Texture.create(size=(self.bt_w, self.bt_h))
        self._img_texture.blit_buffer(
            bytes(self._bitmap), colorfmt="rgba", bufferfmt='ubyte')
        self._img_texture.flip_vertical()

    def on_mouse_move(self, window, mouse_pos):
        """ Mouse move """
        if self._pressed:  # Do not process this event if there's a touch_move
            return
        x, y = mouse_pos
        if self.collide_point(x, y):
            real_x, real_y = x - self.pos[0], y - self.pos[1]
            if self.figcanvas:
                # self.figcanvas.motion_notify_event(x, real_y, guiEvent=None)

                self.figcanvas._lastx, self.figcanvas._lasty = x, real_y
                s = 'motion_notify_event'
                event = MouseEvent(s, self.figcanvas, x, y, self.figcanvas._button, self.figcanvas._key,
                                   guiEvent=None)
                self.figcanvas.callbacks.process(s, event)

    def on_touch_down(self, event):
        x, y = event.x, event.y

        if self.collide_point(x, y):
            self._pressed = True
            real_x, real_y = x - self.pos[0], y - self.pos[1]
            # self.figcanvas.button_press_event(x, real_y, 1, guiEvent=event)

            self.figcanvas._button = 1
            s = 'button_press_event'
            mouseevent = MouseEvent(s, self.figcanvas, x, real_y, 1, self.figcanvas._key,
                                dblclick=False, guiEvent=event)
            self.figcanvas.callbacks.process(s, mouseevent)

    def on_touch_move(self, event):
        """ Mouse move while pressed """
        x, y = event.x, event.y
        if self.collide_point(x, y):
            real_x, real_y = x - self.pos[0], y - self.pos[1]
            # self.figcanvas.motion_notify_event(x, real_y, guiEvent=event)

            self.figcanvas._lastx, self.figcanvas._lasty = x, real_y
            s = 'motion_notify_event'
            event = MouseEvent(s, self.figcanvas, x, y, self.figcanvas._button, self.figcanvas._key,
                               guiEvent=event)
            self.figcanvas.callbacks.process(s, event)

    def on_touch_up(self, event):
        x, y = event.x, event.y
        if self._box_size[0] > 1 or self._box_size[1] > 1:
            self.reset_box()
        if self.collide_point(x, y):
            pos_x, pos_y = self.pos
            real_x, real_y = x - pos_x, y - pos_y
            # self.figcanvas.button_release_event(x, real_y, 1, guiEvent=event)

            s = 'button_release_event'
            event = MouseEvent(s, self.figcanvas, x, real_y, 1, self.figcanvas._key, guiEvent=event)
            self.figcanvas.callbacks.process(s, event)
            self.figcanvas._button = None

            self._pressed = False

    def _onSize(self, o, size):
        """ _onsize method """
        if self.figure is None:
            return
        # Create a new, correctly sized bitmap
        self._width, self._height = size
        self._isDrawn = False

        if self._width <= 1 or self._height <= 1:
            return

        dpival = self.figure.dpi
        winch = self._width / dpival
        hinch = self._height / dpival
        self.figure.set_size_inches(winch, hinch)

        s = 'resize_event'
        event = ResizeEvent(s, self.figcanvas)
        self.figcanvas.callbacks.process(s, event)
        self.figcanvas.draw_idle()

        self.figcanvas.draw()

    def update_lim(self):
        """ update axis lim if zoombox is used"""
        ax=self.axes

        self.do_update=False

        ax.set_xlim(left=min(self.x0_box,self.x1_box),right=max(self.x0_box,self.x1_box))
        ax.set_ylim(bottom=min(self.y0_box,self.y1_box),top=max(self.y0_box,self.y1_box))

    def reset_box(self):
        """ reset zoombox and apply zoombox limit if zoombox option if selected"""
        # if min(abs(self._box_size[0]),abs(self._box_size[1]))>self.minzoom:
        #     trans = self.axes.transData.inverted()
        #     self.x0_box, self.y0_box = trans.transform_point((self._box_pos[0]-self.pos[0], self._box_pos[1]-self.pos[1]))
        #     self.x1_box, self.y1_box = trans.transform_point((self._box_size[0]+self._box_pos[0]-self.pos[0], self._box_size[1]+self._box_pos[1]-self.pos[1]))
        #     self.do_update=True

        self._box_size = 0, 0
        self._box_pos = 0, 0
        self._alpha_box=0

        self._alpha_hor=0
        self._alpha_ver=0
        self.invert_rect_hor = False
        self.invert_rect_ver = False

    def draw_box(self, event, x0, y0, x1, y1) -> None:
        """ Draw zoombox method

        Args:
            event: touch kivy event
            x0: x coordonnate init
            x1: y coordonnate of move touch
            y0: y coordonnate init
            y1: x coordonnate of move touch

        Return:
            None
        """
        pos_x, pos_y = self.pos
        # Kivy coords
        y0 = pos_y + y0
        y1 = pos_y + y1

        if abs(y1-y0)>dp(5) or abs(x1-x0)>dp(5):
            self._alpha_box=0.3
            self._alpha_rect=0

        if x1>x0:
            self.invert_rect_ver=False
        else:
            self.invert_rect_ver=True
        if y1>y0:
            self.invert_rect_hor=False
        else:
            self.invert_rect_hor=True

        self._box_pos = x0, y0
        self._box_size = x1 - x0, y1 - y0

class _FigureCanvas(FigureCanvasAgg):
    """Internal AGG Canvas"""

    def __init__(self, figure, widget, *args, **kwargs):
        self.widget = widget
        super(_FigureCanvas, self).__init__(figure, *args, **kwargs)

    def draw(self):
        """
        Render the figure using agg.
        """
        super(_FigureCanvas, self).draw()
        agg = self.get_renderer()
        w, h = agg.width, agg.height
        self._isDrawn = True

        self.widget.bt_w = w
        self.widget.bt_h = h
        self.widget._bitmap = agg.buffer_rgba()
        self.widget._draw_bitmap()

    def blit(self, bbox=None):
        """
        Render the figure using agg (blit method).
        """
        agg = self.get_renderer()
        w, h = agg.width, agg.height
        self.widget._bitmap = agg.buffer_rgba()
        self.widget.bt_w = w
        self.widget.bt_h = h
        self.widget._draw_bitmap()

from kivy.factory import Factory

Factory.register('MatplotFigureGeneral', MatplotFigureGeneral)

Builder.load_string('''
<MatplotFigureGeneral>
    canvas:
        Color:
            rgba: (1, 1, 1, 1)
        Rectangle:
            pos: self.pos
            size: self.size
            texture: self._img_texture
        Color:
            rgba: 0, 0, 1, self._alpha_box
        BorderImage:
            source: 'border.png'
            pos: self._box_pos
            size: self._box_size
            border:
                dp(1) if root.invert_rect_hor else -dp(1), \
                dp(1) if root.invert_rect_ver else -dp(1), \
                dp(1) if root.invert_rect_hor else -dp(1), \
                dp(1) if root.invert_rect_ver else -dp(1)
        ''')
