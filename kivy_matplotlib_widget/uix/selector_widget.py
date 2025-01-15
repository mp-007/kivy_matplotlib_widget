from kivy.lang import Builder
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import (ColorProperty,
                             ObjectProperty,
                             OptionProperty,
                             BooleanProperty,
                             ListProperty,
                             NumericProperty)
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform

import numpy as np
from matplotlib.path import Path
from matplotlib.patches import Ellipse as Ellipse_mpl
import matplotlib.colors as mcolors

from functools import partial
from math import cos, sin, atan2, pi
from typing import List, Optional

from kivy.clock import Clock
from kivy.graphics import Ellipse, Line, Color, Point, Mesh, PushMatrix, \
    PopMatrix, Rotate, InstructionGroup
from kivy.graphics.tesselator import Tesselator
from kivy.event import EventDispatcher
import copy


kv = '''
<ResizeSelect>:     
    canvas.before:
        # TOP LINE
        Color:
            rgba: root.top_color
        Line:
            width: dp(1)
            points: 
                (self.x + dp(7), self.top, self.right - dp(7), self.top) if root.alpha \
                else (self.x, self.top, self.right, self.top)# Top line
            cap: 'round'
            joint: 'round'
            dash_offset: 2
            dash_length: 10
            close: False

        # BOTTOM LINE
        Color:
            rgba: root.bottom_color
        Line:
            width: dp(1)
            points: 
                (self.x + dp(7), self.y, self.right - dp(7), self.y)  if root.alpha \
                else (self.x, self.y, self.right, self.y)# Bottom
            cap: 'round'
            joint: 'round'
            dash_offset: 2
            dash_length: 10
            close: False

        # LEFT LINE
        Color:
            rgba: root.left_color
        Line:
            width: dp(1)
            points: 
                (self.x, self.y+dp(7), self.x, self.top - dp(7)) if root.alpha \ 
                else (self.x, self.y, self.x, self.top)# Left
            cap: 'round'
            joint: 'round'
            dash_offset: 2
            dash_length: 10
            close: False

        # RIGHT LINE
        Color:
            rgba: root.right_color
        Line:
            width: dp(1)
            points: 
                (self.right, self.y + dp(7), self.right, self.top - dp(7)) if root.alpha \
                else (self.right, self.y, self.right, self.top)# Right
            cap: 'round'
            joint: 'round'
            dash_offset: 2
            dash_length: 10
            close: False

        # Upper left rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.x, self.top - dp(7)
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]                
        Line:
            width: dp(1)
            points: ( \
                self.x, self.top - dp(7), \
                self.x + dp(7), self.top - dp(7),  self.x + dp(7), self.top, \
                self.x, self.top, \
                self.x, self.top - dp(7))  # Horizontal
            cap: 'round'
            joint: 'round'
            close: False

        # Bottom left rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.x, self.y
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.x, self.y, \
                self.x + dp(7), self.y,  self.x + dp(7), self.y + dp(7), \
                self.x, self.y + dp(7), \
                self.x, self.y)  # Vertical
            cap: 'round'
            joint: 'round'
            close: True

        # Bottom right rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.right - dp(7), self.y
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.right - dp(7), self.y, \
                self.right - dp(7), self.y + dp(7),  self.right, self.y + dp(7), \
                self.right, self.y, \
                self.right - dp(7), self.y)  # Vertical
            cap: 'round'
            joint: 'round'
            close: True
            
        # Upper right rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.right - dp(7), self.top - dp(7)
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.right - dp(7), self.top - dp(7), \
                self.right - dp(7), self.top,  self.right, self.top, \
                self.right, self.top - dp(7), \
                self.right - dp(7), self.top - dp(7))  # Horizontal
            cap: 'round'
            joint: 'round'
            close: True

        # Upper edge rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.x + self.width/2 - dp(3.5), self.top - dp(7)
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.x + self.width/2 - dp(3.5), self.top - dp(7), \
                self.x + self.width/2 + dp(3.5), self.top - dp(7),  self.x + self.width/2 + dp(3.5), self.top, \
                self.x + self.width/2 - dp(3.5), self.top, \
                self.x + self.width/2 - dp(3.5), self.top - dp(7))  # Horizontal
            cap: 'round'
            joint: 'round'
            close: True

        # Left edge rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.x, self.y + self.height/2 - dp(3.5)
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.x, self.y + self.height/2 - dp(3.5), \
                self.x + dp(7), self.y + self.height/2 - dp(3.5), \
                self.x + dp(7), self.y + self.height/2 + dp(3.5), \
                self.x, self.y + self.height/2 + dp(3.5), \
                self.x, self.y + self.height/2 - dp(3.5))  # Vertical
            cap: 'round'
            joint: 'round'
            close: True

        # Right edge rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.right - dp(7), self.y + self.height/2 - dp(3.5)
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.right - dp(7), self.y + self.height/2 - dp(3.5), \
                self.right, self.y + self.height/2 - dp(3.5), \
                self.right, self.y + self.height/2 + dp(3.5), \
                self.right - dp(7), self.y + self.height/2 + dp(3.5), \
                self.right - dp(7), self.y + self.height/2 - dp(3.5))  # Vertical
            cap: 'round'
            joint: 'round'
            close: True

        # Bottom edge rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.x + self.width/2 - dp(3.5), self.y
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.x + self.width/2 - dp(3.5), self.y, \
                self.x + self.width/2 + dp(3.5), self.y, \
                self.x + self.width/2 + dp(3.5), self.y + dp(7), \
                self.x + self.width/2 - dp(3.5), self.y + dp(7), \
                self.x + self.width/2 - dp(3.5), self.y)  # Horizontal
            cap: 'round'
            joint: 'round'
            close: True
 
        
<SpanSelect>:     
    canvas.before:
        # TOP LINE
        Color:
            rgba: root.top_color
        Line:
            width: dp(1)
            points: 
                (self.x, self.top, self.right, self.top) if root.alpha \
                else (self.x, self.top, self.right, self.top)# Top line

        # BOTTOM LINE
        Color:
            rgba: root.bottom_color
        Line:
            width: dp(1)
            points: 
                (self.x, self.y, self.right, self.y)  if root.alpha \
                else (self.x, self.y, self.right, self.y)# Bottom

        # LEFT LINE
        Color:
            rgba: root.left_color
        Line:
            width: dp(1)
            points: 
                (self.x, self.y, self.x, self.top) if root.alpha \ 
                else (self.x, self.y, self.x, self.top)# Left


        # RIGHT LINE
        Color:
            rgba: root.right_color
        Line:
            width: dp(1)
            points: 
                (self.right, self.y, self.right, self.top) if root.alpha \
                else (self.right, self.y, self.right, self.top)# Right
                
        Color:
            rgba: root.span_color[0], root.span_color[1], root.span_color[2], self.span_alpha
        Rectangle:

            pos: self.pos
            size: self.size
              

    
<ResizeRelativeLayout>  
    resize_wgt:resize_wgt
    size_hint: None,None
    height: dp(0.001)
    width:dp(0.001)         
    ResizeSelect:
        id:resize_wgt
        desktop_mode:root.desktop_mode
        figure_wgt:root.figure_wgt
        size_hint: None, None
        size: dp(0.001),dp(0.001)
        pos: 0, 0
        opacity:0
        
<LassoRelativeLayout>  
    resize_wgt:resize_wgt
    size_hint: None,None
    height: dp(0.001)
    width:dp(0.001)         
    PainterWidget:
        id:resize_wgt
        pointsize:dp(0.01)
        #desktop_mode:root.desktop_mode
        figure_wgt:root.figure_wgt
        draw_mode:'freeform'
        size_hint: None, None
        size: dp(0.001),dp(0.001)
        pos: 0, 0
        opacity:1
        line_color : 0, 0, 0, 1
        selection_point_color : 62/255, 254/255, 1,1
        
<EllipseRelativeLayout>  
    resize_wgt:resize_wgt
    size_hint: None,None
    height: dp(0.001)
    width:dp(0.001)         
    PainterWidget2:
        id:resize_wgt
        pointsize:dp(0.01)
        #desktop_mode:root.desktop_mode
        figure_wgt:root.figure_wgt
        draw_mode:'ellipse'
        size_hint: None, None
        size: dp(0.001),dp(0.001)
        pos: 0, 0
        opacity:1
        line_color : 0, 0, 0, 1
        selection_point_color : 62/255, 254/255, 1,1
        
<SpanRelativeLayout>  
    resize_wgt:resize_wgt
    size_hint: None,None
    height: dp(0.001)
    width:dp(0.001)         
    SpanSelect:
        id:resize_wgt
        desktop_mode:root.desktop_mode
        figure_wgt:root.figure_wgt
        size_hint: None, None
        size: dp(0.001),dp(0.001)
        pos: 0, 0
        opacity:0

'''

MINIMUM_HEIGHT = 20.0
MINIMUM_WIDTH = 20.0

class ResizeRelativeLayout(RelativeLayout):
    figure_wgt = ObjectProperty()
    resize_wgt = ObjectProperty()
    desktop_mode = BooleanProperty(True)
    def __init__(self,figure_wgt=None,desktop_mode=True, **kwargs):
        self.figure_wgt=figure_wgt
        self.desktop_mode=desktop_mode
        super().__init__(**kwargs)
        
class LassoRelativeLayout(RelativeLayout):
    figure_wgt = ObjectProperty()
    resize_wgt = ObjectProperty()
    desktop_mode = BooleanProperty(True)
    def __init__(self,figure_wgt=None,desktop_mode=True, **kwargs):
        self.figure_wgt=figure_wgt
        self.desktop_mode=desktop_mode
        super().__init__(**kwargs)
        
class EllipseRelativeLayout(RelativeLayout):
    figure_wgt = ObjectProperty()
    resize_wgt = ObjectProperty()
    desktop_mode = BooleanProperty(True)
    def __init__(self,figure_wgt=None,desktop_mode=True, **kwargs):
        self.figure_wgt=figure_wgt
        self.desktop_mode=desktop_mode
        super().__init__(**kwargs)
        
class SpanRelativeLayout(RelativeLayout):
    figure_wgt = ObjectProperty()
    resize_wgt = ObjectProperty()
    desktop_mode = BooleanProperty(True)
    def __init__(self,figure_wgt=None,desktop_mode=True, **kwargs):
        self.figure_wgt=figure_wgt
        self.desktop_mode=desktop_mode
        super().__init__(**kwargs)
        
def line_dists(points, start, end):
    if np.all(start == end):
        return np.linalg.norm(points - start, axis=1)

    vec = end - start
    cross = np.cross(vec, start - points)
    return np.divide(abs(cross), np.linalg.norm(vec))


def rdp(M, epsilon=0):
    M = np.array(M)
    start, end = M[0], M[-1]
    dists = line_dists(M, start, end)

    index = np.argmax(dists)
    dmax = dists[index]

    if dmax > epsilon:
        result1 = rdp(M[:index + 1], epsilon)
        result2 = rdp(M[index:], epsilon)

        result = np.vstack((result1[:-1], result2))
    else:
        result = np.array([start, end])

    return result

class ResizeSelect(FloatLayout):
    top_color = ColorProperty("black")
    bottom_color = ColorProperty("black")
    left_color = ColorProperty("black")
    right_color = ColorProperty("black")
    highlight_color = ColorProperty("red")
    bg_color = ColorProperty([1,1,1,1])
    figure_wgt = ObjectProperty()
    desktop_mode = BooleanProperty(True)
    alpha = NumericProperty(1)

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.selected_side = None
        self.verts = []
        self.ax = None
        self.callback = None
        
        self.alpha_other = 0.3
        self.ind = []

        self.collection = None
        self.xys = None
        self.Npts = None
        self.fc = None
        
        self.line = None  
        self.ind_line=[]
        
        self.first_touch=None

    def on_kv_post(self,_):     
        if platform != 'android' and self.desktop_mode: #only bind mouse position if not android or if the user set desktop mode to false
            Window.bind(mouse_pos=self.on_mouse_pos)
            
    def update_bg_color(self):
        fig_bg_color = self.figure_wgt.figure.get_facecolor()
        rgb_fig_bg_color = mcolors.to_rgb(fig_bg_color)
        if (rgb_fig_bg_color[0]*0.299 + rgb_fig_bg_color[1]*0.587 + rgb_fig_bg_color[2]*0.114) > 186/255:
            self.bg_color = [1,1,1,1]
            self.bottom_color = (
                self.top_colors
            ) = self.left_color = self.right_color = [1,1,1,1]
            
        else:
            self.bg_color = [0,0,0,1]
            self.bottom_color = (
                self.top_colors
            ) = self.left_color = self.right_color = [0,0,0,1]
        
    def set_collection(self,collection):
        self.collection = collection
        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object
        self.fc = collection.get_facecolors()
        if len(self.fc) == 0:
            raise ValueError('Collection must have a facecolor')
        elif len(self.fc) == 1:
            self.fc = np.tile(self.fc, (self.Npts, 1))
            
    def set_line(self,line):
        self.line = line          

    def on_mouse_pos(self, something, touch):
        """
        When the mouse moves, we check the position of the mouse
        and update the cursor accordingly.
        """
        if self.opacity and self.figure_wgt.touch_mode=='selector' and self.collide_point(*self.to_widget(*touch)):
            
            collision = self.collides_with_control_points(something, self.to_widget(*touch))
            if collision in ["top left", "bottom right"]:
                Window.set_system_cursor("size_nwse")
            elif collision in ["top right", "bottom left"]:
                Window.set_system_cursor("size_nesw")
            elif collision in ["top", "bottom"]:
                Window.set_system_cursor("size_ns")
            elif collision in ["left", "right"]:
                Window.set_system_cursor("size_we")
            else:
                Window.set_system_cursor("size_all")
                
        elif self.figure_wgt.collide_point(*touch):
            Window.set_system_cursor("arrow")

    def collides_with_control_points(self, _, touch):
        """
        Returns True if the mouse is over a control point.
        """
        x, y = touch[0], touch[1]

        # Checking mouse is on left edge
        if self.x <= x <= self.x + dp(7):
            if self.y <= y <= self.y + dp(7):
                return "bottom left"
            elif self.y + dp(7) <= y <= self.y + self.height - dp(7):
                return "left"
            else:
                return "top left"

        # Checking mouse is on top edge
        elif self.x + dp(7) <= x <= self.x + self.width - dp(7):
            if self.y <= y <= self.y + dp(7):
                return "bottom"
            elif self.y + self.height - dp(7) <= y <= self.y + self.height:
                return "top"
            else:
                return False

        # Checking mouse is on right edge
        elif self.x + self.width - dp(7) <= x <= self.x + self.width:
            if self.y <= y <= self.y + dp(7):
                return "bottom right"
            elif self.y + dp(7) <= y <= self.y + self.height - dp(7):
                return "right"
            else:
                return "top right"

    def on_touch_down(self, touch):
        if self.figure_wgt.touch_mode != 'selector':
            return
        
        if self.collide_point(*touch.pos) and self.opacity:
            touch.grab(self)
            x, y = touch.pos[0], touch.pos[1]

            collision = self.collides_with_control_points("", touch.pos)

            if collision == "top":
                self.top_color = self.highlight_color
                self.selected_side = "top"
            elif collision == "bottom":
                self.bottom_color = self.highlight_color
                self.selected_side = "bottom"
            elif collision == "left":
                self.left_color = self.highlight_color
                self.selected_side = "left"
            elif collision == "right":
                self.right_color = self.highlight_color
                self.selected_side = "right"
            else:
                if collision == "top left":
                    self.selected_side = "top left"
                    self.top_color = self.highlight_color
                    self.left_color = self.highlight_color
                elif collision == "bottom right":
                    self.selected_side = "bottom right"
                    self.bottom_color = self.highlight_color
                    self.right_color = self.highlight_color
                elif collision == "top right":
                    self.selected_side = "top right"
                    self.top_color = self.highlight_color
                    self.right_color = self.highlight_color
                elif collision == "bottom left":
                    self.selected_side = "bottom left"
                    self.bottom_color = self.highlight_color
                    self.left_color = self.highlight_color
                else:
                    self.selected_side = None
                    self.top_color = self.highlight_color
                    self.bottom_color = self.highlight_color
                    self.left_color = self.highlight_color
                    self.right_color = self.highlight_color
        elif self.figure_wgt.collide_point(*self.to_window(*touch.pos)):
            if self.figure_wgt.touch_mode=='selector':
                if touch.is_double_tap and self.callback_clear:
                    self.callback_clear()
                    return
                
                touch.grab(self)
                x, y = touch.pos[0], touch.pos[1]
                self.pos = (x,y-5)
                self.size = (5,5)
                self.opacity=1
                self.first_touch = (x,y-5)
                self.selected_side = "new select"
                
            
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.figure_wgt.touch_mode != 'selector':
            return
        
        if touch.grab_current is self:
            x, y = self.to_window(*self.pos)

            top = y + self.height  # top of our widget
            right = x + self.width  # right of our widget
            
            if self.selected_side == "top":
                if self.height + touch.dy <= MINIMUM_HEIGHT:
                    return False
                self.height += touch.dy

            elif self.selected_side == "bottom":
                if self.height - touch.dy <= MINIMUM_HEIGHT:
                    return False
                self.height -= touch.dy
                self.y += touch.dy

            elif self.selected_side == "left":
                if self.width - touch.dx <= MINIMUM_WIDTH:
                    return False
                self.width -= touch.dx
                self.x += touch.dx

            elif self.selected_side == "right":
                if self.width + touch.dx <= MINIMUM_WIDTH:
                    return False
                self.width += touch.dx

            elif self.selected_side == "top left":
                if touch.dx > 0:
                    if self.width - touch.dx <= MINIMUM_WIDTH:
                        return False
                if touch.dy < 0:
                    if self.height + touch.dy <= MINIMUM_HEIGHT:
                        return False

                self.width -= touch.dx
                self.x += touch.dx  # OK
                self.height += touch.dy

            elif self.selected_side == "top right":
                if touch.dx < 0:
                    if self.width + touch.dx <= MINIMUM_WIDTH:
                        return False
                if touch.dy < 0:
                    if self.height + touch.dy <= MINIMUM_HEIGHT:
                        return False

                self.width += touch.dx
                self.height += touch.dy

            elif self.selected_side == "bottom left":
                if touch.dx > 0:
                    if self.width - touch.dx <= MINIMUM_WIDTH:
                        return False
                if touch.dy > 0:
                    if self.height - touch.dy <= MINIMUM_HEIGHT:
                        return False

                self.width -= touch.dx  # OK
                self.x += touch.dx
                self.height -= touch.dy
                self.y += touch.dy

            elif self.selected_side == "bottom right":
                if touch.dx < 0:
                    if self.width + touch.dx <= MINIMUM_WIDTH:
                        return False
                if touch.dy > 0:
                    if self.height - touch.dy <= MINIMUM_HEIGHT:
                        return False

                self.width += touch.dx
                self.height -= touch.dy
                self.y += touch.dy
                
            elif self.selected_side == "new select":
                self.width += touch.dx
                self.height -= touch.dy
                self.y += touch.dy  

            elif not self.selected_side:
                if self.figure_wgt.collide_point(*self.to_window(self.pos[0]+touch.dx,self.pos[1]+touch.dy )) and \
                    self.figure_wgt.collide_point(*self.to_window(self.pos[0] + self.size[0]+touch.dx,self.pos[1]+ self.size[1]+touch.dy )):
                    self.x += touch.dx
                    self.y += touch.dy
                
            if self.selected_side == "new select":
                self.alpha = 0
            else:
                self.alpha = 1

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.figure_wgt.touch_mode != 'selector':
            return
        
        if touch.grab_current is self:
            touch.ungrab(self)
            self.alpha = 1
            if (self.bg_color[0]*0.299 + \
            self.bg_color[1]*0.587 + self.bg_color[2]*0.114) > 186/255:
                self.bottom_color = (
                    self.top_colors
                ) = self.left_color = self.right_color = [0,0,0,1]
            else:
                self.bottom_color = (
                    self.top_colors
                ) = self.left_color = self.right_color = [1,1,1,1]                
            
            if self.first_touch and self.selected_side == "new select":
                self.check_if_reverse_selection(touch)
            
            if abs(self.size[0])<MINIMUM_WIDTH or abs(self.size[1])<MINIMUM_HEIGHT:
                self.reset_selection()
            else:
                if self.verts is not None:
                    self.verts = self._get_box_data()
                    self.onselect(self.verts)

            return True
        return super().on_touch_up(touch)
    
    def check_if_reverse_selection(self,last_touch):  

        if last_touch.x > self.first_touch[0] and \
            last_touch.y < self.first_touch[1]:

                return
            
        else:
            #reverse selection'
            if last_touch.x < self.first_touch[0]:
                self.pos[0] = last_touch.x
                self.size[0] = self.first_touch[0] - last_touch.x + 5
                
            if last_touch.y > self.first_touch[1]:
                self.size[1] = last_touch.y - self.first_touch[1] 
                self.pos[1] = last_touch.y - self.size[1]
                
            return


    def reset_selection(self):
        self.pos = (0,0)
        self.size = (dp(0.01),dp(0.01))
        self.opacity=0

        
    def _get_box_data(self):
        trans = self.ax.transData.inverted() 
        #get box 4points xis data
        x0 = self.to_window(*self.pos)[0]-self.figure_wgt.pos[0]
        y0 = self.to_window(*self.pos)[1]-self.figure_wgt.pos[1]
        x1 = self.to_window(*self.pos)[0]-self.figure_wgt.pos[0]
        y1 = self.to_window(*self.pos)[1] + self.height-self.figure_wgt.pos[1]
        x3 = self.to_window(*self.pos)[0] + self.width-self.figure_wgt.pos[0]
        y3 = self.to_window(*self.pos)[1]-self.figure_wgt.pos[1]
        x2 = self.to_window(*self.pos)[0] + self.width -self.figure_wgt.pos[0]
        y2 = self.to_window(*self.pos)[1] + self.height  -self.figure_wgt.pos[1]
        
        x0_box, y0_box = trans.transform_point((x0, y0)) 
        x1_box, y1_box = trans.transform_point((x1, y1))
        x2_box, y2_box = trans.transform_point((x2, y2))
        x3_box, y3_box = trans.transform_point((x3, y3))
        verts=[]
        verts.append((x0_box, y0_box))
        verts.append((x1_box, y1_box))
        verts.append((x2_box, y2_box))
        verts.append((x3_box, y3_box))

        return verts

    def onselect(self, verts):
        path = Path(verts)
        if self.collection:
            self.ind = np.nonzero(path.contains_points(self.xys))[0] #xys collection.get_offsets()
            self.fc[:, -1] = self.alpha_other
            self.fc[self.ind, -1] = 1
            self.collection.set_facecolors(self.fc)
        if self.line:
            xdata,ydata = self.line.get_data()
            self.ind_line = np.nonzero(path.contains_points(np.array([xdata,ydata]).T))[0]                  

        self.figure_wgt.figure.canvas.draw_idle()
        if self.callback:
            self.callback(self)
            
    def set_callback(self,callback):
        self.callback=callback

    def set_callback_clear(self,callback):
        self.callback_clear=callback           
        
    def clear_selection(self):

        if self.collection:
            self.ind = []
            self.fc[:, -1] = 1
            self.collection.set_facecolors(self.fc)
        if self.line:
            self.ind_line=[]
            
        self.reset_selection()
        self.figure_wgt.figure.canvas.draw_idle() 


def _rotate_pos(x, y, cx, cy, angle, base_angle=0.):
    """Rotates ``(x, y)`` by angle ``angle`` along a circle centered at
    ``(cx, cy)``.
    """
    hyp = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    xp = hyp * cos(angle + base_angle)
    yp = hyp * sin(angle + base_angle)
    return xp + cx, yp + cy


class PaintCanvasBehaviorBase(EventDispatcher):
    '''Abstract base class that can paint on a widget canvas. See
    :class:`PaintCanvasBehavior` for a the implementation that can be used
    with touch to draw upon.

    *Accepted keyboard keys and their meaning*

    You must inherit from :class:`~kivy.uix.behaviors.focus.FocusBehavior`
    to be able to be use the keyboard functionality.

    - `ctrl`: The has the same affect as :attr:`multiselect` being True.
    - `delete`: Deletes all the currently :attr:`selected_shapes`.
    - `right`, `left`, `up`, `down` arrow keys: moves the currently
      :attr:`selected_shapes` in the given direction.
    - `ctrl+a`: Selects all the :attr:`shapes`.
    - `ctrl+d`: Duplicates all the currently :attr:`selected_shapes`. Similar
      to :meth:`duplicate_selected_shapes`.
    - `escape`: de-selects all the currently :attr:`selected_shapes`.

    *Internal Logic*

    Each shape has a single point by which it is dragged. However, one can
    interact with other parts of the shape as determined by the shape instance.
    Selection happens by the controller when that point is touched. If
    multi-select or ctrl is held down, multiple shapes can be selected this
    way. The currently selected objects may be dragged by dragging any of their
    selection points.

    First we check if a current_shape is active, if so, all touches are sent to
    it. On touch_up, it checks if done and if so finishes it.

    Next we check if we need to select a shape by the selection points.
    If so, the touch will select or add to selection a shape. If no shape
    is near enough the selection point, the selection will be cleared when the
    touch moves or comes up.

    Finally, if no shape is selected or active, we create a new one on up or
    if the mouse moves.
    '''

    shapes: List['PaintShape'] = ListProperty([])
    """A list of :class:`PaintShape` instances currently added to the painting
    widget.
    """

    selected_shapes: List['PaintShape'] = ListProperty([])
    """A list of :class:`PaintShape` instances currently selected in the
    painting widget.
    """

    current_shape: Optional['PaintShape'] = None
    '''Holds shape currently being edited. Can be a finished shape, e.g. if
    a point is selected.

    Read only.
    '''

    locked: bool = BooleanProperty(False)
    '''It locks all added shapes so they cannot be interacted with.

    Setting it to `True` will finish any shapes being drawn and unselect them.
    '''

    multiselect: bool = BooleanProperty(False)
    """Whether multiple shapes can be selected by holding down control.

    Holding down the control key has the same effect as :attr:`multiselect`
    being True.
    """

    min_touch_dist: float = 10
    """Min distance of a touch to point for it to count as close enough to be
    able to select that point. It's in :func:`kivy.metrics.dp` units.
    """

    long_touch_delay: float = .7
    """Minimum delay after a touch down before a touch up, for the touch to
    be considered a long touch.
    """

    _long_touch_trigger = None

    _ctrl_down = None

    _processing_touch = None

    def __init__(self, **kwargs):
        super(PaintCanvasBehaviorBase, self).__init__(**kwargs)
        self._ctrl_down = set()
        self.fbind('locked', self._handle_locked)

        def set_focus(*largs):
            if not self.focus:
                self.finish_current_shape()
        if hasattr(self, 'focus'):
            self.fbind('focus', set_focus)

    def _handle_locked(self, *largs):
        if not self.locked:
            return
        if self._long_touch_trigger:
            self._long_touch_trigger.cancel()
            self._long_touch_trigger = None

        self.finish_current_shape()
        self.clear_selected_shapes()

    def finish_current_shape(self):
        """Finishes the current shape being drawn and adds it to
        :attr:`shapes`.

        Returns True if there was a unfinished shape that was finished.
        """
        shape = self.current_shape
        if shape:
            if shape.finished:
                self.end_shape_interaction()
            else:
                shape.finish()
                self.current_shape = None

                if shape.is_valid:
                    self.add_shape(shape)
                else:
                    shape.remove_shape_from_canvas()

            return True
        return False

    def start_shape_interaction(self, shape, pos=None):
        """Called by the painter to start interacting with a shape e.g. when
        a touch was close to a point of the shape.

        This adds the shape to :attr:`current_shape`.

        :param shape: The shape to start interacting with.
        :param pos: The mouse pos, if available that caused the interaction.
        """
        assert self.current_shape is None
        self.current_shape = shape
        # shape.start_interaction(pos)

    def end_shape_interaction(self):
        """Called by the painter to end interacting with the
        :attr:`current_shape`.
        """
        shape = self.current_shape
        if shape is not None:
            self.current_shape = None
            shape.stop_interaction()

    def clear_selected_shapes(self):
        """De-selects all currently selected shapes."""
        shapes = self.selected_shapes[:]
        for shape in shapes:
            self.deselect_shape(shape)
        return shapes

    def delete_selected_shapes(self):
        """De-selects and removes all currently selected shapes from
        :attr:`shapes`.

        :return: List of the shapes that were deleted, if any.
        """
        shapes = self.selected_shapes[:]
        self.clear_selected_shapes()
        if self.current_shape is not None:
            shapes.append(self.current_shape)

        for shape in shapes:
            self.remove_shape(shape)
        return shapes

    def delete_all_shapes(self, keep_locked_shapes=True):
        """Removes all currently selected shapes from :attr:`shapes`.

        :param keep_locked_shapes: Whether to also delete the shapes that are
            locked
        :return: List of the shapes that were deleted, if any.
        """
        self.finish_current_shape()
        shapes = self.shapes[:]
        for shape in shapes:
            if not shape.locked or not keep_locked_shapes:
                self.remove_shape(shape)
        return shapes

    def select_shape(self, shape):
        """Selects the shape and adds it to :attr:`selected_shapes`.

        :param shape: :class:`PaintShape` instance to select.
        :return: A bool indicating whether the shape was successfully selected.
        """
        if shape.select():
            self.finish_current_shape()
            self.selected_shapes.append(shape)
            return True
        return False

    def deselect_shape(self, shape):
        """De-selects the shape and removes it from :attr:`selected_shapes`.

        :param shape: :class:`PaintShape` instance to de-select.
        :return: A bool indicating whether the shape was successfully
            de-selected.
        """
        if shape.deselect():
            self.selected_shapes.remove(shape)
            return True
        return False

    def add_shape(self, shape):
        """Add the shape to :attr:`shapes` and to the painter.

        :param shape: :class:`PaintShape` instance to add.
        :return: A bool indicating whether the shape was successfully added.
        """
        self.shapes.append(shape)
        return True

    def remove_shape(self, shape):
        """Removes the shape from the painter and from :attr:`shapes`.

        :param shape: :class:`PaintShape` instance to remove.
        :return: A bool indicating whether the shape was successfully removed.
        """
        self.deselect_shape(shape)

        if shape is self.current_shape:
            self.finish_current_shape()
        shape.remove_shape_from_canvas()

        if shape in self.shapes:
            self.shapes.remove(shape)
            return True
        return False

    def reorder_shape(self, shape, before_shape=None):
        """Move the shape up or down in depth, in terms of the shape order in
        :attr:`shapes` and in the canvas.

        This effect whether a shape will obscure another.

        :param shape: :class:`PaintShape` instance to move from it's current
            position.
        :param before_shape: Where to add it. If `None`, it is moved at the
            end, otherwise it is moved after the given :class:`PaintShape` in
            :attr:`shapes`.
        """
        self.shapes.remove(shape)
        if before_shape is None:
            self.shapes.append(shape)
            shape.move_to_top()
        else:
            i = self.shapes.index(before_shape)
            self.shapes.insert(i, shape)

            for s in self.shapes[i:]:
                s.move_to_top()

    def duplicate_selected_shapes(self):
        """Duplicates all currently :attr:`selected_shapes` and adds them
        to :attr:`shapes`.

        The new shapes are added a slight offset from the original
        shape positions.

        :return: The original :attr:`selected_shapes` that were duplicated.
        """
        shapes = self.selected_shapes[:]
        self.clear_selected_shapes()
        for shape in shapes:
            self.duplicate_shape(shape)
        return shapes

    def duplicate_shape(self, shape):
        """Duplicate the shape and adds it to :attr:`shapes`.

        The new shapes is added at a slight offset from the original
        shape position.

        :param shape: :class:`PaintShape` to duplicate.
        :return: The new :class:`PaintShape` that was created.
        """
        new_shape = copy.deepcopy(shape)
        self.add_shape(new_shape)
        new_shape.translate(dpos=(15, 15))
        return new_shape

    def create_shape_with_touch(self, touch):
        """Called internally whenever the user has done something with a
        touch such that the controller wants to create a new
        :class:`PaintShape` to be added to the painter.

        This should return a new :class:`PaintShape` instance that will be
        added to the painter.

        :param touch: The touch that caused this call.
        :return: A new :class:`PaintShape` instance to be added.
        """
        raise NotImplementedError

    def check_new_shape_done(self, shape, state):
        """Checks whether the shape has been finished drawing. This is how
        the controller decides whether the shape can be considered done and
        moved on from.

        The controller calls this with the :attr:`current_shape` at every touch
        to figure out if the shape is done and ready to be added to
        :attr:`shapes`.

        :param shape: The :class:`PaintShape` to check.
        :param state: The touch state (internal, not sure if this will stay.)
        :return: Whether the touch is completed and fully drawn.
        """
        return not shape.finished and shape.ready_to_finish

    def lock_shape(self, shape):
        """Locks the shape so that it cannot be interacted with by touch.

        :param shape: The :class:`PaintShape` to lock. It should be in
            :attr:`shapes`.
        :return: Whether the shape was successfully locked.
        """
        if shape.locked:
            return False

        res = shape is self.current_shape and self.finish_current_shape()

        if shape.selected:
            res = self.deselect_shape(shape)

        return shape.lock() or res

    def unlock_shape(self, shape):
        """Unlocks the shape so that it can be interacted with again by touch.

        :param shape: The :class:`PaintShape` to unlock. It should be in
            :attr:`shapes`.
        :return: Whether the shape was successfully unlocked.
        """
        if shape.locked:
            return shape.unlock()
        return False

    def get_closest_selection_point_shape(self, x, y):
        """Given a position, it returns the shape whose selection point is the
        closest to this position among all the shapes.

        This is how we find the shape to drag around and select it. Each shape
        has a single selection point by which it can be selected and dragged.
        We find the shape with the closest selection point among all the
        shapes, and that shape is returned.

        :param x: The x pos.
        :param y: The y pos.
        :return: The :class:`PaintShape` that is the closest as described.
        """
        min_dist = dp(self.min_touch_dist)
        closest_shape = None
        for shape in reversed(self.shapes):  # upper shape takes pref
            if shape.locked:
                continue

            dist = shape.get_selection_point_dist((x, y))
            if dist < min_dist:
                closest_shape = shape
                min_dist = dist

        return closest_shape

    def get_closest_shape(self, x, y):
        """Given a position, it returns the shape that has a point on its
        boundary that is the closest to this position, among all the shapes.

        This is how we find the shape on e.g. a long touch when we start
        editing the shape. We find the closest point among all the boundary
        points of all the shapes, and the shape with the closest point is
        returned.

        :param x: The x pos.
        :param y: The y pos.
        :return: The :class:`PaintShape` that is the closest as described.
        """
        min_dist = dp(self.min_touch_dist)
        closest_shape = None
        for shape in reversed(self.shapes):  # upper shape takes pref
            if shape.locked:
                continue

            dist = shape.get_interaction_point_dist((x, y))
            if dist < min_dist:
                closest_shape = shape
                min_dist = dist

        return closest_shape

    def on_touch_down(self, touch):
        ud = touch.ud
        # whether the touch was used by the painter for any purpose whatsoever
        ud['paint_interacted'] = False
        # can be one of current, selected, done indicating how the touch was
        # used, if it was used. done means the touch is done and don't do
        # anything with anymore. selected means a shape was selected.
        ud['paint_interaction'] = ''
        # if this touch experienced a move
        ud['paint_touch_moved'] = False
        # the shape that was selected if paint_interaction is selected
        ud['paint_selected_shape'] = None
        # whether the selected_shapes contained the shape this touch was
        # used to select a shape in touch_down.
        ud['paint_was_selected'] = False
        ud['paint_cleared_selection'] = False

        if self.locked or self._processing_touch is not None:
            return super(PaintCanvasBehaviorBase, self).on_touch_down(touch)

        if super(PaintCanvasBehaviorBase, self).on_touch_down(touch):
            return True
                
        if not self.collide_point(touch.x, touch.y):
            return False

        ud['paint_interacted'] = True
        self._processing_touch = touch
        touch.grab(self)

        # if we have a current shape, all touch will go to it
        current_shape = self.current_shape
        if current_shape is not None:
            ud['paint_cleared_selection'] = current_shape.finished and \
                current_shape.get_interaction_point_dist(touch.pos) \
                >= dp(self.min_touch_dist)
            if ud['paint_cleared_selection']:
                self.finish_current_shape()

            else:
                ud['paint_interaction'] = 'current'
                current_shape.handle_touch_down(touch)
                return True

        # next try to interact by selecting or interacting with selected shapes
        shape = self.get_closest_selection_point_shape(touch.x, touch.y)
        if shape is not None:
            ud['paint_interaction'] = 'selected'
            ud['paint_selected_shape'] = shape
            ud['paint_was_selected'] = shape not in self.selected_shapes
            self._long_touch_trigger = Clock.schedule_once(
                partial(self.do_long_touch, touch), self.long_touch_delay)
            return True

        if self._ctrl_down:
            ud['paint_interaction'] = 'done'
            return True

        self._long_touch_trigger = Clock.schedule_once(
            partial(self.do_long_touch, touch), self.long_touch_delay)
        return True

    def do_long_touch(self, touch, *largs):
        """Handles a long touch by the user.
        """
        assert self._processing_touch
        touch.push()
        touch.apply_transform_2d(self.to_widget)

        self._long_touch_trigger = None
        ud = touch.ud
        if ud['paint_interaction'] == 'selected':
            if self._ctrl_down:
                ud['paint_interaction'] = 'done'
                touch.pop()
                return
            ud['paint_interaction'] = ''

        assert ud['paint_interacted']
        assert not ud['paint_interaction']

        self.clear_selected_shapes()
        shape = self.get_closest_shape(touch.x, touch.y)
        if shape is not None:
            ud['paint_interaction'] = 'current'
            self.start_shape_interaction(shape, (touch.x, touch.y))
        else:
            ud['paint_interaction'] = 'done'
        touch.pop()

    def on_touch_move(self, touch):
        # if touch.grab_current is not None:  ????????
        #     return False

        ud = touch.ud
        if 'paint_interacted' not in ud or not ud['paint_interacted']:
            return super(PaintCanvasBehaviorBase, self).on_touch_move(touch)

        if self._long_touch_trigger is not None:
            self._long_touch_trigger.cancel()
            self._long_touch_trigger = None

        if touch.grab_current is self:
            # for move, only use normal touch, not touch outside range
            return False

        if ud['paint_interaction'] == 'done':
            return True

        ud['paint_touch_moved'] = True
        if not self.collide_point(touch.x, touch.y):
            return True

        if not ud['paint_interaction']:
            if ud['paint_cleared_selection'] or self.clear_selected_shapes():
                ud['paint_interaction'] = 'done'
                return True

            # finally try creating a new shape
            # touch must have originally collided otherwise we wouldn't be here
            shape = self.create_shape_with_touch(touch)
            if shape is not None:
                shape.handle_touch_down(touch, opos=touch.opos)
                self.current_shape = shape
                if self.check_new_shape_done(shape, 'down'):
                    self.finish_current_shape()
                    ud['paint_interaction'] = 'done'
                    return True

                ud['paint_interaction'] = 'current_new'
            else:
                ud['paint_interaction'] = 'done'
                return True

        if ud['paint_interaction'] in ('current', 'current_new'):
            if self.current_shape is None:
                ud['paint_interaction'] = 'done'
            else:
                self.current_shape.handle_touch_move(touch)
            return True

        assert ud['paint_interaction'] == 'selected'

        shape = ud['paint_selected_shape']
        if shape not in self.shapes:
            ud['paint_interaction'] = 'done'
            return True

        if self._ctrl_down or self.multiselect:
            if shape not in self.selected_shapes:
                self.select_shape(shape)
        else:
            if len(self.selected_shapes) != 1 or \
                    self.selected_shapes[0] != shape:
                self.clear_selected_shapes()
                self.select_shape(shape)

        for s in self.selected_shapes:
            s.translate(dpos=(touch.dx, touch.dy))
        return True

    def on_touch_up(self, touch):
        ud = touch.ud
        if 'paint_interacted' not in ud or not ud['paint_interacted']:
            return super(PaintCanvasBehaviorBase, self).on_touch_up(touch)

        if self._long_touch_trigger is not None:
            self._long_touch_trigger.cancel()
            self._long_touch_trigger = None

        touch.ungrab(self)
        # don't process the same touch up again
        paint_interaction = ud['paint_interaction']
        ud['paint_interaction'] = 'done'

        self._processing_touch = None
        if paint_interaction == 'done':
            return True

        if not paint_interaction:
            if ud['paint_cleared_selection'] or self.clear_selected_shapes():
                return True

            # finally try creating a new shape
            # touch must have originally collided otherwise we wouldn't be here
            shape = self.create_shape_with_touch(touch)
            if shape is not None:
                shape.handle_touch_down(touch, opos=touch.opos)
                self.current_shape = shape
                if self.check_new_shape_done(shape, 'down'):
                    self.finish_current_shape()
                    return True

                paint_interaction = 'current_new'
            else:
                return True

        if paint_interaction in ('current', 'current_new'):
            if self.current_shape is not None:
                self.current_shape.handle_touch_up(
                    touch, outside=not self.collide_point(touch.x, touch.y))
                if self.check_new_shape_done(self.current_shape, 'up'):
                    self.finish_current_shape()
            return True

        if not self.collide_point(touch.x, touch.y):
            return True

        assert paint_interaction == 'selected'
        if ud['paint_touch_moved']:
            # moving normally doesn't change the selection state

            # this is a quick selection mode where someone dragged a object but
            # nothing was selected so don't keep the object that was dragged
            # selected
            if ud['paint_was_selected'] and \
                    len(self.selected_shapes) == 1 and \
                    self.selected_shapes[0] == ud['paint_selected_shape']:
                self.clear_selected_shapes()
            return True

        shape = ud['paint_selected_shape']
        if shape not in self.shapes:
            return True

        if self._ctrl_down or self.multiselect:
            if not ud['paint_was_selected'] and shape in self.selected_shapes:
                self.deselect_shape(shape)
            elif ud['paint_was_selected']:
                self.select_shape(shape)
        else:
            if len(self.selected_shapes) != 1 or \
                    self.selected_shapes[0] != shape:
                self.clear_selected_shapes()
                self.select_shape(shape)

        return True

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] in ('lctrl', 'ctrl', 'rctrl'):
            self._ctrl_down.add(keycode[1])

        arrows = {
            'left': (-1, 0), 'right': (1, 0), 'up': (0, 1), 'down': (0, -1)}
        if keycode[1] in arrows and self.selected_shapes:
            dpos = arrows[keycode[1]]
            for shape in self.selected_shapes:
                shape.translate(dpos=dpos)
            return True

        return False

    def keyboard_on_key_up(self, window, keycode):
        if keycode[1] in ('lctrl', 'ctrl', 'rctrl'):
            self._ctrl_down.remove(keycode[1])

        if keycode[1] == 'escape':
            if self.finish_current_shape() or self.clear_selected_shapes():
                return True
        elif keycode[1] == 'delete':
            if self.delete_selected_shapes():
                return True
        elif keycode[1] == 'a' and self._ctrl_down:
            for shape in self.shapes:
                if not shape.locked:
                    self.select_shape(shape)
            return True
        elif keycode[1] == 'd' and self._ctrl_down:
            if self.duplicate_selected_shapes():
                return True

        return False

class PaintShape(EventDispatcher):
    """Base class for shapes used by :attr:`PaintCanvasBehavior` when creating
    new shapes when drawing.

    All the data that configures a shape can be gotten by calling
    :meth:`get_state`. The shape can then be re-created by creating the shape
    and calling :meth:`set_state`.

    For example:

    .. code-block:: python

        shape = PaintCircle(...)
        state = shape.get_state()
        my_yaml.save_config(filename, state)

        # then later
        state = my_yaml.load_file(filename)
        shape = PaintCircle()
        shape.set_state(state)
        shape.set_valid()
        shape.finish()
        if not shape.is_valid:
            raise ValueError(
                'Shape {} is not valid and cannot be added'.format(shape))
        painter.add_shape(shape)

    A shape can also be copied more directly with
    :meth:`PaintCanvasBehaviorBase.duplicate_shape`. Or manually with e.g.:

    .. code-block:: python

        import copy
        shape = PaintCircle(...)
        new_shape = copy.deepcopy(shape)
        painter.add_shape(new_shape)
        new_shape.translate(dpos=(15, 15))

    :Events:

        on_update:
            Dispatched whenever the shape is changed in any way, e.g.
            translated etc. This is only dispatched once the shape is finished.
    """

    line_width = NumericProperty('1dp')
    """The line width of lines shown, in :func:`~kivy.metrics.dp`.
    """

    pointsize = NumericProperty('0.01dp')
    """The point size of points shown, in :func:`~kivy.metrics.dp`.
    """

    line_color = 0, 1, 0, 1
    """The line color of lines and/or points shown.
    """

    selection_point_color = 1, .5, .31, 1
    """The color of the point by which the shape is selected/dragged.
    """

    line_color_locked = .4, .56, .36, 1
    """The line color of lines and/or points shown when the shape is
    :attr:`locked`.
    """

    selected = False
    """Whether the shape is currently selected in
    :attr:`~PaintCanvasBehaviorBase.selected_shapes`. See :meth:`select`.

    Read only. Call :meth:`PaintCanvasBehaviorBase.select_shape` to change.
    """

    locked = BooleanProperty(False)
    """Whether the shape is currently locked and
    :class:`PaintCanvasBehaviorBase` won't interact with it. See :meth:`lock`.

    Read only. Call :meth:`PaintCanvasBehaviorBase.lock_shape` to change.
    """

    finished = False
    """Whether the shape has been finished drawing. See :meth:`finish`.

    Read only.
    """

    interacting = False
    """Whether :class:`PaintCanvasBehavior` is currently interacting with this
    shape e.g. in :attr:`PaintCanvasBehavior.current_shape`. See
    :meth:`start_interaction`.

    Read only.
    """

    ready_to_finish = False
    """Whether the shape is ready to be finished. Used by
    :class:`PaintCanvasBehavior` to decide whether to finish the shape.
    See :meth:`finish`.

    Read only.
    """

    is_valid = False
    """Whether the shape is in a valid state. If :meth:`finish` when not in a
    valid state, :class:`PaintCanvasBehavior` will not keep the shape.

    Read only.
    """

    paint_widget = None
    """When the shape is added to a widget with :meth:`add_shape_to_canvas`,
    it is the widget to which it is added.

    Read only.
    """

    graphics_name = ''
    """The group name given to all the canvas instructions added to the
    :attr:`instruction_group`. These are the lines, points etc.

    Read only and is automatically set when the shape is created.
    """

    instruction_group = None
    """A :class:`~kivy.graphics.InstructionGroup` instance to which all the
    canvas instructions that the shape displays is added to.

    This is added to the host :attr:`paint_widget` by
    :meth:`add_shape_to_canvas`.

    Read only.
    """

    color_instructions = []
    """A list of all the color instructions used to color the shapes.

    Read only.
    """

    __events__ = ('on_update', )

    def __init__(
            self, line_color=(0, 0, 0, 0.65),
            line_color_locked=(.4, .56, .36, 1),
            selection_point_color=(62/255, 254/255, 1,1), **kwargs):
        self.graphics_name = '{}-{}'.format(self.__class__.__name__, id(self))

        super(PaintShape, self).__init__(**kwargs)
        self.line_color = line_color
        self.line_color_locked = line_color_locked
        self.selection_point_color = selection_point_color
        self.color_instructions = []

        self.fbind('line_width', self._update_from_line_width)
        self.fbind('pointsize', self._update_from_pointsize)

    def _update_from_line_width(self, *args):
        pass

    def _update_from_pointsize(self, *args):
        pass

    def on_update(self, *largs):
        pass

    def set_valid(self):
        """Called internally after the shape potentially
        :attr:`is_valid`, to set :attr:`is_valid` in case the shape is now
        valid.

        This needs to be called after a shape is constructed manually before it
        is added with :meth:`PaintCanvasBehaviorBase.add_shape`. See
        :class:`PaintCanvasBehavior` for an example.
        """
        pass

    def add_shape_to_canvas(self, paint_widget):
        """Must be called on the shape to add it to the canvas on which the
        shape should be displayed when it's being drawn.

        If this is never called, the shape won't ever be shown visually.

        A typical pattern of how this is used is:

        .. code-block:: python

            class PainterWidget(PaintCanvasBehavior, Widget):
                def add_shape(self, shape):
                    if super(PainterWidget, self).add_shape(shape):
                        shape.add_shape_to_canvas(self)
                        return True
                    return False

        :param paint_widget: A :class:`~kivy.uix.widget.Widget` to who's canvas
            the graphics instructions displaying the shapes will be added.
        :return: True if it was added, otherwise False e.g. if it has
            previously already been added.
        """
        if self.instruction_group is not None:
            return False

        self.paint_widget = paint_widget
        with paint_widget.canvas:
            self.instruction_group = InstructionGroup()
        return True

    def remove_shape_from_canvas(self):
        """Must be called on the shape to remove it from the canvas to which
        it has previously been added with :meth:`add_shape_to_canvas`.

        If this is never called, the shape won't be removed and will remain
        visible.

        A typical pattern of how this is used is:

        .. code-block:: python

            class PainterWidget(PaintCanvasBehavior, Widget):
                def remove_shape(self, shape):
                    if super(PainterWidget, self).remove_shape(shape):
                        shape.remove_shape_from_canvas()
                        return True
                    return False

        :return: :attr:`paint_widget` to which the shapes has previously been
            added, if it was added previously, otherwise None.
        """
        if self.instruction_group is None:
            return None

        paint_widget = self.paint_widget
        paint_widget.canvas.remove(self.instruction_group)
        self.instruction_group = None
        self.paint_widget = None
        return paint_widget

    def handle_touch_down(self, touch, opos=None):
        """(internal) called by :class:`PaintCanvasBehaviorBase` to handle
        a touch down that is relevant to this shape.

        :param touch: The kivy touch.
        :param opos: The original starting position of the touch e.g.
            ``touch.opos`` if the touch has moved before this was called.
        """
        raise NotImplementedError

    def handle_touch_move(self, touch):
        """(internal) called by :class:`PaintCanvasBehaviorBase` to handle
        a touch move that is relevant to this shape.

        :param touch: The kivy touch.
        """
        # if ready to finish, it needs to ignore until touch is up
        raise NotImplementedError

    def handle_touch_up(self, touch, outside=False):
        """(internal) called by :class:`PaintCanvasBehaviorBase` to handle
        a touch up that is relevant to this shape.

        :param touch: The kivy touch.
        :param outside: Whether the touch falls outside the
            :class:`PaintCanvasBehaviorBase`.
        """
        raise NotImplementedError

    def start_interaction(self, pos):
        """(internal) called by
        :meth:`PaintCanvasBehaviorBase.start_shape_interaction` when it wants
        to start interacting with a shape, e.g. if there was a long touch
        near the shape.

        :param pos: The position of the touch that caused this interaction.
        :return: Whether we started :attr:`interacting`. False if e.g.
            it was already :attr:`interacting`.
        """
        if self.interacting:
            return False
        self.interacting = True
        return True

    def stop_interaction(self):
        """(internal) called by
        :meth:`PaintCanvasBehaviorBase.end_shape_interaction` when it wants
        to stop interacting with a shape.

        :return: Whether we ended :attr:`interacting`. False if e.g.
            we were not already :attr:`interacting`.
        """
        if not self.interacting:
            return False
        self.interacting = False
        return True

    def get_selection_point_dist(self, pos):
        """Returns the minimum of the distance to a selection point that we can
        interact with. Selections points is the differently colored point
        (orange) by which the shape can be dragged or selected etc.

        :param pos: The position to which to compute the min point distance.
        :return: The minimum distance to pos, or a very large number if
            there's no selection point available.
        """
        raise NotImplementedError

    def get_interaction_point_dist(self, pos):
        """Returns the minimum of the distance to any point in the shape that
        we can interact with. These are all the points that can be manipulated
        e.g. to change the shape size or orientation etc.

        :param pos: The position to which to compute the min point distance.
        :return: The minimum distance to pos, or a very large number if
            there's no interaction points available.
        """
        raise NotImplementedError

    def finish(self):
        """Called by
        :meth:`PaintCanvasBehaviorBase.finish_current_shape` when it wants
        to finish the shape and possibly add it to the
        :attr:`PaintCanvasBehaviorBase.shapes`.

        This needs to be called after a shape is constructed manually before it
        is added with :meth:`PaintCanvasBehaviorBase.add_shape`. See
        :class:`PaintCanvasBehavior` for an example.

        :return: True if we just :attr:`finished` the shape, otherwise False
            if it was already :attr:`finished`.
        """
        if self.finished:
            return False
        self.finished = True
        return True

    def select(self):
        """(internal) Called by
        :meth:`PaintCanvasBehaviorBase.select_shape` to select the shape.

        Don't call this directly.

        :return: True if we just :attr:`selected` the shape, otherwise False
            if it was already :attr:`selected`.
        """
        if self.selected:
            return False
        self.selected = True
        return True

    def deselect(self):
        """(internal) Called by
        :meth:`PaintCanvasBehaviorBase.deselect_shape` to de-select the shape.

        Don't call this directly.

        :return: True if we just de- :attr:`selected` the shape, otherwise
            False if it was already de- :attr:`selected`.
        """
        if not self.selected:
            return False
        self.selected = False
        return True

    def lock(self):
        """(internal) Called by
        :meth:`PaintCanvasBehaviorBase.lock_shape` to lock the shape.

        Don't call this directly.

        :return: True if we just :attr:`locked` the shape, otherwise False
            if it was already :attr:`locked`.
        """
        if self.locked:
            return False

        self.locked = True
        return True

    def unlock(self):
        """(internal) Called by
        :meth:`PaintCanvasBehaviorBase.unlock_shape` to unlock the shape.

        Don't call this directly.

        :return: True if we just un :attr:`locked` the shape, otherwise
            False if it was already un :attr:`locked`.
        """
        if not self.locked:
            return False

        self.locked = False
        return True

    def translate(self, dpos=None, pos=None):
        """Translates the shape by ``dpos`` or to be at ``pos``.

        This should only be called

        :param dpos: The change in x, y by which to translate the shape, if not
            None.
        :param pos: The final position to which to set the shape, if not None.
        :return: Whether the shape was successfully translated.
        """
        raise NotImplementedError

    def move_to_top(self):
        """(internal) Called by
        :meth:`PaintCanvasBehaviorBase.reorder_shape` to move the shape to the
        top of the canvas.

        Don't call this directly.

        :return: True if we were able to move it up..
        """
        if self.instruction_group is None:
            return

        self.paint_widget.canvas.remove(self.instruction_group)
        self.paint_widget.canvas.add(self.instruction_group)
        return True

    @classmethod
    def create_shape(cls, **inst_kwargs):
        """Creates a new shape instance of this class from the given arguments.

        See each subclass for the shape arguments.

        E.g.:

        .. code-block:: python

            shape = PaintPolygon.create_shape(
                [0, 0, 300, 0, 300, 800, 0, 800], [0, 0])

        :param inst_kwargs: Configuration options for the new shape that
            will be passed as options to the class when it is instantiated.
        :return: The newly created shape instance.
        """
        raise NotImplementedError

    @classmethod
    def create_shape_from_state(cls, state):
        """Recreates a shape of this class using the ``state``.

        :param state: the state dict as returned by :meth:`get_state`.
        :return: The newly created shape instance.
        """
        shape = cls()
        shape.set_state(state)
        shape.set_valid()
        shape.finish()
        if not shape.is_valid:
            raise ValueError('Shape {} is not valid'.format(shape))

        return shape

    def get_state(self, state=None):
        """Returns a configuration dictionary that can be used to duplicate
        the shape with all the configuration values of the shape. See
        :class:`PaintShape`.

        :param state: A dict, or None. If not None, the config data will be
            added to the dict, otherwise a new dict is created and returned.
        :return: A dict with all the config data of the shape.
        """
        d = {} if state is None else state
        for k in ['line_color', 'line_width', 'is_valid', 'locked',
                  'line_color_locked']:
            d[k] = getattr(self, k)
        d['cls'] = self.__class__.__name__

        return d

    def set_state(self, state):
        """Takes a configuration dictionary and applies it to the shape. See
        :class:`PaintShape` and :meth:`get_state`.

        :param state: A dict with shape specific configuration values.
        """
        state = dict(state)
        lock = None
        for k, v in state.items():
            if k == 'locked':
                lock = bool(v)
                continue
            elif k == 'cls':
                continue
            setattr(self, k, v)

        self.finish()

        if lock is True:
            self.lock()
        elif lock is False:
            self.unlock()
        self.dispatch('on_update')

    def __deepcopy__(self, memo):
        obj = self.__class__()
        obj.set_state(self.get_state())

        obj.set_valid()
        obj.finish()
        return obj

    def add_area_graphics_to_canvas(self, name, canvas):
        """Add graphics instructions to ``canvas`` such that the inside area
        of the shapes will be colored in with the color instruction
        below it in the canvas.

        See the examples how to use it.

        :param name: The group name given to the graphics instructions when
            they are added to the canvas. This is how the canvas can remove
            them all at once.
        :param canvas: The canvas to which to add the instructions.
        """
        raise NotImplementedError

    def show_shape_in_canvas(self):
        """Shows the shape in the widget's canvas. Call this after
        :meth:`hide_shape_in_canvas` to display the shape again.
        """
        for color in self.color_instructions:
            color.rgba = [color.r, color.g, color.b, 1.]

    def hide_shape_in_canvas(self):
        """Hides the shape so that it is not visible in the widget to which it
        was added with :meth:`add_shape_to_canvas`.
        """
        for color in self.color_instructions:
            color.rgba = [color.r, color.g, color.b, 0.]

    def rescale(self, scale):
        """Rescales the all the perimeter points/lines distance from the center
        of the shape by the fractional amount ``scale``.

        E.g. if a point on the perimeter is at distance ``X`` from the center
        of the shape, after this function it'll be at distance ``scale * X``
        from the center of the shape.

        :param scale: amount by which to scale
        """
        raise NotImplementedError

class PaintEllipse(PaintShape):
    """A shape that represents an ellipse.

    The shape has a single point by which it can be dragged or the radius
    expanded.
    """
    pointsize = NumericProperty('7dp')

    center = ListProperty([0, 0])
    """A 2-tuple containing the center position of the ellipse.

    This can be set, and the shape will translate itself to the new center pos.

    This is read only while a user is interacting with the shape with touch,
    or if the shape is not :attr:`finished`.
    """

    radius_x = NumericProperty('10dp')
    """The x-radius of the circle.

    This can be set, and the shape will resize itself to the new size.

    This is read only while a user is interacting with the shape with touch,
    or if the shape is not :attr:`finished`.
    """

    radius_y = NumericProperty('15dp')
    """The y-radius of the circle.

    This can be set, and the shape will resize itself to the new size.

    This is read only while a user is interacting with the shape with touch,
    or if the shape is not :attr:`finished`.
    """

    angle = NumericProperty(0)
    '''The angle in radians by which the x-axis is rotated counter clockwise.
    This allows the ellipse to be rotated rather than just be aligned to the
    default axes.

    This can be set, and the shape will reorient itself to the new size.

    This is read only while a user is interacting with the shape with touch,
    or if the shape is not :attr:`finished`.
    '''

    perim_ellipse_inst = None
    """(internal) The graphics instruction representing the perimeter.
    """

    ellipse_color_inst = None
    """(internal) The color instruction coloring the perimeter.
    """

    selection_point_inst = None
    """(internal) The graphics instruction representing the selection point
    on the first axis.
    """

    selection_point_inst2 = None
    """(internal) The graphics instruction representing the second selection
    point for the second axis.
    """

    rotate_inst = None
    """(internal) The graphics instruction that rotates the ellipse.
    """

    ready_to_finish = True

    is_valid = True
    
    during_creation = False

    def __init__(self, **kwargs):
        super(PaintEllipse, self).__init__(**kwargs)

        def update(*largs):
            self.translate()
        self.fbind('radius_x', update)
        self.fbind('radius_y', update)
        self.fbind('angle', update)
        self.fbind('center', update)

    @classmethod
    def create_shape(
            cls, center=(0, 0), radius_x=dp(10), radius_y=dp(15), angle=0,
            **inst_kwargs):
        """Creates a new ellipse instance from the given arguments.

        E.g.:

        .. code-block:: python

            shape = PaintEllipse.create_shape([0, 0], 5, 10, 0)

        :param center: The :attr:`center` of the ellipse.
        :param radius_x: The :attr:`radius_x` of the ellipse.
        :param radius_y: The :attr:`radius_y` of the ellipse.
        :param angle: The :attr:`angle` of the ellipse in radians.
        :param inst_kwargs: Configuration options for the new shape that
            will be passed as options to the class when it is instantiated.
        :return: The newly created ellipse instance.
        """
        shape = cls(
            center=center, radius_x=radius_x, radius_y=radius_y, angle=angle,
            **inst_kwargs)
        shape.set_valid()
        shape.finish()
        if not shape.is_valid:
            raise ValueError(
                'Shape {} is not valid'.format(shape))
        return shape

    def add_area_graphics_to_canvas(self, name, canvas):
        with canvas:
            x, y = self.center
            rx, ry = self.radius_x, self.radius_y
            angle = self.angle
            
            PushMatrix(group=name)
            Rotate(angle=angle / pi * 180., origin=(x, y), group=name)
            Ellipse(size=(rx * 2., ry * 2.), pos=(x - rx, y - ry), group=name)
            PopMatrix(group=name)

    def add_shape_to_canvas(self, paint_widget):
        if not super(PaintEllipse, self).add_shape_to_canvas(paint_widget):
            return False

        colors = self.color_instructions = []
        
        x, y = self.center
        rx, ry = self.radius_x, self.radius_y
        angle = self.angle

        i1 = self.ellipse_color_inst = Color(
            *self.line_color, group=self.graphics_name)
        colors.append(i1)

        i2 = PushMatrix(group=self.graphics_name)
        i3 = self.rotate_inst = Rotate(
            angle=angle / pi * 180., origin=(x, y), group=self.graphics_name)

        i4 = self.perim_ellipse_inst = Line(
            ellipse=(x - rx, y - ry, 2 * rx, 2 * ry),
            width=self.line_width, group=self.graphics_name)
        
        i66 = self.perim_color_inst2 = Color(
            *self.selection_point_color, group=self.graphics_name)
        colors.append(i66)
        
        i6 = self.selection_point_inst2 = Point(
            points=[x, y + ry], pointsize=self.pointsize,
            group=self.graphics_name)
        i8 = Color(*self.selection_point_color, group=self.graphics_name)
        colors.append(i8)

        i5 = self.selection_point_inst = Point(
            points=[x + rx, y], pointsize=self.pointsize,
            group=self.graphics_name)
        i7 = PopMatrix(group=self.graphics_name)

        for inst in (i1, i2, i3, i4, i66, i6, i8, i5, i7):
            self.instruction_group.add(inst)
        return True

    def remove_shape_from_canvas(self):
        if super(PaintEllipse, self).remove_shape_from_canvas():
            self.ellipse_color_inst = None
            self.perim_ellipse_inst = None
            self.selection_point_inst = None
            self.selection_point_inst2 = None
            self.rotate_inst = None
            return True
        return False

    def _update_from_line_width(self, *args):
        super()._update_from_line_width()
        if self.perim_ellipse_inst is not None:
            # w = 2 if self.selected else 1
            w=1
            self.perim_ellipse_inst.width = w * self.line_width

    def _update_from_pointsize(self, *args):
        super()._update_from_pointsize()
        if self.selection_point_inst is not None:
            # w = 2 if self.interacting else 1
            w=1
            self.selection_point_inst.pointsize = w * self.pointsize
            self.selection_point_inst2.pointsize = w * self.pointsize

    def handle_touch_down(self, touch, opos=None):
        if not self.finished:
            self.center = opos or tuple(touch.pos)

    def handle_touch_move(self, touch):
        if not self.finished:
            return
        if self.interacting:
            dp2 = dp(2)
            px, py = touch.ppos
            x, y = touch.pos
            cx, cy = self.center

            px, py = px - cx, py - cy
            x, y = x - cx, y - cy

            d1, d2 = self._get_interaction_points_dist(touch.pos)
            if d1 <= d2:
                angle = self.angle
            else:
                angle = self.angle + pi / 2.0

            rrx, rry = cos(angle), sin(angle)
            prev_r = px * rrx + py * rry
            r = x * rrx + y * rry
            if r <= dp2 or prev_r <= dp2:
                return

            prev_theta = atan2(py, px)
            theta = atan2(y, x)
            self.angle = (self.angle + theta - prev_theta) % (2 * pi)
            if d1 <= d2:
                self.radius_x = max(self.radius_x + r - prev_r, dp2)
                if self.during_creation:
                    self.radius_y = max(self.radius_y + r - prev_r, dp2)
            else:
                self.radius_y = max(self.radius_y + r - prev_r, dp2)
                if self.during_creation:

                    self.radius_x = max(self.radius_x + r - prev_r, dp2)

    def handle_touch_up(self, touch, outside=False):
        if not self.finished:
            return

    def start_interaction(self, pos):
        if super(PaintEllipse, self).start_interaction(pos):
            if self.selection_point_inst is not None:
                self.selection_point_inst.pointsize = self.pointsize
                self.selection_point_inst2.pointsize = self.pointsize
            return True
        return False

    def stop_interaction(self):
        if super(PaintEllipse, self).stop_interaction():
            if self.selection_point_inst is not None:
                self.selection_point_inst.pointsize = self.pointsize
                self.selection_point_inst2.pointsize = self.pointsize
            return True
        return False

    def get_selection_point_dist(self, pos):
        x1, y1 = pos

        x2, y2 = self.center
        x2, y2 = _rotate_pos(x2 + self.radius_x, y2, x2, y2, self.angle)
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def get_interaction_point_dist(self, pos):
        d1, d2 = self._get_interaction_points_dist(pos)
        return min(d1, d2)

    def _get_interaction_points_dist(self, pos):
        x1, y1 = pos

        x2, y2 = self.center
        x_, y_ = _rotate_pos(x2 + self.radius_x, y2, x2, y2, self.angle)
        d1 = ((x1 - x_) ** 2 + (y1 - y_) ** 2) ** 0.5

        x_, y_ = _rotate_pos(
            x2, y2 + self.radius_y, x2, y2, self.angle, base_angle=pi / 2.0)
        d2 = ((x1 - x_) ** 2 + (y1 - y_) ** 2) ** 0.5
        return d1, d2

    def lock(self):
        if super(PaintEllipse, self).lock():
            if self.instruction_group is not None:
                self.ellipse_color_inst.rgb = self.line_color_locked[:3]
            return True
        return False

    def unlock(self):
        if super(PaintEllipse, self).unlock():
            if self.instruction_group is not None:
                self.ellipse_color_inst.rgb = self.line_color[:3]
            return True
        return False

    def select(self):
        if not super(PaintEllipse, self).select():
            return False
        if self.instruction_group is not None:
            self.perim_ellipse_inst.width = 2 * self.line_width
        return True

    def deselect(self):
        if super(PaintEllipse, self).deselect():
            if self.instruction_group is not None:
                self.perim_ellipse_inst.width = self.line_width
            return True
        return False

    def translate(self, dpos=None, pos=None):
        if dpos is not None:
            x, y = self.center
            dx, dy = dpos
            x += dx
            y += dy
        elif pos is not None:
            x, y = pos
        else:
            x, y = self.center

        rx, ry = self.radius_x, self.radius_y
        angle = self.angle
        self.center = x, y
        if self.rotate_inst is not None:
            self.rotate_inst.angle = angle / pi * 180.
            self.rotate_inst.origin = x, y
            self.perim_ellipse_inst.ellipse = x - rx, y - ry, 2 * rx, 2 * ry
            self.selection_point_inst.points = [x + rx, y]
            self.selection_point_inst2.points = [x, y + ry]

        self.dispatch('on_update')
        return True

    def get_state(self, state=None):
        d = super(PaintEllipse, self).get_state(state)
        for k in ['center', 'radius_x', 'radius_y', 'angle']:
            d[k] = getattr(self, k)
        return d

    def rescale(self, scale):
        self.radius_x *= scale
        self.radius_y *= scale

    def get_widget_verts(self):
        cx, cy = self.center
        x0,y0 = self._get_coord_from_angle(self.selection_point_inst.points)
        x1,y1 = self._get_coord_from_angle(self.selection_point_inst2.points,base_angle = pi / 2.)
        
        return np.array([[cx,cy],
                         [x0,y0],
                         [x1,y1]])
 
    def _get_coord_from_angle(self,pos,base_angle=0.):
        x1, y1 = pos

        x2, y2 = self.center
        x, y = _rotate_pos(x1, y1, x2, y2, self.angle, base_angle=base_angle)
        return x,y
    
    def get_min_max(self):
        """
        Calculates the min/max x and y coordinates for a rotated ellipse.
        
        Args:
            None
            
        Returns:
            dict: A dictionary containing min_x, max_x, min_y, max_y.
        """
        cx, cy = self.center
        a = self.radius_x  # semi-major axis
        b = self.radius_y  # semi-minor axis
        theta = self.angle  # convert angle to radians
        
        # Parametric equations for the ellipse
        t = np.linspace(0, 2 * pi, 1000)  # Parameter t from 0 to 2*pi
    
        # Parametric points on the unrotated ellipse
        x_ellipse = a * np.cos(t)
        y_ellipse = b * np.sin(t)
        
        # Rotation matrix applied to the points
        x_rotated = x_ellipse * cos(theta) - y_ellipse * sin(theta)
        y_rotated = x_ellipse * sin(theta) + y_ellipse * cos(theta)
        
        # Translating the rotated points to the ellipse's center
        x_final = cx + x_rotated
        y_final = cy + y_rotated
        
        # Finding the min and max values of x and y
        min_x = np.min(x_final)
        max_x = np.max(x_final)
        min_y = np.min(y_final)
        max_y = np.max(y_final)
        
        return min_x, max_x, min_y, max_y       
        

class PaintPolygon(PaintShape):
    """A shape that represents a polygon.

    Points are added to the shape one touch down at a time and to finish the
    shape, one double clicks.

    The shape has a single point by which it can be dragged. All the points
    that make up the polygon, however, can be edited once the shape is
    selected.
    """

    points = ListProperty([])
    """A list of points (x1, y1, x2, y2, ...) that make up the perimeter of the
    polygon.

    There must be at least 3 points for the shape to be :attr:`is_valid`.
    The shape auto-closes so the last point doesn't have to be the same as the
    first.

    This can be set, and the shape will properly update. However, if changed
    manually, :attr:`selection_point` should also be changed to have a
    corresponding point in :attr:`points`.

    This is read only while a user is interacting with the shape with touch,
    or if the shape is not :attr:`finished`.
    """

    selection_point = ListProperty([])
    """A 2-tuple indicating the position of the selection point.

    This can be set, and the shape will properly update. However, if changed
    manually, :attr:`points` should contain a corresponding point at this pos
    by which it is selected.

    This is read only while a user is interacting with the shape with touch,
    or if the shape is not :attr:`finished`.
    """

    perim_line_inst = None
    """(internal) The graphics instruction representing the perimeter.
    """

    perim_points_inst = None
    """(internal) The graphics instruction representing the perimeter points.
    """

    perim_color_inst = None
    """(internal) The color instruction coloring the perimeter.
    """
    perim_color_inst2 = None

    selection_point_inst = None
    """(internal) The graphics instruction representing the selection point.
    """

    perim_close_inst = None
    """(internal) The graphics instruction representing the closing of
    the perimeter.
    """

    ready_to_finish = False

    is_valid = False

    _last_point_moved = None
    """The index in :attr:`points` of the last perimeter point that was being
    dragged and changed by touch. This is how we have continuity when dragging
    a point.
    """

    def __init__(self, **kwargs):
        super(PaintPolygon, self).__init__(**kwargs)

        def update(*largs):
            if self.perim_line_inst is not None:
                self.perim_line_inst.points = self.points
                self.perim_points_inst.points = self.points
                self.selection_point_inst.points = self.selection_point
            self.dispatch('on_update')

        self.fbind('points', update)
        self.fbind('selection_point', update)
        update()

    @classmethod
    def create_shape(cls, points=(), selection_point=(), **inst_kwargs):
        """Creates a new polygon instance from the given arguments.

        E.g.:

        .. code-block:: python

            shape = PaintPolygon.create_shape(
                [0, 0, 300, 0, 300, 800, 0, 800], [0, 0])

        :param points: The list of :attr:`points` of the polygon.
        :param selection_point: The :attr:`selection_point` of the polygon.
        :param inst_kwargs: Configuration options for the new shape that
            will be passed as options to the class when it is instantiated.
        :return: The newly created polygon instance.
        """
        if not selection_point:
            selection_point = points[:2]

        shape = cls(
            points=points, selection_point=selection_point, **inst_kwargs)
        shape.set_valid()
        shape.finish()
        if not shape.is_valid:
            raise ValueError(
                'Shape {} is not valid'.format(shape))
        return shape

    def add_area_graphics_to_canvas(self, name, canvas):
        with canvas:
            points = self.points
            if not points:
                return

            tess = Tesselator()
            tess.add_contour(points)

            if tess.tesselate():
                for vertices, indices in tess.meshes:
                    Mesh(
                        vertices=vertices, indices=indices,
                        mode='triangle_fan', group=name)

    def add_shape_to_canvas(self, paint_widget):
        if not super(PaintPolygon, self).add_shape_to_canvas(paint_widget):
            return False

        colors = self.color_instructions = []

        i1 = self.perim_color_inst = Color(
            *self.line_color, group=self.graphics_name)
        colors.append(i1)

        i2 = self.perim_line_inst = Line(
            points=self.points, width=self.line_width,
            close=self.finished, group=self.graphics_name)
        
        i33 = self.perim_color_inst2 = Color(
            *self.selection_point_color, group=self.graphics_name)
        colors.append(i33)
        
        i3 = self.perim_points_inst = Point(
            points=self.points, pointsize=self.pointsize,
            group=self.graphics_name)

        insts = [i1, i2,i33, i3]
        if not self.finished:
            points = self.points[-2:] + self.points[:2]
            line = self.perim_close_inst = Line(
                points=points, width=self.line_width,
                close=False, group=self.graphics_name)
            line.dash_offset = 4
            line.dash_length = 4
            insts.append(line)

        i4 = Color(*self.selection_point_color, group=self.graphics_name)
        colors.append(i4)

        i5 = self.selection_point_inst = Point(
            points=self.selection_point, pointsize=self.pointsize,
            group=self.graphics_name)

        for inst in insts + [i4, i5]:
            self.instruction_group.add(inst)

        return True

    def remove_shape_from_canvas(self):
        if super(PaintPolygon, self).remove_shape_from_canvas():
            self.perim_color_inst = None
            self.perim_points_inst = None
            self.perim_line_inst = None
            self.selection_point_inst = None
            self.perim_close_inst = None
            return True
        return False

    def _update_from_line_width(self, *args):
        super()._update_from_line_width()
        w = 2 if self.selected else 1
        w=1
        if self.perim_line_inst is not None:
            self.perim_line_inst.width = w * self.line_width
        if self.perim_close_inst is not None:
            self.perim_close_inst.width = w * self.line_width

    def _update_from_pointsize(self, *args):
        super()._update_from_pointsize()
        if self.perim_points_inst is not None:
            w = 2 if self.interacting else 1
            self.perim_points_inst.pointsize = w * self.pointsize
            self.selection_point_inst.pointsize = w * self.pointsize

    def set_valid(self):
        self.is_valid = len(self.points) >= 6

    def handle_touch_down(self, touch, opos=None):
        return

    def handle_touch_move(self, touch):
        if not self.finished:
            return

        i = self._last_point_moved
        if i is None:
            i, dist = self._get_interaction_point(touch.pos)
            if dist is None:
                return
            self._last_point_moved = i

        x, y = self.points[2 * i: 2 * i + 2]
        x += touch.dx
        y += touch.dy
        self.points[2 * i: 2 * i + 2] = x, y
        if not i:
            self.selection_point = [x, y]

    def handle_touch_up(self, touch, outside=False):
        if not self.finished:
            if touch.is_double_tap:
                self.ready_to_finish = True
                return

            if not outside:
                if not self.selection_point:
                    self.selection_point = touch.pos[:]
                self.points.extend(touch.pos)
                if self.perim_close_inst is not None:
                    self.perim_close_inst.points = \
                        self.points[-2:] + self.points[:2]
                if len(self.points) >= 6:
                    self.is_valid = True
        else:
            self._last_point_moved = None

    def start_interaction(self, pos):
        if super(PaintPolygon, self).start_interaction(pos):
            if self.selection_point_inst is not None:
                self.selection_point_inst.pointsize = 2* self.pointsize
                self.perim_points_inst.pointsize = 2*self.pointsize
            return True
        return False

    def stop_interaction(self):
        if super(PaintPolygon, self).stop_interaction():
            if self.selection_point_inst is not None:
                self.selection_point_inst.pointsize = self.pointsize
                self.perim_points_inst.pointsize = self.pointsize
            return True
        return False

    def get_selection_point_dist(self, pos):
        x1, y1 = pos
        # if not self.selection_point:
        #     return 10000.0

        x2, y2 = self.selection_point
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def get_interaction_point_dist(self, pos):
        i, dist = self._get_interaction_point(pos)
        if dist is None:
            return 10000.0
        return dist

    def _get_interaction_point(self, pos):
        x1, y1 = pos
        points = self.points
        if not points:
            return None, None

        min_i = 0
        min_d = 10000.0
        for i in range(len(points) // 2):
            x, y = points[2 * i], points[2 * i + 1]
            dist = ((x1 - x) ** 2 + (y1 - y) ** 2) ** 0.5
            if dist < min_d:
                min_d = dist
                min_i = i

        return min_i, min_d

    def finish(self):
        if super(PaintPolygon, self).finish():
            if self.perim_close_inst is not None:
                self.instruction_group.remove(self.perim_close_inst)
                self.perim_close_inst = None
                self.perim_line_inst.close = True
            return True
        return False

    def lock(self):
        if super(PaintPolygon, self).lock():
            if self.instruction_group is not None:
                self.perim_color_inst.rgb = self.line_color_locked[:3]
            return True
        return False

    def unlock(self):
        if super(PaintPolygon, self).unlock():
            if self.instruction_group is not None:
                self.perim_color_inst.rgb = self.line_color[:3]
            return True
        return False

    def select(self):
        if not super(PaintPolygon, self).select():
            return False
        if self.instruction_group is not None:
            # perim_close_inst cannot be ON if we're selecting
            self.perim_line_inst.width = 2 * self.line_width
        return True

    def deselect(self):
        if super(PaintPolygon, self).deselect():
            if self.instruction_group is not None:
                self.perim_line_inst.width = self.line_width
            return True
        return False

    def translate(self, dpos=None, pos=None):
        if dpos is not None:
            dx, dy = dpos
        elif pos is not None:
            px, py = self.selection_point
            x, y = pos
            dx, dy = x - px, y - py
        else:
            assert False

        points = self.points
        new_points = [None, ] * len(points)
        for i in range(len(points) // 2):
            new_points[2 * i] = points[2 * i] + dx
            new_points[2 * i + 1] = points[2 * i + 1] + dy
        self.selection_point = new_points[:2]
        self.points = new_points

        self.dispatch('on_update')
        return True

    def get_state(self, state=None):
        d = super(PaintPolygon, self).get_state(state)
        for k in ['points', 'selection_point']:
            d[k] = getattr(self, k)
        return d

    def rescale(self, scale):
        points = self.points
        if not points:
            return

        n = len(points) / 2.0
        cx = sum(points[::2]) / n
        cy = sum(points[1::2]) / n
        x_vals = ((x_val - cx) * scale + cx for x_val in points[::2])
        y_vals = ((y_val - cy) * scale + cy for y_val in points[1::2])

        points = [val for point in zip(x_vals, y_vals) for val in point]
        self.points = points
        self.selection_point = points[:2]    

class PaintFreeformPolygon(PaintPolygon):
    """A shape that represents a polygon.

    As opposed to :class:`PaintPolygon`, points are added to shape during the
    first touch, while the user holds the touch down and moves the touch,
    and the shape is finished when the user release the touch.

    Otherwise, it's the same as :class:`PaintPolygon`.
    """

    def handle_touch_down(self, touch, opos=None):
        if not self.finished:
            pos = opos or touch.pos
            if not self.selection_point:
                self.selection_point = pos[:]

            self.points.extend(pos)
            if self.perim_close_inst is not None:
                self.perim_close_inst.points = \
                    self.points[-2:] + self.points[:2]
            if len(self.points) >= 6:
                self.is_valid = True

    def handle_touch_move(self, touch):
        if self.finished:
            return super(PaintFreeformPolygon, self).handle_touch_move(touch)

        if not self.selection_point:
            self.selection_point = touch.pos[:]

        self.points.extend(touch.pos)
        if self.perim_close_inst is not None:
            self.perim_close_inst.points = self.points[-2:] + self.points[:2]
        if len(self.points) >= 6:
            self.is_valid = True

    def handle_touch_up(self, touch, outside=False):
        if self.finished:
            return super(PaintFreeformPolygon, self).handle_touch_up(touch)
        self.ready_to_finish = True

class PaintCanvasBehavior(PaintCanvasBehaviorBase):
    """Implements the :class:`PaintCanvasBehaviorBase` to be able to draw
    any of the following shapes: `'circle', 'ellipse', 'polygon', 'freeform'`,
    and 'point'.
    They are drawn using :class:`PaintCircle`, :class:`PaintEllipse`,
    :class:`PaintPolygon`, :class:`PaintFreeformPolygon`, and
    :class:`PaintPoint`, respectively.

    This is a demo class to be used as a guide for your own usage.
    """

    draw_mode = OptionProperty('freeform', options=[
        'circle', 'ellipse', 'polygon', 'freeform', 'point', 'none'])
    """The shape to create when a user starts drawing with a touch. It can be
    one of ``'circle', 'ellipse', 'polygon', 'freeform', 'point', 'none'`` and
    it starts drawing the corresponding shape in the painter widget.

    When ``'none'``, not shape will be drawn and only selection is possible.
    """

    shape_cls_map = {'ellipse': PaintEllipse,
        'polygon': PaintPolygon, 'freeform': PaintFreeformPolygon
    }
    """Maps :attr:`draw_mode` to the actual :attr:`PaintShape` subclass to be
    used for drawing when in this mode.

    This can be overwritten to add support for drawing other, non-builtin,
    shapes.
    """

    shape_cls_name_map = {}
    """Automatically generated mapping that maps the names of classes provided
    in :attr:`shape_cls_map` to the actual class objects. This is used when
    reconstructing shapes e.g. in :meth:`create_shape_from_state`, where we
    only have the class name in ``state``.
    """

    def __init__(self, **kwargs):
        self.shape_cls_name_map = {
            cls.__name__: cls for cls in self.shape_cls_map.values()
            if cls is not None}
        super(PaintCanvasBehavior, self).__init__(**kwargs)
        self.fbind('draw_mode', self._handle_draw_mode)

    def _handle_draw_mode(self, *largs):
        self.finish_current_shape()

    def create_shape_with_touch(self, touch):
        draw_mode = self.draw_mode
        if draw_mode is None:
            raise TypeError('Cannot create a shape when the draw mode is none')

        shape_cls = self.shape_cls_map[draw_mode]

        if shape_cls is None:
            return None
        return shape_cls()

    def create_shape(self, cls_name, **inst_kwargs):
        """Creates a new shape instance from the given arguments.

        E.g.:

        .. code-block:: python

            shape = painter.create_shape(
                'polygon', points=[0, 0, 300, 0, 300, 800, 0, 800])

        It is the same as using :meth:`PaintShape.create_shape` on the
        shape class.

        :param cls_name: The name of the shape class to create, e.g.
            ``"ellipse"``. It uses :attr:`shape_cls_map` to find the
            class to instantiate.
        :param inst_kwargs: Configuration options for the new shape that
            will be passed as options to the class when it is instantiated.
        :return: The newly created shape instance.
        """
        return self.shape_cls_map[cls_name].create_shape(**inst_kwargs)

    def create_add_shape(self, cls_name, **inst_kwargs):
        """Creates a new shape instance and also adds it the painter with
        :meth:`~PaintCanvasBehaviorBase.add_shape`.

        It has the same parameters and return value as :meth:`create_shape`.
        """
        shape = self.create_shape(cls_name, **inst_kwargs)
        self.add_shape(shape)
        shape.add_shape_to_canvas(self)
        return shape

    def create_shape_from_state(self, state, add=True):
        """Recreates a shape as given by the ``state`` and adds it to
        the painter with :meth:`~PaintCanvasBehaviorBase.add_shape`.

        :param state: the state dict as returned by
            :meth:`PaintShape.get_state`.
        :param add: Whether to add to the painter.
        :return: The newly created shape instance.
        """
        cls = self.shape_cls_name_map[state['cls']]
        shape = cls.create_shape_from_state(state)

        if add:
            self.add_shape(shape)
        return shape
    
class PainterWidget(PaintCanvasBehavior, FloatLayout):
    figure_wgt = ObjectProperty()
    desktop_mode = BooleanProperty(True)
    alpha = NumericProperty(1)
    max_rate = NumericProperty(2/60)

    def __init__(self,**kwargs):
        super().__init__(**kwargs)    
        self.selected_side = None
        self.last_touch_time=None
        self.verts = []
        self.widget_verts = []
        self.ax = None
        self.callback = None
        self.callback_clear = None
        
        self.alpha_other = 0.3
        self.ind = []

        self.collection = None
        self.xys = None
        self.Npts = None
        self.fc = None
        
        self.line = None  
        self.ind_line=[]
        
        self.first_touch=None
        self.current_shape_close=None

    #TODO manage mouse system cursor
    # def on_kv_post(self,_):     
    #     if platform != 'android' and self.desktop_mode: #only bind mouse position if not android or if the user set desktop mode to false
    #         Window.bind(mouse_pos=self.on_mouse_pos)
            
    def on_mouse_pos(self, something, touch):
        """
        TODO
        When the mouse moves, we check the position of the mouse
        and update the cursor accordingly.
        """
        if self.opacity and self.collide_point(*self.to_widget(*touch)):
            
            collision = self.collides_with_control_points(something, self.to_widget(*touch))
            if collision in ["top left", "bottom right"]:
                Window.set_system_cursor("size_nwse")
            elif collision in ["top right", "bottom left"]:
                Window.set_system_cursor("size_nesw")
            elif collision in ["top", "bottom"]:
                Window.set_system_cursor("size_ns")
            elif collision in ["left", "right"]:
                Window.set_system_cursor("size_we")
            else:
                Window.set_system_cursor("size_all")
                
        elif self.figure_wgt.collide_point(*touch):
            Window.set_system_cursor("arrow")
    

    def create_shape_with_touch(self, touch):
        shape = super(PainterWidget, self).create_shape_with_touch(touch)
        if shape is not None:
            shape.add_shape_to_canvas(self)
        return shape

    def add_shape(self, shape):
        if super(PainterWidget, self).add_shape(shape):
            shape.add_shape_to_canvas(self)
            return True
        return False
    
    def on_touch_down(self, touch):
        if self.figure_wgt.touch_mode!='selector':
            return False
        ud = touch.ud
        # whether the touch was used by the painter for any purpose whatsoever
        ud['paint_interacted'] = False
        # can be one of current, selected, done indicating how the touch was
        # used, if it was used. done means the touch is done and don't do
        # anything with anymore. selected means a shape was selected.
        ud['paint_interaction'] = ''
        # if this touch experienced a move
        ud['paint_touch_moved'] = False
        # the shape that was selected if paint_interaction is selected
        ud['paint_selected_shape'] = None
        # whether the selected_shapes contained the shape this touch was
        # used to select a shape in touch_down.
        ud['paint_was_selected'] = False
        ud['paint_cleared_selection'] = False

        if self.locked or self._processing_touch is not None:
            return super(PaintCanvasBehaviorBase, self).on_touch_down(touch)

        if super(PaintCanvasBehaviorBase, self).on_touch_down(touch):
            return True

        if self.figure_wgt.collide_point(*self.to_window(*touch.pos)):
            if self.figure_wgt.touch_mode=='selector':
                if touch.is_double_tap and self.callback_clear:
                    self.callback_clear()
                    return
                
                x, y = touch.pos[0], touch.pos[1]
                result=False
                if self.shapes and self.opacity==1:
                    result = self.check_if_inside_path(self.shapes[0].points,x,y)

                self.opacity=1
                if result:
                    shape = self.get_closest_selection_point_shape(touch.x, touch.y)
                    shape2 = self.get_closest_shape(touch.x, touch.y)
                    if shape is not None or shape2 is not None:
                        self.selected_side = "modify"
                        if shape:
                            self.start_shape_interaction(shape, (touch.x, touch.y))
                            shape.handle_touch_up(
                                touch, outside=not self.collide_point(touch.x, touch.y))
                            if self.check_new_shape_done(shape, 'up'):
                                self.finish_current_shape()
                        else:
                            self.start_shape_interaction(shape2, (touch.x, touch.y))
                            shape2.handle_touch_up(
                                touch, outside=not self.collide_point(touch.x, touch.y))
                            if self.check_new_shape_done(shape2, 'up'):
                                self.finish_current_shape()
                        
                    else:
                        self.selected_side = "pan"
                else:
                    shape = self.get_closest_selection_point_shape(touch.x, touch.y)
                    shape2 = self.get_closest_shape(touch.x, touch.y)
                    if shape is not None or shape2 is not None:
                        self.selected_side = "modify"
                        if shape:
                            ud['paint_interaction'] = 'current'
                            self.start_shape_interaction(shape, (touch.x, touch.y))
                            shape.handle_touch_up(
                                touch, outside=not self.collide_point(touch.x, touch.y))
                            if self.check_new_shape_done(shape, 'up'):
                                self.finish_current_shape()
                        else:
                            ud['paint_interaction'] = 'current'
                            self.start_shape_interaction(shape2, (touch.x, touch.y))
                            shape2.handle_touch_up(
                                touch, outside=not self.collide_point(touch.x, touch.y))
                            if self.check_new_shape_done(shape2, 'up'):
                                self.finish_current_shape()
      
                    else:
                        self.selected_side = "new select"
                        self.delete_all_shapes()
                
                ud['paint_interacted'] = True
                self._processing_touch = touch
                touch.grab(self)
        
                # if we have a current shape, all touch will go to it
                current_shape = self.current_shape
                if current_shape is not None:
                    ud['paint_cleared_selection'] = current_shape.finished and \
                        current_shape.get_interaction_point_dist(touch.pos) \
                        >= dp(self.min_touch_dist)
                    if ud['paint_cleared_selection']:
                        self.finish_current_shape()
        
                    else:
                        ud['paint_interaction'] = 'current'
                        current_shape.handle_touch_down(touch)

                        return True
        
                # next try to interact by selecting or interacting with selected shapes
                shape = self.get_closest_selection_point_shape(touch.x, touch.y)
                if shape is not None:
                    ud['paint_interaction'] = 'selected'
                    ud['paint_selected_shape'] = shape
                    ud['paint_was_selected'] = shape not in self.selected_shapes
                    return True
        
                if self._ctrl_down:
                    ud['paint_interaction'] = 'done'
                    return True

                if self.selected_side == "new select":

                    for shape in self.shapes:
                        shape.pointsize = dp(0.01)
                        
                return True                
                
        elif not self.collide_point(touch.x, touch.y):
            return False


    def on_touch_move(self, touch):
        if self.figure_wgt.touch_mode!='selector':
            return False        

        ud = touch.ud

        if touch.grab_current is self:
            # for move, only use normal touch, not touch outside range
            x, y = self.to_window(*self.pos)
                
            if self.selected_side == "new select" or self.selected_side == "modify":

                if ud['paint_interaction'] == 'done':
                    return True

                ud['paint_touch_moved'] = True
                
                if self.figure_wgt.collide_point(*self.to_window(*touch.pos)):

                    if not ud['paint_interaction']:
                        if ud['paint_cleared_selection'] or self.clear_selected_shapes():
                            ud['paint_interaction'] = 'done'
                            return True
    
                        # finally try creating a new shape
                        # touch must have originally collided otherwise we wouldn't be here
                        shape = self.create_shape_with_touch(touch)
                        if shape is not None:
                            shape.handle_touch_down(touch, opos=touch.opos)
                            self.first_touch = touch
                            self.current_shape = shape
                            if self.check_new_shape_done(shape, 'down'):
                                self.finish_current_shape()
                                ud['paint_interaction'] = 'done'
                                return True
    
                            ud['paint_interaction'] = 'current_new'
                        else:
                            ud['paint_interaction'] = 'done'
                            return True
    
                    if ud['paint_interaction'] in ('current', 'current_new'):
                        if self.current_shape is None:
                            ud['paint_interaction'] = 'done'
                        else:
                            self.current_shape.handle_touch_move(touch)
                        return True
    
            if self.selected_side == "pan":
                
                    shape = ud['paint_selected_shape']

                    dataxy = np.array(self.shapes[0].points).reshape(-1,2)
                    xmax, ymax = dataxy.max(axis=0)
                    xmin, ymin = dataxy.min(axis=0)
                    if self.figure_wgt.collide_point(*self.to_window(xmin +touch.dx,ymin+touch.dy)) and \
                        self.figure_wgt.collide_point(*self.to_window(xmax+touch.dx,ymax+touch.dy)):

                        for s in self.shapes:
                            s.translate(dpos=(touch.dx, touch.dy))
                    return True

            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.figure_wgt.touch_mode!='selector':
            return False        
        ud = touch.ud

        if touch.grab_current is self:
            touch.ungrab(self)  
            # don't process the same touch up again
            paint_interaction = ud['paint_interaction']
            ud['paint_interaction'] = 'done'
            self._processing_touch = None
            self.finish_current_shape()
            self.alpha = 1

                
            if self.selected_side != "modify":
                if self.selected_side == "new select" and self.shapes:
                    self.filter_path(self.shapes[0])
                elif self.selected_side=='pan' and self.shapes:
                    self.widget_verts = np.array(self.shapes[0].points).reshape(-1, 2)

                # self.clear_selected_shapes()
                shape = self.get_closest_shape(touch.x, touch.y)
                if shape is not None:
                    ud['paint_interaction'] = 'current'

                    for shape in self.shapes:
                        shape.pointsize = dp(7)
                else:
                    for shape in self.shapes:
                        shape.pointsize = dp(7)
                        
                if self.widget_verts is not None:
                    self.verts = self._get_lasso_data(self.widget_verts)
                    self.onselect(self.verts)
                    
            if self.selected_side == "modify":

                paint_interaction = ud['paint_interaction']
                ud['paint_interaction'] = 'done' 
                self._processing_touch = None

                if not paint_interaction:
                    if ud['paint_cleared_selection'] or self.clear_selected_shapes():
                        return True

                    # finally try creating a new shape
                    # touch must have originally collided otherwise we wouldn't be here
                    shape = self.create_shape_with_touch(touch)
                    if shape is not None:
                        shape.handle_touch_down(touch, opos=touch.opos)
                        self.current_shape = shape
                        if self.check_new_shape_done(shape, 'down'):
                            self.finish_current_shape()
                            return True

                        paint_interaction = 'current_new'
                    else:
                        return True

                if self.current_shape is not None:
                    self.current_shape.handle_touch_up(
                        touch, outside=not self.collide_point(touch.x, touch.y))
                    if self.check_new_shape_done(self.current_shape, 'up'):
                        self.finish_current_shape()

                self.finish_current_shape()
                if self.selected_side=='modify' and self.shapes:
                    self.widget_verts = np.array(self.shapes[0].points).reshape(-1, 2)[1:,:]
                    if self.widget_verts is not None:
                        self.verts = self._get_lasso_data(self.widget_verts)
                        self.onselect(self.verts)
                return super().on_touch_up(touch)


                shape = ud['paint_selected_shape']
                if shape not in self.shapes:
                    return True

                if self._ctrl_down or self.multiselect:
                    if not ud['paint_was_selected'] and shape in self.selected_shapes:
                        self.deselect_shape(shape)
                    elif ud['paint_was_selected']:
                        self.select_shape(shape)
                else:
                    if len(self.selected_shapes) != 1 or \
                            self.selected_shapes[0] != shape:
                        self.clear_selected_shapes()
                        self.select_shape(shape)
                        

                return True
                    
            return True  
            
        if self.figure_wgt.collide_point(*self.to_window(*touch.pos)):        
            self._processing_touch = None

            return True        
        

        return super().on_touch_up(touch)
       

    def check_if_inside_path(self,pts,x,y):
        verts = np.array(pts).reshape(-1, 2)
        path = Path(verts)
        ind = np.nonzero(path.contains_points(np.array([[x,y]])))[0]
        if len(ind)!=0:
            return True
        else:
            return False
        
    def get_closest_selection_point_shape(self, x, y):
        """Given a position, it returns the shape whose selection point is the
        closest to this position among all the shapes.

        This is how we find the shape to drag around and select it. Each shape
        has a single selection point by which it can be selected and dragged.
        We find the shape with the closest selection point among all the
        shapes, and that shape is returned.

        :param x: The x pos.
        :param y: The y pos.
        :return: The :class:`PaintShape` that is the closest as described.
        """
        min_dist = dp(self.min_touch_dist)
        closest_shape = None
        for shape in reversed(self.shapes):  # upper shape takes pref
            # if shape.locked:
            #     continue

            dist = shape.get_selection_point_dist((x, y))
            if dist < min_dist:
                closest_shape = shape
                min_dist = dist

        return closest_shape
    
    def do_long_touch(self, touch, *largs):
        """Handles a long touch by the user.
        """
        # assert self._processing_touch
        touch.push()
        touch.apply_transform_2d(self.to_widget)

        self._long_touch_trigger = None
        ud = touch.ud
        if ud['paint_interaction'] == 'selected':
            if self._ctrl_down:
                ud['paint_interaction'] = 'done'
                touch.pop()
                return
            ud['paint_interaction'] = ''

        # assert ud['paint_interacted']
        # assert not ud['paint_interaction']

        self.clear_selected_shapes()
        shape = self.get_closest_shape(touch.x, touch.y)
        if shape is not None:
            ud['paint_interaction'] = 'current'
            self.start_shape_interaction(shape, (touch.x, touch.y))
        else:
            ud['paint_interaction'] = 'done'
        touch.pop() 
        
    def filter_path(self,shape):
        pts = shape.points
        verts = np.array(pts).reshape(-1, 2)
        filter_pts = rdp(verts,5.0)
        
        if len(filter_pts) < 6 :
            self.widget_verts = None
            return
        
        
        #delete old shape
        self.delete_all_shapes()
        
        shape = self.create_shape_with_touch(self.first_touch)
        if shape is not None:
            shape.handle_touch_down(self.first_touch, opos=self.first_touch.opos)
            self.current_shape = shape
        
        
        #crete new filter shape
        for data_xy in filter_pts:
            
            if not self.current_shape.selection_point:
                self.current_shape.selection_point = data_xy
    
            self.current_shape.points.extend(data_xy)
            if self.current_shape.perim_close_inst is not None:
                self.current_shape.perim_close_inst.points = self.current_shape.points[-2:] + self.current_shape.points[:2]
            if len(self.current_shape.points) >= 6:
                self.current_shape.is_valid = True
                
        self.finish_current_shape()
        
        self.widget_verts = filter_pts

    def set_collection(self,collection):
        self.collection = collection
        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object
        self.fc = collection.get_facecolors()
        if len(self.fc) == 0:
            raise ValueError('Collection must have a facecolor')
        elif len(self.fc) == 1:
            self.fc = np.tile(self.fc, (self.Npts, 1))
            
    def set_line(self,line):
        self.line = line            
 
    def onselect(self, verts):
        if verts:
            path = Path(verts)
            if self.collection:
                self.ind = np.nonzero(path.contains_points(self.xys))[0] #xys collection.get_offsets()
                self.fc[:, -1] = self.alpha_other
                self.fc[self.ind, -1] = 1
                self.collection.set_facecolors(self.fc)
            if self.line:
                xdata,ydata = self.line.get_data()
                self.ind_line = np.nonzero(path.contains_points(np.array([xdata,ydata]).T))[0]                  
    
            self.figure_wgt.figure.canvas.draw_idle()
            if self.callback:
                self.callback(self)
            
    def set_callback(self,callback):
        self.callback=callback
        
    def set_callback_clear(self,callback):
        self.callback_clear=callback          
        
    def clear_selection(self):

        if self.collection:
            self.ind = []
            self.fc[:, -1] = 1
            self.collection.set_facecolors(self.fc)
        if self.line:
            self.ind_line=[]

        self.delete_all_shapes()
        self.figure_wgt.figure.canvas.draw_idle()  
        
    def _get_lasso_data(self,widget_verts):
        trans = self.ax.transData.inverted() 
        
        verts=[]
        for data_xy in widget_verts:
            x, y = trans.transform_point((data_xy[0] + self.to_window(*self.pos)[0]-self.figure_wgt.pos[0],
                                          data_xy[1] + self.to_window(*self.pos)[1]-self.figure_wgt.pos[1]))
            verts.append((x, y))

        return verts
    
class PainterWidget2(PaintCanvasBehavior, FloatLayout):
    figure_wgt = ObjectProperty()
    desktop_mode = BooleanProperty(True)
    alpha = NumericProperty(1)
    max_rate = NumericProperty(2/60)

    def __init__(self,**kwargs):
        super().__init__(**kwargs)    
        self.selected_side = None
        self.last_touch_time=None
        self.verts = []
        self.widget_verts = []
        self.ax = None
        self.callback = None
        self.callback_clear = None
        
        self.alpha_other = 0.3
        self.ind = []

        self.collection = None
        self.xys = None
        self.Npts = None
        self.fc = None
        
        self.line = None  
        self.ind_line=[]
        
        self.first_touch=None
        self.current_shape_close=None

    #TODO manage mouse system cursor
    # def on_kv_post(self,_):     
    #     if platform != 'android' and self.desktop_mode: #only bind mouse position if not android or if the user set desktop mode to false
    #         Window.bind(mouse_pos=self.on_mouse_pos)
            
    def on_mouse_pos(self, something, touch):
        """
        TODO
        When the mouse moves, we check the position of the mouse
        and update the cursor accordingly.
        """
        if self.opacity and self.collide_point(*self.to_widget(*touch)):
            
            collision = self.collides_with_control_points(something, self.to_widget(*touch))
            if collision in ["top left", "bottom right"]:
                Window.set_system_cursor("size_nwse")
            elif collision in ["top right", "bottom left"]:
                Window.set_system_cursor("size_nesw")
            elif collision in ["top", "bottom"]:
                Window.set_system_cursor("size_ns")
            elif collision in ["left", "right"]:
                Window.set_system_cursor("size_we")
            else:
                Window.set_system_cursor("size_all")
                
        elif self.figure_wgt.collide_point(*touch):
            Window.set_system_cursor("arrow")
    

    def create_shape_with_touch(self, touch, check=True):
        shape = super(PainterWidget2, self).create_shape_with_touch(touch)
        # print('aa')
        if check and shape.radius_x==dp(10) and shape.radius_y==dp(15):
            return None       
        
        if shape is not None:
            shape.add_shape_to_canvas(self)
        return shape

    def add_shape(self, shape):
        if super(PainterWidget2, self).add_shape(shape):
            shape.add_shape_to_canvas(self)
            return True
        return False
    
    def on_touch_down(self, touch):
        if self.figure_wgt.touch_mode!='selector':
            return False

        ud = touch.ud
        # whether the touch was used by the painter for any purpose whatsoever
        ud['paint_interacted'] = False
        # can be one of current, selected, done indicating how the touch was
        # used, if it was used. done means the touch is done and don't do
        # anything with anymore. selected means a shape was selected.
        ud['paint_interaction'] = ''
        # if this touch experienced a move
        ud['paint_touch_moved'] = False
        # the shape that was selected if paint_interaction is selected
        ud['paint_selected_shape'] = None
        # whether the selected_shapes contained the shape this touch was
        # used to select a shape in touch_down.
        ud['paint_was_selected'] = False
        ud['paint_cleared_selection'] = False
        if self.locked or self._processing_touch is not None:
            return super(PaintCanvasBehaviorBase, self).on_touch_down(touch)

        if super(PaintCanvasBehaviorBase, self).on_touch_down(touch):
            return True
        
        if self.figure_wgt.collide_point(*self.to_window(*touch.pos)):
            
            
            if self.figure_wgt.touch_mode=='selector':
                
                if touch.is_double_tap and self.callback_clear:
                    self.callback_clear()
                    return

                x, y = touch.pos[0], touch.pos[1]
                result=False
                if self.shapes and self.opacity==1:
                    result = self.check_if_inside_path(self.shapes[0],x,y)
                    
                self.opacity=1
                if result:
                    shape = self.get_closest_selection_point_shape(touch.x, touch.y)
                    shape2 = self.get_closest_shape(touch.x, touch.y)
                    if shape is not None or shape2 is not None:
                        self.selected_side = "modify"
                        if shape:
                            self.start_shape_interaction(shape, (touch.x, touch.y))
                            shape.handle_touch_up(
                                touch, outside=not self.collide_point(touch.x, touch.y))
                            if self.check_new_shape_done(shape, 'up'):
                                self.finish_current_shape()
                        else:
                            self.start_shape_interaction(shape2, (touch.x, touch.y))
                            shape2.handle_touch_up(
                                touch, outside=not self.collide_point(touch.x, touch.y))
                            if self.check_new_shape_done(shape2, 'up'):
                                self.finish_current_shape()
                        
                    else:
                        self.selected_side = "pan"
                        touch.grab(self)
                        return True
                else:
                    shape = self.get_closest_selection_point_shape(touch.x, touch.y)
                    shape2 = self.get_closest_shape(touch.x, touch.y)
                    if shape is not None or shape2 is not None:
                        self.selected_side = "modify"
                        if shape:
                            ud['paint_interaction'] = 'current'
                            self.start_shape_interaction(shape, (touch.x, touch.y))
                            shape.handle_touch_up(
                                touch, outside=not self.collide_point(touch.x, touch.y))
                            if self.check_new_shape_done(shape, 'up'):
                                self.finish_current_shape()
                        else:
                            ud['paint_interaction'] = 'current'
                            self.start_shape_interaction(shape2, (touch.x, touch.y))
                            shape2.handle_touch_up(
                                touch, outside=not self.collide_point(touch.x, touch.y))
                            if self.check_new_shape_done(shape2, 'up'):
                                self.finish_current_shape()
      
                    else:
                        self.selected_side = "new select"
                        self.delete_all_shapes()
                
                ud['paint_interacted'] = True
                self._processing_touch = touch
                touch.grab(self)
                # if we have a current shape, all touch will go to it
                current_shape = self.current_shape
                if current_shape is not None:
                    ud['paint_cleared_selection'] = current_shape.finished and \
                        current_shape.get_interaction_point_dist(touch.pos) \
                        >= dp(self.min_touch_dist)
                    if ud['paint_cleared_selection']:
                        self.finish_current_shape()
        
                    else:
                        ud['paint_interaction'] = 'current'
                        current_shape.handle_touch_down(touch)
                        

                        return True
        
                # next try to interact by selecting or interacting with selected shapes
                shape = self.get_closest_selection_point_shape(touch.x, touch.y)
                if shape is not None:
                    ud['paint_interaction'] = 'selected'
                    ud['paint_selected_shape'] = shape
                    ud['paint_was_selected'] = shape not in self.selected_shapes
                    return True
        
                if self._ctrl_down:
                    ud['paint_interaction'] = 'done'
                    return True

                if self.selected_side == "new select":

                    for shape in self.shapes:
                        shape.pointsize = dp(7)
                        
                return True 
                
                
        elif not self.collide_point(touch.x, touch.y):
            if self.figure_wgt.collide_point(*self.to_window(*touch.pos)):
                self.delete_all_shapes()
            return False


    def on_touch_move(self, touch):
        if self.figure_wgt.touch_mode!='selector':
            return False        

        ud = touch.ud

        if touch.grab_current is self:
            # for move, only use normal touch, not touch outside range
            x, y = self.to_window(*self.pos)
                
            if self.selected_side == "new select" or self.selected_side == "modify":

                # if ud['paint_interaction'] == 'done':
                #     return True

                ud['paint_touch_moved'] = True
                
                if self.figure_wgt.collide_point(*self.to_window(*touch.pos)):

                    if not ud['paint_interaction']:
                        if ud['paint_cleared_selection'] or self.clear_selected_shapes():
                            ud['paint_interaction'] = 'done'
                            return True
    
                        # finally try creating a new shape
                        # touch must have originally collided otherwise we wouldn't be here
                        shape = self.create_shape_with_touch(touch,check=False)
                        if shape is not None:
                            shape.handle_touch_down(touch, opos=touch.opos)
                            self.first_touch = touch
                            self.current_shape = shape
                            self.current_shape.during_creation = True
                            
                            if self.check_new_shape_done(shape, 'down'):
                                
                                self.finish_current_shape()
                                self.current_shape = self.shapes[0]
                                ud['paint_interaction'] = 'done'
                                return True
    
                            ud['paint_interaction'] = 'current_new'
                        else:
                            ud['paint_interaction'] = 'done'
                            shape.handle_touch_move(touch)
                            return True
    
                    # if ud['paint_interaction'] in ('current', 'current_new'):
                    else:
                        if self.current_shape is None:
                            ud['paint_interaction'] = 'done'
                        else:
                            self.current_shape.start_interaction((touch.x, touch.y))
                            self.current_shape.handle_touch_move(touch)
                        return True
    
            if self.selected_side == "pan":
                shape = ud['paint_selected_shape']

                xmin,xmax,ymin,ymax = self.shapes[0].get_min_max()
                if self.figure_wgt.collide_point(*self.to_window(xmin +touch.dx,ymin+touch.dy)) and \
                    self.figure_wgt.collide_point(*self.to_window(xmax+touch.dx,ymax+touch.dy)):

                    for s in self.shapes:
                        s.translate(dpos=(touch.dx, touch.dy))
                return True

            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        
        if self.figure_wgt.touch_mode!='selector':
            return False 
            
        ud = touch.ud
        
        if touch.grab_current is self:
            touch.ungrab(self)  
            # don't process the same touch up again
            paint_interaction = ud['paint_interaction']
            ud['paint_interaction'] = 'done'
            self._processing_touch = None
            self.finish_current_shape()
            self.alpha = 1
            

                
            if self.selected_side != "modify":
                if self.selected_side == "new select" and self.shapes:
                    self.shapes[0].during_creation = False
                    self.widget_verts = self.shapes[0].get_widget_verts()
                elif self.selected_side=='pan' and self.shapes:
                    self.widget_verts = self.shapes[0].get_widget_verts()

                # self.clear_selected_shapes()
                shape = self.get_closest_shape(touch.x, touch.y)
                if shape is not None:
                    ud['paint_interaction'] = 'current'

                    for shape in self.shapes:
                        shape.pointsize = dp(7)
                else:
                    for shape in self.shapes:
                        shape.pointsize = dp(7)
                        
                if self.widget_verts is not None:
                    self.verts = self._get_ellipse_data(self.widget_verts)
                    self.onselect(self.verts)
    
                    
            if self.selected_side == "modify":

                paint_interaction = ud['paint_interaction']
                ud['paint_interaction'] = 'done' 
                self._processing_touch = None

                if not paint_interaction:
                    if ud['paint_cleared_selection'] or self.clear_selected_shapes():
                        return True

                    # finally try creating a new shape
                    # touch must have originally collided otherwise we wouldn't be here
                    shape = self.create_shape_with_touch(touch)
                    if shape is not None:
                        shape.handle_touch_down(touch, opos=touch.opos)
                        self.current_shape = shape
                        if self.check_new_shape_done(shape, 'down'):
                            self.finish_current_shape()
                            return True

                        paint_interaction = 'current_new'
                    else:
                        return True

                if self.current_shape is not None:
                    self.current_shape.handle_touch_up(
                        touch, outside=not self.collide_point(touch.x, touch.y))
                    if self.check_new_shape_done(self.current_shape, 'up'):
                        self.finish_current_shape()

                self.finish_current_shape()
                if self.selected_side=='modify' and self.shapes:
                    self.widget_verts = self.shapes[0].get_widget_verts()

                    if self.widget_verts is not None:
                        self.verts = self._get_ellipse_data(self.widget_verts)
                        self.onselect(self.verts)
                return super().on_touch_up(touch)


                shape = ud['paint_selected_shape']
                if shape not in self.shapes:
                    return True

                if self._ctrl_down or self.multiselect:
                    if not ud['paint_was_selected'] and shape in self.selected_shapes:
                        self.deselect_shape(shape)
                    elif ud['paint_was_selected']:
                        self.select_shape(shape)
                else:
                    if len(self.selected_shapes) != 1 or \
                            self.selected_shapes[0] != shape:
                        self.clear_selected_shapes()
                        self.select_shape(shape)
                        

                return True
                    
            return True  
            
        if self.figure_wgt.collide_point(*self.to_window(*touch.pos)):        
            self._processing_touch = None

            return True        
        
        self.finish_current_shape()

        return super().on_touch_up(touch)
       

    def check_if_inside_path(self,shape,x,y):
        cx, cy = shape.center
        width= shape.radius_x * 2
        height= shape.radius_y * 2
        angle= shape.rotate_inst.angle
        
        path = Ellipse_mpl((cx,cy), width, height,angle=angle)
        ind = np.nonzero(path.contains_points(np.array([[x,y]])))[0]
        if len(ind)!=0:
            return True
        else:
            return False
        
    def get_closest_selection_point_shape(self, x, y):
        """Given a position, it returns the shape whose selection point is the
        closest to this position among all the shapes.

        This is how we find the shape to drag around and select it. Each shape
        has a single selection point by which it can be selected and dragged.
        We find the shape with the closest selection point among all the
        shapes, and that shape is returned.

        :param x: The x pos.
        :param y: The y pos.
        :return: The :class:`PaintShape` that is the closest as described.
        """
        min_dist = dp(self.min_touch_dist)
        closest_shape = None
        for shape in reversed(self.shapes):  # upper shape takes pref
            # if shape.locked:
            #     continue

            dist = shape.get_selection_point_dist((x, y))
            if dist < min_dist:
                closest_shape = shape
                min_dist = dist

        return closest_shape
    
    def do_long_touch(self, touch, *largs):
        """Handles a long touch by the user.
        """
        # assert self._processing_touch
        touch.push()
        touch.apply_transform_2d(self.to_widget)

        self._long_touch_trigger = None
        ud = touch.ud
        if ud['paint_interaction'] == 'selected':
            if self._ctrl_down:
                ud['paint_interaction'] = 'done'
                touch.pop()
                return
            ud['paint_interaction'] = ''

        # assert ud['paint_interacted']
        # assert not ud['paint_interaction']

        self.clear_selected_shapes()
        shape = self.get_closest_shape(touch.x, touch.y)
        if shape is not None:
            ud['paint_interaction'] = 'current'
            self.start_shape_interaction(shape, (touch.x, touch.y))
        else:
            ud['paint_interaction'] = 'done'
        touch.pop() 
        

    def set_collection(self,collection):
        self.collection = collection
        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object
        self.fc = collection.get_facecolors()
        if len(self.fc) == 0:
            raise ValueError('Collection must have a facecolor')
        elif len(self.fc) == 1:
            self.fc = np.tile(self.fc, (self.Npts, 1))
            
    def set_line(self,line):
        self.line = line            
 
    def onselect(self, verts):
        if verts and self.shapes:           
            cx, cy = self.shapes[0].center
            width= self.shapes[0].radius_x * 2
            height= self.shapes[0].radius_y * 2
            angle= self.shapes[0].rotate_inst.angle
            
            path = Ellipse_mpl((cx,cy), width, height,angle=angle)
            
            newverts = self._get_ellipse_data(path.get_verts())
            
            path = Path(newverts)

            if self.collection:
                self.ind = np.nonzero(path.contains_points(self.xys))[0] #xys collection.get_offsets()
                self.fc[:, -1] = self.alpha_other
                self.fc[self.ind, -1] = 1
                self.collection.set_facecolors(self.fc)
            if self.line:
                xdata,ydata = self.line.get_data()
                self.ind_line = np.nonzero(path.contains_points(np.array([xdata,ydata]).T))[0]                  
    
            self.figure_wgt.figure.canvas.draw_idle()
            if self.callback:
                self.callback(self)
                
    def set_callback(self,callback):
        self.callback=callback
        
    def set_callback_clear(self,callback):
        self.callback_clear=callback          
        
    def clear_selection(self):

        if self.collection:
            self.ind = []
            self.fc[:, -1] = 1
            self.collection.set_facecolors(self.fc)
        if self.line:
            self.ind_line=[]

        self.delete_all_shapes()
        self.figure_wgt.figure.canvas.draw_idle()  
        
    def _get_ellipse_data(self,widget_verts):
        trans = self.ax.transData.inverted() 
        
        verts=[]
        for data_xy in widget_verts:
            x, y = trans.transform_point((data_xy[0] + self.to_window(*self.pos)[0]-self.figure_wgt.pos[0],
                                          data_xy[1] + self.to_window(*self.pos)[1]-self.figure_wgt.pos[1]))
            verts.append((x, y))

        return verts
    

class SpanSelect(FloatLayout):
    top_color = ColorProperty("black")
    bottom_color = ColorProperty("black")
    left_color = ColorProperty("black")
    right_color = ColorProperty("black")
    highlight_color = ColorProperty("red")
    bg_color = ColorProperty([1,1,1,1])    
    figure_wgt = ObjectProperty()
    desktop_mode = BooleanProperty(True)
    span_orientation = OptionProperty('vertical', options=['vertical','horizontal'])
    span_color = ColorProperty("red")
    span_alpha = NumericProperty(0.3)
    span_hide_on_release = BooleanProperty(False)
    alpha = NumericProperty(1)
    invert_rect_ver = BooleanProperty(False)
    invert_rect_hor = BooleanProperty(False)    
    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.verts = []
        self.ax = None
        self.callback = None
        
        self.alpha_other = 0.3
        self.ind = []

        self.collection = None
        self.xys = None
        self.Npts = None
        self.fc = None
        
        self.line = None  
        self.ind_line=[]
        
        self.first_touch=None

    def on_kv_post(self,_):     
        if platform != 'android' and self.desktop_mode: #only bind mouse position if not android or if the user set desktop mode to false
            Window.bind(mouse_pos=self.on_mouse_pos)
            
    def update_bg_color(self):
        fig_bg_color = self.figure_wgt.figure.get_facecolor()
        rgb_fig_bg_color = mcolors.to_rgb(fig_bg_color)
        if (rgb_fig_bg_color[0]*0.299 + rgb_fig_bg_color[1]*0.587 + rgb_fig_bg_color[2]*0.114) > 186/255:
            self.bg_color = [1,1,1,1]
            self.bottom_color = (
                self.top_colors
            ) = self.left_color = self.right_color = [1,1,1,1]
            
        else:
            self.bg_color = [0,0,0,1]
            self.bottom_color = (
                self.top_colors
            ) = self.left_color = self.right_color = [0,0,0,1]
        
    def set_collection(self,collection):
        self.collection = collection
        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object
        self.fc = collection.get_facecolors()
        if len(self.fc) == 0:
            raise ValueError('Collection must have a facecolor')
        elif len(self.fc) == 1:
            self.fc = np.tile(self.fc, (self.Npts, 1))
            
    def set_line(self,line):
        self.line = line          

    def on_mouse_pos(self, something, touch):
        """
        When the mouse moves, we check the position of the mouse
        and update the cursor accordingly.
        """
        if self.opacity and self.figure_wgt.touch_mode=='selector' and self.collide_point(*self.to_widget(*touch)):
            
            collision = self.collides_with_control_points(something, self.to_widget(*touch))
            if collision in ["top left", "bottom right"]:
                Window.set_system_cursor("size_nwse")
            elif collision in ["top right", "bottom left"]:
                Window.set_system_cursor("size_nesw")
            elif collision in ["top", "bottom"]:
                Window.set_system_cursor("size_ns")
            elif collision in ["left", "right"]:
                Window.set_system_cursor("size_we")
            else:
                Window.set_system_cursor("size_all")
                
        elif self.figure_wgt.collide_point(*touch):
        # else:
            Window.set_system_cursor("arrow")

    def collides_with_control_points(self, _, touch):
        """
        Returns True if the mouse is over a control point.
        """
        x, y = touch[0], touch[1]

        
        if self.span_orientation == 'vertical':
            # Checking mouse is on left edge
            if self.x - dp(7) <= x <= self.x + dp(7):
                if self.y <= y <= self.y + self.height:
                    return "left"
                else:
                    return False

            # Checking mouse is on right edge
            elif self.x + self.width - dp(7) <= x <= self.x + self.width + dp(7):
                if self.y<= y <= self.y + self.height:
                    return "right"
                else:
                    return False 
            else:
                return False

        elif self.span_orientation == 'horizontal':
            # Checking mouse is on top edge
            if self.x <= x <= self.x + self.width:
                if self.y <= y <= self.y + dp(7):
                    return "bottom"
                elif self.y + self.height - dp(7)<= y <= self.y + self.height:
                    return "top"
                else:
                    return False
            else:
                return False


    def on_touch_down(self, touch):
        if self.figure_wgt.touch_mode != 'selector':
            return
        if self.collide_point(*touch.pos) and self.opacity:
            touch.grab(self)
            x, y = touch.pos[0], touch.pos[1]

            collision = self.collides_with_control_points("", touch.pos)

            if collision == "top":
                self.top_color = self.highlight_color
                self.selected_side = "top"
            elif collision == "bottom":
                self.bottom_color = self.highlight_color
                self.selected_side = "bottom"
            elif collision == "left":
                self.left_color = self.highlight_color
                self.selected_side = "left"
            elif collision == "right":
                self.right_color = self.highlight_color
                self.selected_side = "right"
            else:
                self.selected_side = None
                self.top_color = self.highlight_color
                self.bottom_color = self.highlight_color
                self.left_color = self.highlight_color
                self.right_color = self.highlight_color
        elif self.figure_wgt.collide_point(*self.to_window(*touch.pos)):
            if self.figure_wgt.touch_mode=='selector':
                if touch.is_double_tap and self.callback_clear:
                    self.callback_clear()
                    return
                
                touch.grab(self)
                #get figure boundaries (in pixels)
                
                left_bound = float(self.figure_wgt.x +self.ax.bbox.bounds[0])
                right_bound = float(self.figure_wgt.x +self.ax.bbox.bounds[2] +self.ax.bbox.bounds[0] )
                top_bound = float(self.figure_wgt.y +self.ax.bbox.bounds[3] + self.ax.bbox.bounds[1])
                bottom_bound = float(self.figure_wgt.y +self.ax.bbox.bounds[1])
                
                width = right_bound-left_bound
                
                left_bound,right_bound = self.to_widget(left_bound,right_bound)

                x, y = touch.pos[0], touch.pos[1]
                
                self.opacity=1
                
                if self.span_orientation == 'vertical':
                    self.pos = (x,bottom_bound - self.figure_wgt.y)
                    self.size = (5,top_bound-bottom_bound) 
                elif self.span_orientation == 'horizontal':
                    self.pos = (left_bound,y)
                    self.size = (width,-5) 
                    
                # self.size = (5,5)
                self.opacity=1
                if self.span_orientation == 'vertical':
                    self.first_touch = (x,bottom_bound - self.figure_wgt.y) 
                elif self.span_orientation == 'horizontal':
                    self.first_touch = (left_bound,y)
                self.selected_side = "new select"
                
            
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.figure_wgt.touch_mode != 'selector':
            return
        
        if touch.grab_current is self:
            x, y = self.to_window(*self.pos)

            top = y + self.height  # top of our widget
            right = x + self.width  # right of our widget
            
            if self.selected_side == "top":
                if self.height + touch.dy <= MINIMUM_HEIGHT:
                    return False
                self.height += touch.dy

            elif self.selected_side == "bottom":
                if self.height - touch.dy <= MINIMUM_HEIGHT:
                    return False
                self.height -= touch.dy
                self.y += touch.dy

            elif self.selected_side == "left":
                if self.width - touch.dx <= MINIMUM_WIDTH:
                    return False
                self.width -= touch.dx
                self.x += touch.dx

            elif self.selected_side == "right":
                if self.width + touch.dx <= MINIMUM_WIDTH:
                    return False
                self.width += touch.dx

                
            elif self.selected_side == "new select":
                if self.span_orientation == 'vertical':
                    self.width += touch.dx
                elif self.span_orientation == 'horizontal':
                    self.height += touch.dy

            elif not self.selected_side:
                if self.figure_wgt.collide_point(*self.to_window(self.pos[0]+touch.dx,self.pos[1]+touch.dy )) and \
                    self.figure_wgt.collide_point(*self.to_window(self.pos[0] + self.size[0]+touch.dx,self.pos[1]+ self.size[1]+touch.dy )):
                    if self.span_orientation == 'vertical':    
                        self.x += touch.dx
                    elif self.span_orientation == 'horizontal':
                        self.y += touch.dy

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.figure_wgt.touch_mode != 'selector':
            return
        
        if touch.grab_current is self:
            touch.ungrab(self)
            self.alpha = 1
            if (self.bg_color[0]*0.299 + \
            self.bg_color[1]*0.587 + self.bg_color[2]*0.114) > 186/255:
                self.bottom_color = (
                    self.top_colors
                ) = self.left_color = self.right_color = [0,0,0,1]
            else:
                self.bottom_color = (
                    self.top_colors
                ) = self.left_color = self.right_color = [1,1,1,1]                
            
            if self.first_touch and self.selected_side == "new select":
                self.check_if_reverse_selection(touch)
            
            if abs(self.size[0])<MINIMUM_WIDTH or abs(self.size[1])<MINIMUM_HEIGHT:
                self.reset_selection()
            else:
                if self.verts is not None:
                    self.verts = self._get_box_data()
                    self.onselect(self.verts)

            return True
        return super().on_touch_up(touch)
    
    def check_if_reverse_selection(self,last_touch):  
        if self.span_orientation == 'vertical':
            if last_touch.x > self.first_touch[0]:
                return
            else:
                # print('reverse')
                self.pos[0] = last_touch.x + 5 
                self.size[0] = abs(self.size[0]) #self.first_touch[0] - last_touch.x
                
        elif self.span_orientation == 'horizontal':
            if last_touch.y > self.first_touch[1]:
                return
            else:
                # print('reverse')  
                self.pos[1] = last_touch.y  - 5
                self.size[1] = abs(self.size[1])
            
        else:
            return

    def reset_selection(self):
        self.pos = (0,0)
        self.size = (dp(0.01),dp(0.01))
        self.opacity=0

        
    def _get_box_data(self):
        trans = self.ax.transData.inverted() 
        #get box 4points xis data
        x0 = self.to_window(*self.pos)[0]-self.figure_wgt.pos[0]
        y0 = self.to_window(*self.pos)[1]-self.figure_wgt.pos[1]
        x1 = self.to_window(*self.pos)[0]-self.figure_wgt.pos[0]
        y1 = self.to_window(*self.pos)[1] + self.height-self.figure_wgt.pos[1]
        x3 = self.to_window(*self.pos)[0] + self.width-self.figure_wgt.pos[0]
        y3 = self.to_window(*self.pos)[1]-self.figure_wgt.pos[1]
        x2 = self.to_window(*self.pos)[0] + self.width -self.figure_wgt.pos[0]
        y2 = self.to_window(*self.pos)[1] + self.height  -self.figure_wgt.pos[1]
        
        
        x0_box, y0_box = trans.transform_point((x0, y0)) 
        x1_box, y1_box = trans.transform_point((x1, y1))
        x2_box, y2_box = trans.transform_point((x2, y2))
        x3_box, y3_box = trans.transform_point((x3, y3))
        verts=[]
        verts.append((x0_box, y0_box))
        verts.append((x1_box, y1_box))
        verts.append((x2_box, y2_box))
        verts.append((x3_box, y3_box))
        
        if self.span_orientation == 'vertical':
            if self.collection:
                ymin = np.nanmin(self.xys[:,1])
                ymax = np.nanmax(self.xys[:,1])
            if self.line:
                ydata = self.line.get_ydata()
                ymin = np.nanmin(ydata)
                ymax = np.nanmax(ydata)                
                
            verts[0] = (verts[0][0],ymin-1)
            verts[3] = (verts[3][0],ymin-1)
            verts[1] = (verts[1][0],ymax+1)
            verts[2] = (verts[2][0],ymax+1)
            
        elif self.span_orientation == 'horizontal':
            if self.collection:
                xmin = np.nanmin(self.xys[:,1])
                xmax = np.nanmax(self.xys[:,1])
            if self.line:
                xdata = self.line.get_xdata() 
                xmin = np.nanmin(xdata)
                xmax = np.nanmax(xdata)
                   
            verts[0] = (xmin-1,verts[0][1])
            verts[1] = (xmin-1,verts[1][1])
            verts[2] = (xmax+1,verts[2][1])
            verts[3] = (xmax+1 ,verts[3][1])           
            

        return verts

    def onselect(self, verts):
        path = Path(verts)
        if self.collection:
            self.ind = np.nonzero(path.contains_points(self.xys))[0] #xys collection.get_offsets()
            self.fc[:, -1] = self.alpha_other
            self.fc[self.ind, -1] = 1
            self.collection.set_facecolors(self.fc)
        if self.line:
            xdata,ydata = self.line.get_data()
            
            #matplotlib method if data is sorted
            # indmin, indmax = np.searchsorted(x, (xmin, xmax))
            # indmax = min(len(x) - 1, indmax)
            
            # region_x = x[indmin:indmax]
            # region_y = y[indmin:indmax]
            
            self.ind_line = np.nonzero(path.contains_points(np.array([xdata,ydata]).T))[0]                  

        self.figure_wgt.figure.canvas.draw_idle()
        if self.callback:
            self.callback(self)
            
    def set_callback(self,callback):
        self.callback=callback

    def set_callback_clear(self,callback):
        self.callback_clear=callback  
        
    def clear_selection(self):

        if self.collection:
            self.ind = []
            self.fc[:, -1] = 1
            self.collection.set_facecolors(self.fc)
        if self.line:
            self.ind_line=[]
            
        self.reset_selection()
        self.figure_wgt.figure.canvas.draw_idle()
    
Builder.load_string(kv)