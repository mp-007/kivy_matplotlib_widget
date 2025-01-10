""" MatplotFigure is based on https://github.com/mp-007/kivy_matplotlib_widget """
__all__ = (
    'MatplotFigureCropFactor',
)

import math
import copy

import matplotlib
matplotlib.use('Agg')

from kivy.graphics.texture import Texture
from kivy.graphics.transformation import Matrix
from kivy.lang import Builder
from kivy.properties import ObjectProperty, ListProperty, BooleanProperty, AliasProperty, \
    NumericProperty, OptionProperty, BoundedNumericProperty, StringProperty
from kivy.uix.widget import Widget
from kivy.vector import Vector
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib import cbook
from matplotlib.backend_bases import ResizeEvent
from weakref import WeakKeyDictionary
from kivy.metrics import dp
import numpy as np



class MatplotFigureCropFactor(Widget):
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
    legend_do_scroll_x = BooleanProperty(True)
    legend_do_scroll_y = BooleanProperty(True)
    interactive_axis = BooleanProperty(False) 
    do_pan_x = BooleanProperty(True)
    do_pan_y = BooleanProperty(True)    
    do_zoom_x = BooleanProperty(True)
    do_zoom_y = BooleanProperty(True)  
    fast_draw = BooleanProperty(True) #True will don't draw axis
    xsorted = BooleanProperty(False) #to manage x sorted data
    minzoom = NumericProperty(dp(20))
    compare_xdata = BooleanProperty(False)   
    hover_instance = ObjectProperty(None, allownone=True)
    nearest_hover_instance = ObjectProperty(None, allownone=True)
    compare_hover_instance = ObjectProperty(None, allownone=True)
    disable_mouse_scrolling = BooleanProperty(False) 
    disable_double_tap = BooleanProperty(False) 
    text_instance = None
    auto_zoom = BooleanProperty(False)
    zoom_angle_detection=NumericProperty(15) #in degree
    auto_cursor = BooleanProperty(False)
    autoscale_visible_only = BooleanProperty(True)
    autoscale_axis = OptionProperty("both", options=["both", "x", "y"])
    autoscale_tight = BooleanProperty(False) 
    scale_min = NumericProperty(0.01)
    scale_max = NumericProperty(1e20)

    stop_xlimits = ListProperty(None, allownone=True)
    stop_ylimits = ListProperty(None, allownone=True)
    x_cursor_label = StringProperty("x")
    y_cursor_label = StringProperty("y")
    show_cursor = BooleanProperty(False)
    
    default_dpi=None
    crop_factor = NumericProperty(2.2)

    def on_figure(self, obj, value):
        if self.default_dpi is None:
            #get default matplotlib figure dpi
            self.default_dpi = self.figure.get_dpi()
            
        self.figure.dpi = self.default_dpi / self.crop_factor
        self.figcanvas = _FigureCanvas(self.figure, self)
        self.figcanvas._isDrawn = False
        _, _, w, h = self.figure.bbox.bounds
        w = int(math.ceil(w))
        h = int(math.ceil(h))

        self.width = w
        self.height = h
        self._img_texture = Texture.create(size=(w, h))

        if self.figure.axes[0]:
            ax = self.figure.axes[0]
            patch_cpy = copy.copy(ax.patch)
            patch_cpy.set_visible(False)
            for pos in ['right', 'top', 'bottom', 'left']:
                ax.spines[pos].set_zorder(10)
            patch_cpy.set_zorder(9)
            self.background_patch_copy = ax.add_patch(patch_cpy)

            self.axes = self.figure.axes[0]
            self.xmin, self.xmax = self.axes.get_xlim()
            self.ymin, self.ymax = self.axes.get_ylim()

        matplotlib.pyplot.close()

    def __init__(self, **kwargs):
        super(MatplotFigureCropFactor, self).__init__(**kwargs)

        # figure info
        self.figure = None
        self.axes = None
        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None

        # option
        self.touch_mode = 'pan'  # pan, pan_x, pan_y, adjust_x, adjust_y
        self.text=None
        self.cursor_xaxis_formatter=None #used matplotlib formatter to display x cursor value
        self.cursor_yaxis_formatter=None #used matplotlib formatter to display y cursor value
        
        # clear touches on touch up
        self._touches = []
        self._last_touch_pos = {}
        
        #pan management
        self.first_touch_pan = None        

        # background
        self.background = None
        self.background_patch_copy = None

        # manage adjust x and y
        self.anchor_x = None
        self.anchor_y = None

        # manage back and next event
        if hasattr(cbook,'_Stack'):
            #manage matplotlib version with no Stack (replace by _Stack)
            self._nav_stack = cbook._Stack()
        else:
            self._nav_stack = cbook.Stack()  

        self.bind(size=self._onSize)

    def on_crop_factor(self, obj, value):
        if self.figure:
            if self.default_dpi is None:
                #get default matplotlib figure dpi
                self.default_dpi = self.figure.get_dpi()
    
            self.figure.dpi = self.default_dpi / value
            
            self.figcanvas.draw()
        
    def transform_eval(self, x, axis):
        custom_transform = axis.get_transform()
        return custom_transform.transform_non_affine(np.array([x]))[0]

    def inv_transform_eval(self, x, axis):
        inv_custom_transform = axis.get_transform().inverted()
        return inv_custom_transform.transform_non_affine(np.array([x]))[0]

    def register_lines(self) -> None:
        self.horizontal_line = self.axes.axhline(color='orange', lw=0.8, ls='--', visible=False, animated=True)
        self.vertical_line = self.axes.axvline(color='orange', lw=0.8, ls='--', visible=False, animated=True)

        self.text = self.axes.text(0.0, 1.01, ' ',
                                   transform=self.axes.transAxes,
                                   ha='left', color='orange', fontsize=14, animated=True)
        self._text_data = ' '

        self.horizontal_line.set_zorder(1000)
        self.vertical_line.set_zorder(1000)

    def set_cross_hair_visible(self, visible: bool) -> None:
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        if visible:
            self.text.set_text(self._text_data)
        else:
            self._text_data = self.text._text
            self.text.set_text(' ')

    def home(self) -> None:
        if (
            self.xmin is not None
            and self.xmax is not None
            and self.ymin is not None
            and self.ymax is not None
        ):

            ax = self.axes
            xleft, xright = ax.get_xlim()
            ybottom, ytop = ax.get_ylim()

            # check inverted data
            inverted_x = False
            if xleft > xright:
                inverted_x = True
            inverted_y = False
            if ybottom > ytop:
                inverted_y = True

            if inverted_x:
                ax.set_xlim(right=self.xmin, left=self.xmax)
            else:
                ax.set_xlim(left=self.xmin, right=self.xmax)
            if inverted_y:
                ax.set_ylim(top=self.ymin, bottom=self.ymax)
            else:
                ax.set_ylim(bottom=self.ymin, top=self.ymax)

            self._draw(ax)

    def update(self):
        """Reset the Axes stack."""
        self._nav_stack.clear()

    def push_current(self):
        """Push the current view limits and position onto the stack."""
        self._nav_stack.push(
            WeakKeyDictionary(
                {ax: (
                    ax._get_view(),
                    (ax.get_position(True).frozen(), ax.get_position().frozen())
                ) for ax in self.figure.axes}))

    def _update_view(self):
        """
        Update the viewlim and position from the view and position stack for
        each Axes.
        """
        nav_info = self._nav_stack()
        if nav_info is None:
            return
        # Retrieve all items at once to avoid any risk of GC deleting an Axes
        # while in the middle of the loop below.
        items = list(nav_info.items())
        for ax, (view, (pos_orig, pos_active)) in items:
            ax._set_view(view)
            # Restore both the original and modified positions
            ax._set_position(pos_orig, 'original')
            ax._set_position(pos_active, 'active')

        self.figure.canvas.draw_idle()
        self.figure.canvas.flush_events()

    def reset_touch(self) -> None:
        """ reset touch

        Return:
            None
        """
        self._touches = []
        self._last_touch_pos = {}

    def _get_scale(self):
        """ kivy scatter _get_scale method """
        p1 = Vector(*self.to_parent(0, 0))
        p2 = Vector(*self.to_parent(1, 0))
        scale = p1.distance(p2)

        if hasattr(self, '_scale_p'):
            if str(scale) == str(self._scale_p):
                return self._scale_p

        self._scale_p = scale
        return scale

    def _set_scale(self, scale):
        """ kivy scatter _set_scale method """
        rescale = scale * 1.0 / self.scale
        self.apply_transform(Matrix().scale(rescale, rescale, rescale),
                             post_multiply=True,
                             anchor=self.to_local(*self.center))

    scale = AliasProperty(_get_scale, _set_scale, bind=('x', 'y', 'transform'))

    def normalize_axis_stops(self, stop_limits, xlim):
        if stop_limits is not None:
            if xlim[0] is not None and stop_limits[0] > xlim[0]:
                xlim = stop_limits[0], xlim[1]
            if xlim[1] is not None and stop_limits[1] < xlim[1]:
                xlim = xlim[0], stop_limits[1]

        return xlim

    def _draw_bitmap(self):
        """ draw bitmap method. based on kivy scatter method"""

        if self._bitmap is None:
            return

        self._img_texture = Texture.create(size=(self.bt_w, self.bt_h))
        self._img_texture.flip_vertical()
        self._img_texture.blit_buffer(
            bytes(self._bitmap), size=(self.bt_w, self.bt_h), colorfmt='rgba', bufferfmt='ubyte')
        self.update_hover()

    def transform_with_touch(self, event):
        """ manage touch behaviour. based on kivy scatter method"""
        # just do a simple one finger drag
        event_ppos = event.ppos[0] / self.crop_factor, event.ppos[1] / self.crop_factor
        event_pos = event.pos[0] / self.crop_factor, event.pos[1] / self.crop_factor

        if len(self._touches) == self.translation_touches:
            
            if self.touch_mode=='pan':
                if self._nav_stack() is None:
                    self.push_current()                
                self.apply_pan(self.axes, event)
 
            if self.touch_mode=='pan_x' or self.touch_mode=='pan_y' \
                or self.touch_mode=='adjust_x' or self.touch_mode=='adjust_y':
                if self._nav_stack() is None:
                    self.push_current()                    
                self.apply_pan(self.axes, event, mode=self.touch_mode)                
            
            elif self.touch_mode=='zoombox':
                if self._nav_stack() is None:
                    self.push_current()                
                real_x, real_y = event.x - self.pos[0], event.y - self.pos[1]
                #in case x_init is not create
                if not hasattr(self,'x_init'):
                    self.x_init = event.x
                    self.y_init = real_y
                self.draw_box(event, self.x_init,self.y_init, event.x, real_y)
                
            changed = True

        #note: avoid zoom in/out on touch mode zoombox
        if len(self._touches) == 1:#
            return changed

        # we have more than one touch... list of last known pos
        points = [Vector(self._last_touch_pos[t]) for t in self._touches if t is not event]
        points.append(Vector(event_pos))

        # we only want to transform if the touch is part of the two touches
        # farthest apart! So first we find anchor, the point to transform
        # around as another touch farthest away from current touch's pos
        anchor = max(points[:-1], key=lambda p: p.distance(event_pos))

        # now we find the touch farthest away from anchor, if its not the
        # same as touch. Touch is not one of the two touches used to transform
        farthest = max(points, key=anchor.distance)
        if farthest is not points[-1]:
            return False

        # ok, so we have touch, and anchor, so we can actually compute the
        # transformation
        old_line = Vector(*event_ppos) - anchor
        new_line = Vector(*event_pos) - anchor
        if not new_line.length():  # div by zero
            return False

        if self.do_scale:
            scale = old_line.length() / new_line.length()
            new_scale = scale * self.scale
            if new_scale < self.scale_min:
                scale = self.scale_min / self.scale
            elif new_scale > self.scale_max:
                scale = self.scale_max / self.scale

            self.apply_zoom(scale, self.axes, anchor=anchor, new_line=new_line)

            return True

        return False

    def on_touch_down(self, event):
        """ Manage Mouse/touch press """
        if self.disabled:
            return

        if self.collide_point(*self.to_local(*event.pos)) and self.figure:
            self._pressed = True
            if event.is_mouse_scrolling:
                if not self.disable_mouse_scrolling:
                    ax = self.axes
                    ax = self.axes
                    self.zoom_factory(event, ax, base_scale=1.1)
                return True

            elif event.is_double_tap:
                if not self.disable_double_tap:
                    self.home()
                return True

            else:
                if self.touch_mode=='zoombox':
                    x, y = event.x, event.y
                    real_x, real_y = x - self.pos[0], y - self.pos[1]
                    self.x_init=x
                    self.y_init=real_y
                    self.draw_box(event, x, real_y, x, real_y)                 
                event.grab(self)
                self._touches.append(event)
                self._last_touch_pos[event] = event.pos[0] / self.crop_factor, event.pos[1] / self.crop_factor
                if len(self._touches) > 1:
                    self.background = None

                return True

        else:
            return False

    def on_touch_move(self, event):
        """ Manage Mouse/touch move while pressed """
        if self.disabled:
            return

        if event.is_double_tap:
            if not self.disable_double_tap:
                self.home()
            return True

        # scale/translate
        if event in self._touches and event.grab_current == self:
            self.transform_with_touch(event)
            self._last_touch_pos[event] = event.pos[0] / self.crop_factor, event.pos[1] / self.crop_factor

        # stop propagating if its within our bounds
        if self.collide_point(*event.pos):
            return True

    def on_touch_up(self, event):
        """ Manage Mouse/touch release """
        # remove it from our saved touches
        if event in self._touches and event.grab_state:
            event.ungrab(self)
            del self._last_touch_pos[event]
            self._touches.remove(event)
            if self.touch_mode=='pan' or self.touch_mode=='zoombox' or \
                self.touch_mode=='pan_x' or self.touch_mode=='pan_y' \
                    or self.touch_mode=='adjust_x' or self.touch_mode=='adjust_y' \
                        or self.touch_mode=='minmax': 
                        
                self.push_current()
                if self.interactive_axis:
                    if self.touch_mode=='pan_x' or self.touch_mode=='pan_y' \
                        or self.touch_mode=='adjust_x' or self.touch_mode=='adjust_y':
                        self.touch_mode='pan'
                    self.first_touch_pan=None

        x, y = event.x, event.y
        if abs(self._box_size[0]) > 1 or abs(self._box_size[1]) > 1 or self.touch_mode=='zoombox':
            self.reset_box()  
            if not self.collide_point(x, y) and self.do_update:
                #update axis lim if zoombox is used and touch outside widget
                self.update_lim()            
                ax=self.axes
                ax.figure.canvas.draw_idle()
                ax.figure.canvas.flush_events() 
                return True
            
        # stop propagating if its within our bounds
        if self.collide_point(x, y) and self.figure:
            self._pressed = False

            if self.do_update:
                self.update_lim()            

            self.anchor_x=None
            self.anchor_y=None
            
            ax=self.axes
            self.background=None
            self.show_compare_cursor=True
            ax.figure.canvas.draw_idle()
            ax.figure.canvas.flush_events()                           
            
            return True

    def apply_zoom(self, scale_factor, ax, anchor=(0, 0), new_line=None):
        """ zoom touch method """

        self.background = None
        x = anchor[0] - self.pos[0] / self.crop_factor
        y = anchor[1] - self.pos[1] / self.crop_factor

        trans = ax.transData.inverted()
        xdata, ydata = trans.transform_point((x + new_line.x / 2, y + new_line.y / 2))

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()

        scale = ax.get_xscale()
        yscale = ax.get_yscale()

        if scale == 'linear':
            old_min = cur_xlim[0]
            old_max = cur_xlim[1]
        else:
            min_ = cur_xlim[0]
            max_ = cur_xlim[1]
            old_min = self.transform_eval(min_, ax.yaxis)
            xdata = self.transform_eval(xdata, ax.yaxis)
            old_max = self.transform_eval(max_, ax.yaxis)

        if yscale == 'linear':
            yold_min = cur_ylim[0]
            yold_max = cur_ylim[1]
        else:
            ymin_ = cur_ylim[0]
            ymax_ = cur_ylim[1]
            yold_min = self.transform_eval(ymin_, ax.yaxis)
            ydata = self.transform_eval(ydata, ax.yaxis)
            yold_max = self.transform_eval(ymax_, ax.yaxis)

        new_width = (old_max - old_min) * scale_factor
        new_height = (yold_max - yold_min) * scale_factor

        relx = (old_max - xdata) / (old_max - old_min)
        rely = (yold_max - ydata) / (yold_max - yold_min)

        if self.do_zoom_x:
            x_left = xdata - new_width * (1 - relx)
            x_right = xdata + new_width * (relx)
            if scale != 'linear':
                try:
                    x_left, x_right = self.inv_transform_eval(x_left, ax.xaxis), self.inv_transform_eval(x_right, ax.xaxis)
                except OverflowError:  # Limit case
                    x_left, x_right = min_, max_
                    if x_left <= 0. or x_right <= 0.:  # Limit case
                        x_left, x_right = min_, max_

            x_left, x_right = self.normalize_axis_stops(self.stop_xlimits, (x_left, x_right))
            ax.set_xlim([x_left, x_right])

        if self.do_zoom_y:
            y_left = ydata - new_height * (1 - rely)
            y_right = ydata + new_height * (rely)
            if yscale != 'linear':
                try:
                    y_left, y_right = self.inv_transform_eval(y_left, ax.yaxis), self.inv_transform_eval(y_right, ax.yaxis)
                except OverflowError:  # Limit case
                    y_left, y_right = ymin_, ymax_
                    if y_left <= 0. or y_right <= 0.:  # Limit case
                        y_left, y_right = ymin_, ymax_

            y_left, y_right = self.normalize_axis_stops(self.stop_ylimits, (y_left, y_right))
            ax.set_ylim([y_left, y_right])

        self._draw(ax)

    def apply_pan(self, ax, event, mode='pan'):
        """ pan method """
        # self.background = None
        trans = ax.transData.inverted()
        xdata, ydata = trans.transform_point(((event.x - self.pos[0]) / self.crop_factor,
                                              (event.y - self.pos[1]) / self.crop_factor))
        xpress, ypress = trans.transform_point(((self._last_touch_pos[event][0] - self.pos[0] / self.crop_factor),
                                                (self._last_touch_pos[event][1] - self.pos[1] / self.crop_factor)))
        
        # trans = ax.transData.inverted()
        # xdata, ydata = trans.transform_point((event.x-self.pos[0], event.y-self.pos[1]))
        # xpress, ypress = trans.transform_point((self._last_touch_pos[event][0]-self.pos[0], self._last_touch_pos[event][1]-self.pos[1]))
        
        scale=ax.get_xscale()
        yscale=ax.get_yscale()
        
        if scale == 'linear':
            dx = xdata - xpress
        else:
            dx = self.transform_eval(xdata,ax.xaxis) - \
                self.transform_eval(xpress,ax.xaxis)
                
        if yscale == 'linear':
            dy = ydata - ypress
        else:
            dy = self.transform_eval(ydata,ax.yaxis) - \
                self.transform_eval(ypress,ax.yaxis)        

        xleft,xright=self.axes.get_xlim()
        ybottom,ytop=self.axes.get_ylim()
        
        #check inverted data
        inverted_x = False
        if xleft>xright:
            inverted_x=True
            cur_xlim=(xright,xleft)
        else:
            cur_xlim=(xleft,xright)
        inverted_y = False
        if ybottom>ytop:
            inverted_y=True 
            cur_ylim=(ytop,ybottom)
        else:
            cur_ylim=(ybottom,ytop) 
        
        if self.interactive_axis and self.touch_mode=='pan' and not self.first_touch_pan=='pan':
            if (ydata < cur_ylim[0] and not inverted_y) or (ydata > cur_ylim[1] and inverted_y):
                left_anchor_zone= (cur_xlim[1] - cur_xlim[0])*.2 + cur_xlim[0]
                right_anchor_zone= (cur_xlim[1] - cur_xlim[0])*.8 + cur_xlim[0]
                if xdata < left_anchor_zone or xdata > right_anchor_zone:
                    mode = 'adjust_x'
                else:
                    mode = 'pan_x'
                self.touch_mode = mode
            elif (xdata < cur_xlim[0] and not inverted_x) or (xdata > cur_xlim[1] and inverted_x):
                bottom_anchor_zone=  (cur_ylim[1] - cur_ylim[0])*.2 + cur_ylim[0]
                top_anchor_zone= (cur_ylim[1] - cur_ylim[0])*.8 + cur_ylim[0]               
                if ydata < bottom_anchor_zone or ydata > top_anchor_zone:
                    mode = 'adjust_y'
                else:
                    mode= 'pan_y' 
                self.touch_mode = mode
            else:
                self.touch_mode = 'pan'

        if not mode=='pan_y' and not mode=='adjust_y':             
            if mode=='adjust_x':
                if self.anchor_x is None:
                    midpoint= (cur_xlim[1] + cur_xlim[0])/2
                    if xdata>midpoint:
                        self.anchor_x='left'
                    else:
                        self.anchor_x='right'
                if self.anchor_x=='left':                
                    if xdata> cur_xlim[0]:
                        if scale == 'linear':
                            cur_xlim -= dx
                        else:
                            try:
                                cur_xlim = [self.inv_transform_eval((self.transform_eval(cur_xlim[0],ax.xaxis) - dx),ax.xaxis),
                                           self.inv_transform_eval((self.transform_eval(cur_xlim[1],ax.xaxis) - dx),ax.xaxis)]  
                            except (ValueError, OverflowError):
                                cur_xlim = cur_xlim  # Keep previous limits  

                        if self.stop_xlimits is not None:
                            if cur_xlim[0] > self.stop_xlimits[0] and cur_xlim[1] < self.stop_xlimits[1]:
                                if inverted_x:
                                    ax.set_xlim(cur_xlim[1], None)
                                else:
                                    ax.set_xlim(None, cur_xlim[1])
                        else:                                
                            if inverted_x:
                                ax.set_xlim(cur_xlim[1],None)
                            else:
                                ax.set_xlim(None,cur_xlim[1])
                else:
                    if xdata< cur_xlim[1]:
                        if scale == 'linear':
                            cur_xlim -= dx
                        else:
                            try:
                                cur_xlim = [self.inv_transform_eval((self.transform_eval(cur_xlim[0],ax.xaxis) - dx),ax.xaxis),
                                           self.inv_transform_eval((self.transform_eval(cur_xlim[1],ax.xaxis) - dx),ax.xaxis)]  
                            except (ValueError, OverflowError):
                                cur_xlim = cur_xlim  # Keep previous limits 
                                
                        if self.stop_xlimits is not None:
                            if cur_xlim[0] > self.stop_xlimits[0] and cur_xlim[1] < self.stop_xlimits[1]:
                                if inverted_x:
                                    ax.set_xlim(None, cur_xlim[0])
                                else:
                                    ax.set_xlim(cur_xlim[0], None)
                        else:                                
                            if inverted_x:
                                ax.set_xlim(None,cur_xlim[0])
                            else:
                                ax.set_xlim(cur_xlim[0],None)
            else:
                if scale == 'linear':
                    cur_xlim -= dx
                else:
                    try:
                        cur_xlim = [self.inv_transform_eval((self.transform_eval(cur_xlim[0],ax.xaxis) - dx),ax.xaxis),
                                   self.inv_transform_eval((self.transform_eval(cur_xlim[1],ax.xaxis) - dx),ax.xaxis)]  
                    except (ValueError, OverflowError):
                        cur_xlim = cur_xlim  # Keep previous limits  
                        
                if self.stop_xlimits is not None:
                    if cur_xlim[0] < self.stop_xlimits[0] or cur_xlim[1] > self.stop_xlimits[1]:
                        side = 'left' if (xleft - cur_xlim[0]) > 0 else 'right'
                        diff = min(abs(cur_xlim[0] - self.stop_xlimits[0]), abs(cur_xlim[1] - self.stop_xlimits[1]))
                        if side == 'left':
                            cur_xlim = cur_xlim[0] + diff, cur_xlim[1] + diff
                        else:
                            cur_xlim = cur_xlim[0] - diff, cur_xlim[1] - diff
                    if inverted_x:
                        ax.set_xlim(cur_xlim[1], cur_xlim[0])
                    else:
                        ax.set_xlim(cur_xlim)
                else:                        
                    if inverted_x:
                        ax.set_xlim(cur_xlim[1],cur_xlim[0])
                    else:
                        ax.set_xlim(cur_xlim)
                
        if not mode=='pan_x' and not mode=='adjust_x':
            if mode=='adjust_y':
                if self.anchor_y is None:
                    midpoint= (cur_ylim[1] + cur_ylim[0])/2
                    if ydata>midpoint:
                        self.anchor_y='top'
                    else:
                        self.anchor_y='bottom'               
                
                if self.anchor_y=='top':
                    if ydata> cur_ylim[0]:
                        if yscale == 'linear':
                            cur_ylim -= dy
                        
                        else:
                            try:
                                cur_ylim = [self.inv_transform_eval((self.transform_eval(cur_ylim[0],ax.yaxis) - dy),ax.yaxis),
                                           self.inv_transform_eval((self.transform_eval(cur_ylim[1],ax.yaxis) - dy),ax.yaxis)]
                            except (ValueError, OverflowError):
                                cur_ylim = cur_ylim  # Keep previous limits                        
                        
                        if inverted_y:
                            ax.set_ylim(cur_ylim[1],None)
                        else:
                            ax.set_ylim(None,cur_ylim[1])
                else:
                    if ydata< cur_ylim[1]:
                        if yscale == 'linear':
                            cur_ylim -= dy
                        
                        else:
                            try:
                                cur_ylim = [self.inv_transform_eval((self.transform_eval(cur_ylim[0],ax.yaxis) - dy),ax.yaxis),
                                           self.inv_transform_eval((self.transform_eval(cur_ylim[1],ax.yaxis) - dy),ax.yaxis)]
                            except (ValueError, OverflowError):
                                cur_ylim = cur_ylim  # Keep previous limits 
                        if inverted_y:
                            ax.set_ylim(None,cur_ylim[0]) 
                        else:
                            ax.set_ylim(cur_ylim[0],None)
            else:            
                if yscale == 'linear':
                    cur_ylim -= dy 
                
                else:
                    try:
                        cur_ylim = [self.inv_transform_eval((self.transform_eval(cur_ylim[0],ax.yaxis) - dy),ax.yaxis),
                                   self.inv_transform_eval((self.transform_eval(cur_ylim[1],ax.yaxis) - dy),ax.yaxis)]
                    except (ValueError, OverflowError):
                        cur_ylim = cur_ylim  # Keep previous limits 
                if inverted_y:
                    ax.set_ylim(cur_ylim[1],cur_ylim[0])
                else:
                    ax.set_ylim(cur_ylim)

        # self._draw(ax)
        if self.first_touch_pan is None:
            self.first_touch_pan=self.touch_mode

        if self.fast_draw: 
            #use blit method               
            if self.background is None:
                self.background_patch_copy.set_visible(True)
                ax.figure.canvas.draw_idle()
                ax.figure.canvas.flush_events()                   
                self.background = ax.figure.canvas.copy_from_bbox(ax.figure.bbox)
                self.background_patch_copy.set_visible(False)  
            ax.figure.canvas.restore_region(self.background)                
           
            for line in ax.lines:
                ax.draw_artist(line)
                
            ax.figure.canvas.blit(ax.bbox)
            ax.figure.canvas.flush_events() 
            
            # self.update_hover()
            
        else:
            ax.figure.canvas.draw_idle()
            ax.figure.canvas.flush_events()        

    def zoom_factory(self, event, ax, base_scale=1.1):
        """ zoom with scrolling mouse method """
        self.background = None
        xdata, ydata = self._calculate_mouse_position(self.to_local(*event.pos))

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()

        scale = ax.get_xscale()
        yscale = ax.get_yscale()

        if scale == 'linear':
            old_min = cur_xlim[0]
            old_max = cur_xlim[1]

        else:
            min_ = cur_xlim[0]
            max_ = cur_xlim[1]
            old_min = self.transform_eval(min_, ax.yaxis)
            xdata = self.transform_eval(xdata, ax.yaxis)
            old_max = self.transform_eval(max_, ax.yaxis)

        if yscale == 'linear':
            yold_min = cur_ylim[0]
            yold_max = cur_ylim[1]

        else:
            ymin_ = cur_ylim[0]
            ymax_ = cur_ylim[1]
            yold_min = self.transform_eval(ymin_, ax.yaxis)
            ydata = self.transform_eval(ydata, ax.yaxis)
            yold_max = self.transform_eval(ymax_, ax.yaxis)

        if event.button == 'scrolldown':
            # deal with zoom in
            scale_factor = 1 / base_scale
        elif event.button == 'scrollup':
            # deal with zoom out
            scale_factor = base_scale
        else:
            scale_factor = 1

        new_width = (old_max - old_min) * scale_factor
        new_height = (yold_max - yold_min) * scale_factor

        relx = (old_max - xdata) / (old_max - old_min)
        rely = (yold_max - ydata) / (yold_max - yold_min)

        if self.do_zoom_x:
            x_left = xdata - new_width * (1 - relx)
            x_right = xdata + new_width * (relx)

            if scale != 'linear':
                try:
                    x_left, x_right = self.inv_transform_eval(x_left, ax.yaxis), self.inv_transform_eval(x_right, ax.yaxis)
                except OverflowError:  # Limit case
                    x_left, x_right = min_, max_
                    if x_left <= 0. or x_right <= 0.:  # Limit case
                        x_left, x_right = min_, max_

            x_left, x_right = self.normalize_axis_stops(self.stop_xlimits, (x_left, x_right))
            ax.set_xlim([x_left, x_right])

        if self.do_zoom_y:
            y_left = ydata - new_height * (1 - rely)
            y_right = ydata + new_height * (rely)

            if yscale != 'linear':
                try:
                    y_left, y_right = self.inv_transform_eval(y_left, ax.yaxis), self.inv_transform_eval(y_right, ax.yaxis)
                except OverflowError:  # Limit case
                    y_left, y_right = ymin_, ymax_
                    if y_left <= 0. or y_right <= 0.:  # Limit case
                        y_left, y_right = ymin_, ymax_

            y_left, y_right = self.normalize_axis_stops(self.stop_ylimits, (y_left, y_right))
            ax.set_ylim([y_left, y_right])

        self._draw(ax)

    def _onSize(self, o, size):
        """ _onsize method """
        self.background = None
        if self.figure is None or self.axes is None:
            return

        # Create a new, correctly sized bitmap
        self._width, self._height = size
        self.figcanvas._isDrawn = False

        if self._width <= 1 or self._height <= 1:
            return

        dpival = self.figure.dpi
        winch = self._width / dpival
        hinch = self._height / dpival
        self.figure.set_size_inches(winch / self.crop_factor, hinch / self.crop_factor)

        event = ResizeEvent('resize_event', self.figcanvas)
        self.figcanvas.callbacks.process('resize_event', event)

    def _update_background(self):
        if self.text:
            self.set_cross_hair_visible(False)
        self.axes.figure.canvas.draw_idle()
        self.axes.figure.canvas.flush_events()                   
        self.background = self.axes.figure.canvas.copy_from_bbox(self.axes.figure.bbox)
        if self.text:
            self.set_cross_hair_visible(True)         

    def _draw(self, ax):
        if self.fast_draw:
            if self.background is None:
                self._update_background()

            ax.figure.canvas.restore_region(self.background)

            for line in ax.lines:
                ax.draw_artist(line)

            for image in ax.images:
                ax.draw_artist(image)

            if self.show_cursor and self.text:
                self.axes.draw_artist(self.text)
                self.axes.draw_artist(self.horizontal_line)
                self.axes.draw_artist(self.vertical_line)
            ax.figure.canvas.blit(ax.bbox)

        else:
            ax.figure.canvas.draw_idle()
            if self.show_cursor and self.text:
                self.axes.draw_artist(self.text)
                self.axes.draw_artist(self.horizontal_line)
                self.axes.draw_artist(self.vertical_line)
            ax.figure.canvas.blit(ax.bbox)

        ax.figure.canvas.flush_events()

    def _calculate_mouse_position(self, pos):
        trans = self.axes.transData.inverted()
        x, y = trans.transform_point(((pos[0] - self.pos[0]) / self.crop_factor, (pos[1] - self.pos[1]) / self.crop_factor))
        return x, y

    def on_motion(self, window, pos):
        if self.collide_point(*pos) and self.show_cursor:
            # self.set_cross_hair_visible(True)
            x, y = self._calculate_mouse_position(self.to_local(*pos))
            if self.hover_instance:
                ax=self.axes
                self.hover_instance.xmin_line = float(ax.bbox.bounds[0]) *self.crop_factor  + self.x
                self.hover_instance.xmax_line = float(ax.bbox.bounds[0] + ax.bbox.bounds[2]) *self.crop_factor + self.x              
                self.hover_instance.ymin_line = float(ax.bbox.bounds[1])*self.crop_factor  + self.y
                self.hover_instance.ymax_line = float(ax.bbox.bounds[1] + ax.bbox.bounds[3])*self.crop_factor
                xy_pos = ax.transData.transform([(x,y)]) 
                self.x_hover_data = x
                self.y_hover_data = y
                self.hover_instance.x_hover_pos=float(xy_pos[0][0])*self.crop_factor + self.x
                self.hover_instance.y_hover_pos=float(xy_pos[0][1])*self.crop_factor + self.y
                self.hover_instance.show_cursor=True
                    
                if self.cursor_xaxis_formatter:
                    x = self.cursor_xaxis_formatter.format_data(x)
                else:
                    x = ax.xaxis.get_major_formatter().format_data_short(x)
                if self.cursor_yaxis_formatter:
                    y = self.cursor_yaxis_formatter.format_data(y) 
                else:
                    y = ax.yaxis.get_major_formatter().format_data_short(y)
                self.hover_instance.label_x_value=f"{x}"
                self.hover_instance.label_y_value=f"{y}"
                
                if self.hover_instance.x_hover_pos>self.x+(self.axes.bbox.bounds[2] + self.axes.bbox.bounds[0])*self.crop_factor or \
                    self.hover_instance.x_hover_pos<self.x+self.axes.bbox.bounds[0]*self.crop_factor or \
                    self.hover_instance.y_hover_pos>self.y+(self.axes.bbox.bounds[1] + self.axes.bbox.bounds[3])*self.crop_factor or \
                    self.hover_instance.y_hover_pos<self.y+self.axes.bbox.bounds[1]*self.crop_factor:               
                    self.hover_instance.hover_outside_bound=True
                else:
                    self.hover_instance.hover_outside_bound=False 
            
            elif self.text:

                self.horizontal_line.set_ydata([y])
                self.vertical_line.set_xdata([x])
                self.text.set_text(f'{self.x_cursor_label}: {x:.3f} {self.y_cursor_label}: {y:.3f}')
                self._draw(self.axes)

        elif self.show_cursor:
            if self.hover_instance:
                self.hover_instance.x_hover_pos=self.x
                self.hover_instance.y_hover_pos=self.y      
                self.hover_instance.show_cursor=False
                self.x_hover_data = None
                self.y_hover_data = None
            elif self.text:            
                if self.text._text != ' ':
                    self.set_cross_hair_visible(False)
                    self._draw(self.axes)

    def update_hover(self):
        """ update hover on fast draw (if exist)"""
        if self.hover_instance:
            #update hover pos if needed
            if self.hover_instance.show_cursor and self.x_hover_data and self.y_hover_data:        
                xy_pos = self.axes.transData.transform([(self.x_hover_data,self.y_hover_data)]) 
                self.hover_instance.x_hover_pos=float(xy_pos[0][0])*self.crop_factor + self.x
                self.hover_instance.y_hover_pos=float(xy_pos[0][1])*self.crop_factor + self.y
     
                self.hover_instance.xmin_line = float(self.axes.bbox.bounds[0]) *self.crop_factor  + self.x
                self.hover_instance.xmax_line = float(self.axes.bbox.bounds[0] + self.axes.bbox.bounds[2]) *self.crop_factor + self.x            
                self.hover_instance.ymin_line = float(self.axes.bbox.bounds[1])*self.crop_factor  + self.y
                self.hover_instance.ymax_line = float(self.axes.bbox.bounds[1] + self.axes.bbox.bounds[3])*self.crop_factor
                
                if self.hover_instance.x_hover_pos>self.x+(self.axes.bbox.bounds[2] + self.axes.bbox.bounds[0])*self.crop_factor or \
                    self.hover_instance.x_hover_pos<self.x+self.axes.bbox.bounds[0]*self.crop_factor or \
                    self.hover_instance.y_hover_pos>self.y+(self.axes.bbox.bounds[1] + self.axes.bbox.bounds[3])*self.crop_factor or \
                    self.hover_instance.y_hover_pos<self.y+self.axes.bbox.bounds[1]*self.crop_factor:               
                    self.hover_instance.hover_outside_bound=True
                else:
                    self.hover_instance.hover_outside_bound=False                
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
        
        trans = self.axes.transData.inverted()
        # xdata, ydata = trans.transform_point((event.x-pos_x, event.y-pos_y)) 
        xdata, ydata = trans.transform_point(((event.x-pos_x) / self.crop_factor, (event.y-pos_y) / self.crop_factor))

        xleft,xright=self.axes.get_xlim()
        ybottom,ytop=self.axes.get_ylim()
        
        xmax = max(xleft,xright)
        xmin = min(xleft,xright)
        ymax = max(ybottom,ytop)
        ymin = min(ybottom,ytop)
        
        #check inverted data
        inverted_x = False
        if xleft>xright:
            inverted_x=True
        inverted_y = False
        if ybottom>ytop:
            inverted_y=True        

        # x0data, y0data = trans.transform_point((x0-pos_x, y0-pos_y)) 
        x0data, y0data = trans.transform_point(((x0-pos_x) / self.crop_factor, (y0-pos_y) / self.crop_factor))
         
        if x0data>xmax or x0data<xmin or y0data>ymax or y0data<ymin:
            return

        if xdata<xmin:
            x1_min = self.axes.transData.transform([(xmin,ymin)])
            if (x1<x0 and not inverted_x) or (x1>x0 and inverted_x):
                x1=x1_min[0][0]*self.crop_factor+pos_x
            else:
                x0=x1_min[0][0]*self.crop_factor

        if xdata>xmax:
            x0_max = self.axes.transData.transform([(xmax,ymin)])
            if (x1>x0 and not inverted_x) or (x1<x0 and inverted_x):
                x1=x0_max[0][0]*self.crop_factor+pos_x 
            else:
                x0=x0_max[0][0] *self.crop_factor                 

        if ydata<ymin:
            y1_min = self.axes.transData.transform([(xmin,ymin)])
            if (y1<y0 and not inverted_y) or (y1>y0 and inverted_y):
                y1=y1_min[0][1]*self.crop_factor+pos_y
            else:
                y0=y1_min[0][1]*self.crop_factor+pos_y

        if ydata>ymax:
            y0_max = self.axes.transData.transform([(xmax,ymax)])
            if (y1>y0 and not inverted_y) or (y1<y0 and inverted_y):
                y1=y0_max[0][1]*self.crop_factor+pos_y
            else:
                y0=y0_max[0][1]*self.crop_factor+pos_y
                
        if abs(x1-x0)<dp(20) and abs(y1-y0)>self.minzoom:
            self.pos_x_rect_ver=x0
            self.pos_y_rect_ver=y0   
            
            x1_min = self.axes.transData.transform([(xmin,ymin)])
            x0=x1_min[0][0]*self.crop_factor+pos_x

            x0_max = self.axes.transData.transform([(xmax,ymin)])
            x1=x0_max[0][0]*self.crop_factor+pos_x

            self._alpha_ver=1
            self._alpha_hor=0
                
        elif abs(y1-y0)<dp(20) and abs(x1-x0)>self.minzoom:
            self.pos_x_rect_hor=x0
            self.pos_y_rect_hor=y0  

            y1_min = self.axes.transData.transform([(xmin,ymin)])
            y0=y1_min[0][1]*self.crop_factor+pos_y
             
            y0_max = self.axes.transData.transform([(xmax,ymax)])
            y1=y0_max[0][1]*self.crop_factor+pos_y         

            self._alpha_hor=1
            self._alpha_ver=0
                        
        else:
            self._alpha_hor=0   
            self._alpha_ver=0

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
        
    def update_lim(self):
        """ update axis lim if zoombox is used"""
        ax=self.axes

        self.do_update=False
        
        #check if inverted axis
        xleft,xright=self.axes.get_xlim()
        ybottom,ytop=self.axes.get_ylim()
        
        if xright>xleft:
            ax.set_xlim(left=min(self.x0_box,self.x1_box),right=max(self.x0_box,self.x1_box))
        else:
            ax.set_xlim(right=min(self.x0_box,self.x1_box),left=max(self.x0_box,self.x1_box))
        if ytop>ybottom:
            ax.set_ylim(bottom=min(self.y0_box,self.y1_box),top=max(self.y0_box,self.y1_box))
        else:
            ax.set_ylim(top=min(self.y0_box,self.y1_box),bottom=max(self.y0_box,self.y1_box))

    def reset_box(self):
        """ reset zoombox and apply zoombox limit if zoombox option if selected"""
        if min(abs(self._box_size[0]),abs(self._box_size[1]))>self.minzoom:
            trans = self.axes.transData.inverted()
            self.x0_box, self.y0_box = trans.transform_point(((self._box_pos[0]-self.pos[0])/ self.crop_factor, (self._box_pos[1]-self.pos[1])/ self.crop_factor)) 
            self.x1_box, self.y1_box = trans.transform_point(((self._box_size[0]+self._box_pos[0]-self.pos[0])/ self.crop_factor, (self._box_size[1]+self._box_pos[1]-self.pos[1])/ self.crop_factor))
            self.do_update=True
            
        self._box_size = 0, 0
        self._box_pos = 0, 0
        self._alpha_box=0

        self._pos_x_rect_hor = 0
        self._pos_y_rect_hor = 0
        self._pos_x_rect_ver = 0
        self._pos_y_rect_ver = 0 
        self._alpha_hor=0 
        self._alpha_ver=0
        self.invert_rect_hor = False
        self.invert_rect_ver = False

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

    def clear(self):
        self.get_renderer().clear()


Builder.load_string('''
<MatplotFigureCropFactor>
            
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
                
    canvas.after:            
        #horizontal rectangle left
		Color:
			rgba:0, 0, 0, self._alpha_hor
		Line:
			width: dp(1)
			rectangle:
				(self.pos_x_rect_hor+dp(1) if root.invert_rect_ver \
                 else self.pos_x_rect_hor-dp(4),self.pos_y_rect_hor-dp(20), dp(4),dp(40))            

        #horizontal rectangle right
		Color:
			rgba:0, 0, 0, self._alpha_hor
		Line:
			width: dp(1)
			rectangle:
				(self.pos_x_rect_hor-dp(4)+self._box_size[0] if root.invert_rect_ver \
                 else self.pos_x_rect_hor+dp(1)+self._box_size[0], self.pos_y_rect_hor-dp(20), dp(4),dp(40))             

        #vertical rectangle bottom
		Color:
			rgba:0, 0, 0, self._alpha_ver
		Line:
			width: dp(1)
			rectangle:
				(self.pos_x_rect_ver-dp(20),self.pos_y_rect_ver+dp(1) if root.invert_rect_hor else \
                 self.pos_y_rect_ver-dp(4), dp(40),dp(4))            

        #vertical rectangle top
		Color:
			rgba:0, 0, 0, self._alpha_ver
		Line:
			width: dp(1)
			rectangle:
				(self.pos_x_rect_ver-dp(20),self.pos_y_rect_ver-dp(4)+self._box_size[1] \
                 if root.invert_rect_hor else self.pos_y_rect_ver+dp(1)+self._box_size[1], \
                 dp(40),dp(4))            
''')
FigureCanvas = _FigureCanvas
