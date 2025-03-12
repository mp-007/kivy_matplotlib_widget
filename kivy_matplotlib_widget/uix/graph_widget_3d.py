""" MatplotFigure3D for matplotlib 3D graph
"""

import math

import matplotlib
matplotlib.use('Agg')
from kivy.graphics.texture import Texture
from kivy.graphics.transformation import Matrix
from kivy.lang import Builder
from kivy.properties import AliasProperty,ObjectProperty, ListProperty, BooleanProperty, BoundedNumericProperty, AliasProperty, \
    NumericProperty,StringProperty,ColorProperty
from kivy.uix.widget import Widget
from kivy.vector import Vector
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.transforms import Bbox
from matplotlib.backend_bases import ResizeEvent
from matplotlib.backend_bases import MouseEvent
from kivy.metrics import dp
from kivy_matplotlib_widget.tools.cursors import cursor

import numpy as np
import matplotlib.transforms as mtransforms
from mpl_toolkits import mplot3d
from weakref import WeakKeyDictionary
from matplotlib import cbook

from kivy.uix.scatter import Scatter
from kivy.graphics.transformation import Matrix
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager
import time

def line2d_seg_dist(p1, p2, p0):
    """distance(s) from line defined by p1 - p2 to point(s) p0

    p0[0] = x(s)
    p0[1] = y(s)

    intersection point p = p1 + u*(p2-p1)
    and intersection point lies within segment if u is between 0 and 1
    """

    x21 = p2[0] - p1[0]
    y21 = p2[1] - p1[1]
    x01 = np.asarray(p0[0]) - p1[0]
    y01 = np.asarray(p0[1]) - p1[1]

    u = (x01*x21 + y01*y21) / (x21**2 + y21**2)
    u = np.clip(u, 0, 1)
    d = np.hypot(x01 - u*x21, y01 - u*y21)

    return d

def get_xyz_mouse_click(event, ax):
    """
    Get coordinates clicked by user
    """
    if ax.M is None:
        return {}

    xd, yd = event.xdata, event.ydata
    p = (xd, yd)
    edges = ax.tunit_edges()
    ldists = [(line2d_seg_dist(p0, p1, p), i) for \
                i, (p0, p1) in enumerate(edges)]
    ldists.sort()

    # nearest edge
    edgei = ldists[0][1]

    p0, p1 = edges[edgei]

    # scale the z value to match
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    d0 = np.hypot(x0-xd, y0-yd)
    d1 = np.hypot(x1-xd, y1-yd)
    dt = d0+d1
    z = d1/dt * z0 + d0/dt * z1

    x, y, z = mplot3d.proj3d.inv_transform(xd, yd, z, ax.M)
    return x, y, z

class MatplotlibEvent:
    x:None
    y:None
    pickradius:None
    inaxes:None
    projection:False
    compare_xdata:False

class MatplotFigure3D(ScatterLayout):
    """Widget to show a matplotlib figure in kivy.
    The figure is rendered internally in an AGG backend then
    the rgba data is obtained and blitted into a kivy texture.
    """

    cursor_cls=None
    pickradius = NumericProperty(dp(50))
    projection = BooleanProperty(False)
    myevent = MatplotlibEvent()
    figure = ObjectProperty(None)
    _box_pos = ListProperty([0, 0])
    _box_size = ListProperty([0, 0])
    _img_texture = ObjectProperty(None)
    _alpha_box = NumericProperty(0)   
    _bitmap = None
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
    move_lock = False
    scale_lock_left = False
    scale_lock_right = False
    scale_lock_top = False
    scale_lock_bottom = False
    center_graph = ListProperty([0, 0])
    cursor_label=None
    max_hover_rate =  NumericProperty(None,allownone=True) 
    last_hover_time=None 
    cursor_alpha =  NumericProperty(0.0)
    
    default_dpi=None
    crop_factor = NumericProperty(1.0)     
    cursor_size=NumericProperty("10dp")
    matplot_figure_layout = ObjectProperty(None) 

    def on_figure(self, obj, value):
        if self.default_dpi is None:
            #get default matplotlib figure dpi
            self.default_dpi = self.figure.get_dpi()
        self.figcanvas = _FigureCanvas(self.figure, self)
        self.figcanvas._isDrawn = False
        l, b, w, h = self.figure.bbox.bounds
        w = int(math.ceil(w))
        h = int(math.ceil(h))
        self.width = w
        self.height = h

        # Texture
        self._img_texture = Texture.create(size=(w, h))
        
        if self.matplot_figure_layout:
        
            self.cursor = self.figure.axes[0].scatter([0], [0], [0], marker="s",color="k", s=100,alpha=0)
            self.cursor_cls = cursor(self.figure,remove_artists=[self.cursor])

            self.cursor_label = CursorInfo()
            self.cursor_label.figure=self.figure
            self.cursor_label.xmin_line = self.x + dp(20)
            self.cursor_label.ymax_line = self.y +  h - dp(48)
            self.matplot_figure_layout.parent.add_widget(self.cursor_label)
          

    def __init__(self, **kwargs):
        super(MatplotFigure3D, self).__init__(**kwargs)
        
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
        self.touch_mode='rotate'
        self.hover_on = False
        self.xsorted = True #to manage x sorted data (if numpy is used)

        #zoom box coordonnate
        self.x0_box = None
        self.y0_box = None
        self.x1_box = None
        self.y1_box = None

        if hasattr(cbook,'_Stack'):
            #manage matplotlib version with no Stack (replace by _Stack)
            self._nav_stack = cbook._Stack()
        else:
            self._nav_stack = cbook.Stack()          
        self.set_history_buttons() 
        
        #clear touches on touch up
        self._touches = []
        self._last_touch_pos = {}
              
        self.bind(size=self._onSize)

    def on_crop_factor(self, obj, value):
        # return
        if self.figure:
            if self.default_dpi is None:
                #get default matplotlib figure dpi
                self.default_dpi = self.figure.get_dpi()
    
            self.figure.dpi = self.default_dpi / value
            
            self.figcanvas.draw()

            
    def _get_scale(self):
        p1 = Vector(*self.to_parent(0, 0))
        p2 = Vector(*self.to_parent(1, 0))
        scale = p1.distance(p2)

        # XXX float calculation are not accurate, and then, scale can be
        # thrown again even with only the position change. So to
        # prevent anything wrong with scale, just avoid to dispatch it
        # if the scale "visually" didn't change. #947
        # Remove this ugly hack when we'll be Python 3 only.
        if hasattr(self, '_scale_p'):
            if str(scale) == str(self._scale_p):
                return self._scale_p

        self._scale_p = scale
        return scale

    def _set_scale(self, scale):
        rescale = scale * 1.0 / self.scale
        
        #update center
        new_center = self.parent.to_local(*self.parent.center)
        self.apply_transform(Matrix().scale(rescale, rescale, rescale),
                             post_multiply=True,
                             anchor=(new_center[0]/2/scale,new_center[1]/2/scale))

    scale = AliasProperty(_get_scale, _set_scale, bind=('x', 'y', 'transform'))

    def set_custom_label_widget(self,custom_widget):
        self.cursor_label = custom_widget
        
        
    def home(self, *args):
        """
        Restore the original view.

        For convenience of being directly connected as a GUI callback, which
        often get passed additional parameters, this method accepts arbitrary
        parameters, but does not use them.
        """
        ax=self.figure.axes[0]
        ax.view_init(ax.initial_elev, ax.initial_azim, ax.initial_roll)
        self._nav_stack.home()
        self.set_history_buttons()
        self._update_view()
        self.figure.axes[0].autoscale()
        if self.crop_factor!=1.0:
            self.crop_factor=1.0
        else:
            self.figcanvas.draw()
        self.scale=1.0
        self.pos=(0,0)
        if self.cursor_alpha == 1.0:
            self.recalcul_cursor()
        
    def push_current(self):
       """Push the current view limits and position onto the stack."""
       self._nav_stack.push(
           WeakKeyDictionary(
               {ax: (ax._get_view(),
                     # Store both the original and modified positions.
                     (ax.get_position(True).frozen(),
                      ax.get_position().frozen()))
                for ax in self.figure.axes}))
       self.set_history_buttons()       

    def update(self):
        """Reset the Axes stack."""
        self._nav_stack.clear()
        self.set_history_buttons()
        
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
        self.figcanvas.draw()

    def set_history_buttons(self):
        """Enable or disable the back/forward button."""        
        

    def reset_touch(self) -> None:
        """ reset touch
        
        Return:
            None
        """
        self._touches = []
        self._last_touch_pos = {}
    
    def transform_with_touch(self, touch):
        changed = False

        # just do a simple one finger drag
        if len(self._touches) == self.translation_touches:
            # _last_touch_pos has last pos in correct parent space,
            # just like incoming touch
            dx = (touch.x - self._last_touch_pos[touch][0]) \
                 * self.do_translation_x
            dy = (touch.y  - self._last_touch_pos[touch][1]) \
                 * self.do_translation_y
            dx = dx / self.translation_touches
            dy = dy / self.translation_touches
            
            scale_x = self.bbox[1][0]/self.size[0]
            scale_y = self.bbox[1][1]/self.size[1]
            if scale_x>1.0:
                scale_x = scale_x**0.5
                scale_y = scale_y**0.5
            elif scale_y<1.0:
                scale_x = scale_x**0.5
                scale_y = scale_y**0.5

            
            
            self.apply_transform(Matrix().translate(dx/2/scale_x, dy/2/scale_y, 0))
            changed = True
    
            if self.cursor_alpha == 1.0:
                self.recalcul_cursor()
            
        if len(self._touches) == 1:#
            return changed
        
        # we have more than one touch... list of last known pos
        points = [Vector(self._last_touch_pos[t]) for t in self._touches
                  if t is not touch]
        # add current touch last
        points.append(Vector(touch.pos))

        # we only want to transform if the touch is part of the two touches
        # farthest apart! So first we find anchor, the point to transform
        # around as another touch farthest away from current touch's pos
        anchor = max(points[:-1], key=lambda p: p.distance(touch.pos))

        # now we find the touch farthest away from anchor, if its not the
        # same as touch. Touch is not one of the two touches used to transform
        farthest = max(points, key=anchor.distance)
        if farthest is not points[-1]:
            return changed

        # ok, so we have touch, and anchor, so we can actually compute the
        # transformation
        old_line = Vector(*touch.ppos) - anchor
        new_line = Vector(*touch.pos) - anchor
        if not old_line.length():  # div by zero
            return changed

        if self.do_scale:
            scale = old_line.length() / new_line.length()
            new_scale = scale * self.scale
            if new_scale < self.scale_min:
                scale = self.scale_min / self.scale
            elif new_scale > self.scale_max:
                scale = self.scale_max / self.scale
                
            if scale<1.0:
                ## zoom in
                if self.scale < 5:
                    self.scale = self.scale /scale
                    
                    self.crop_factor = 1/self.scale

            else:
                ## zoom out
                if self.scale > 0.6:
                    self.scale = self.scale /scale
                    
                    self.crop_factor = 1/self.scale
                    
            if self.cursor_alpha == 1.0:
                self.recalcul_cursor()
            changed = True

        return changed
    


    def _draw_bitmap(self):
        """ draw bitmap method. based on kivy scatter method"""
        if self._bitmap is None:
            print("No bitmap!")
            return
        self._img_texture = Texture.create(size=(self.bt_w, self.bt_h))
        self._img_texture.blit_buffer(
            bytes(self._bitmap), colorfmt="rgba", bufferfmt='ubyte')
        self._img_texture.flip_vertical()

    def transform_with_touch2(self, event):
        """ manage touch behaviour. based on kivy scatter method"""
        # just do a simple one finger drag
        changed = False

        if len(self._touches) == self.translation_touches:
            if self.touch_mode=='pan':
                ax=self.figure.axes[0]
                # Start the pan event with pixel coordinates
                px, py = ax.transData.transform([ax._sx, ax._sy])
                ax.start_pan(px, py, 2)
                # pan view (takes pixel coordinate input)
                ax.drag_pan(2, None, event.x, event.y)
                ax.end_pan()
                
                # Store the event coordinates for the next time through.
                # ax._sx, ax._sy = x, y
                trans = ax.transData.inverted()
                xdata, ydata = trans.transform_point((event.x, event.y))
                ax._sx, ax._sy = xdata, ydata
                # Always request a draw update at the end of interaction
                # ax.get_figure(root=True).canvas.draw_idle()
                self.figcanvas.draw()
                if self.cursor_alpha == 1.0:
                    self.recalcul_cursor()
                
            changed = True

        #note: avoid zoom in/out on touch mode zoombox
        if len(self._touches) == 1:#
            return changed
        
        # we have more than one touch... list of last known pos
        points = [Vector(self._last_touch_pos[t]) for t in self._touches
                  if t is not event]
        # add current touch last
        points.append(Vector(event.pos))

        # we only want to transform if the touch is part of the two touches
        # farthest apart! So first we find anchor, the point to transform
        # around as another touch farthest away from current touch's pos
        anchor = max(points[:-1], key=lambda p: p.distance(event.pos))

        # now we find the touch farthest away from anchor, if its not the
        # same as touch. Touch is not one of the two touches used to transform
        farthest = max(points, key=anchor.distance)
        if farthest is not points[-1]:
            return changed

        # ok, so we have touch, and anchor, so we can actually compute the
        # transformation
        old_line = Vector(*event.ppos) - anchor
        new_line = Vector(*event.pos) - anchor
        if not old_line.length():  # div by zero
            return changed

        if self.do_scale:
            scale = old_line.length() / new_line.length()
            new_scale = scale * self.scale
            if new_scale < self.scale_min:
                scale = self.scale_min / self.scale
            elif new_scale > self.scale_max:
                scale = self.scale_max / self.scale
                
            ax=self.figure.axes[0]
            ax._scale_axis_limits(scale, scale, scale)
            self.figcanvas.draw()
            if self.cursor_alpha == 1.0:
                self.recalcul_cursor()

            changed = True
        return changed

    def on_touch_down(self, touch):
        """ Manage Mouse/touch press """
        x, y = touch.x, touch.y
        self.prev_x = touch.x
        self.prev_y = touch.y
        
        if self.collide_point(x, y):
            # real_x, real_y = x - self.pos[0], y - self.pos[1]
            # self.figcanvas.button_press_event(x, real_y, 1, guiEvent=event)
            if touch.is_mouse_scrolling:
                
                if self.touch_mode == 'figure_zoom_pan':
                    
                    if touch.button == 'scrolldown':
                        ## zoom in
                        if self.scale < 5:
                            self.scale = self.scale * 1.1
                            
                            self.crop_factor = 1/self.scale
    
                    elif touch.button == 'scrollup':
                        ## zoom out
                        if self.scale > 0.6:
                            self.scale = self.scale * 0.8
                            
                            self.crop_factor = 1/self.scale

                    if self.cursor_alpha == 1.0:
                        self.recalcul_cursor()

                else:
                    if touch.button == 'scrollup':
                        ## zoom in
                        scale_factor = 1.1
    
                    elif touch.button == 'scrolldown':
                        ## zoom out
                        scale_factor = 0.8
                    ax=self.figure.axes[0]
                    ax._scale_axis_limits(scale_factor, scale_factor, scale_factor)
                    self.figcanvas.draw()
                    if self.cursor_alpha == 1.0:
                        self.recalcul_cursor()
            
            elif self.touch_mode == 'pan':
                ax=self.figure.axes[0]
                #transform kivy x,y touch event to x,y data
                trans = ax.transData.inverted()
                xdata, ydata = trans.transform_point((touch.x, touch.y))
                ax._sx, ax._sy = xdata, ydata

            else:
                # real_x, real_y = x - self.pos[0], y - self.pos[1]
                x = (touch.x) / self.crop_factor
                real_y = (touch.y) / self.crop_factor
                
                self.figcanvas._button = 1
                s = 'button_press_event'
                mouseevent = MouseEvent(s, self.figcanvas, x, real_y, 1, self.figcanvas._key,
                                    dblclick=False, guiEvent=touch)
                self.figcanvas.callbacks.process(s, mouseevent) 
                
                
        # if the touch isnt on the widget we do nothing
        if not self.do_collide_after_children:
            if not self.collide_point(x, y):
                return False

        # let the child widgets handle the event if they want
        touch.push()
        touch.apply_transform_2d(self.to_local)
        if super(Scatter, self).on_touch_down(touch):
            # ensure children don't have to do it themselves
            if 'multitouch_sim' in touch.profile:
                touch.multitouch_sim = True
            touch.pop()
            self._bring_to_front(touch)
            # return True

            return False
        touch.pop()

        # if our child didn't do anything, and if we don't have any active
        # interaction control, then don't accept the touch.
        if not self.do_translation_x and \
                not self.do_translation_y and \
                not self.do_rotation and \
                not self.do_scale:
            return False

        if self.do_collide_after_children:
            if not self.collide_point(x, y):
                return False

        if 'multitouch_sim' in touch.profile:
            touch.multitouch_sim = True
        # grab the touch so we get all it later move events for sure
        self._bring_to_front(touch)
        touch.grab(self)
        self._touches.append(touch)
        self._last_touch_pos[touch] = (touch.pos[0],
                                       touch.pos[1])

        # return True 
        return False                  

    def on_touch_move(self, event):
        """ Mouse move while pressed """

        x, y = event.x, event.y
        if self.collide_point(x, y):

            real_x, real_y = x - self.pos[0], y - self.pos[1]
            # self.figcanvas.motion_notify_event(x, real_y, guiEvent=event)
            if event.is_mouse_scrolling:
                pass
                
            elif self.touch_mode == 'figure_zoom_pan':
                
                touch =event
                # let the child widgets handle the event if they want
                if self.collide_point(x, y) and not touch.grab_current == self:
                    touch.push()
                    touch.apply_transform_2d(self.to_local)
                    if super(MatplotFigure3D, self).on_touch_move(touch):
                        touch.pop()
                        return True
                    touch.pop()
        
                # rotate/scale/translate
                if touch in self._touches and touch.grab_current == self:
                    self.transform_with_touch(touch)
                    self._last_touch_pos[touch] = (touch.pos[0],
                                                   touch.pos[1])
        
                # stop propagating if its within our bounds
                if self.collide_point(x, y):
                    return True                
                
                
            elif self.touch_mode == 'cursor':
                if self.cursor_label is None:
                    return
                #trick to improve app fps (use for big data)
                if self.max_hover_rate is not None:

                    if self.last_hover_time is None:
                        self.last_hover_time = time.time()
                    elif time.time() - self.last_hover_time < self.max_hover_rate:
                        return
                    else:
                        self.last_hover_time=None

                self.myevent.x=event.x - self.pos[0] - self.bbox[0][0]
                self.myevent.y=event.y - self.pos[1]- self.bbox[0][1]

                if self.scale != 1.0:

                    self.myevent.x=event.x/self.scale - self.pos[0]/self.scale - self.bbox[0][0]
                    self.myevent.y=event.y/self.scale - self.pos[1]/self.scale- self.bbox[0][1]

                self.myevent.x=self.myevent.x / self.crop_factor
                self.myevent.y=self.myevent.y / self.crop_factor
                self.myevent.inaxes=self.figure.canvas.inaxes((self.myevent.x,
                                                              self.myevent.y))
                self.myevent.pickradius=self.pickradius
                self.myevent.projection=self.projection
                self.myevent.compare_xdata=False
                #find closest artist from kivy event
                sel = self.cursor_cls.xy_event(self.myevent) 
                
                if not sel:
                    self.cursor_alpha = 0.0

                else:
    
                    self.myevent.xdata = sel.target[0]    
                    self.myevent.ydata = sel.target[1]  
                    try:
                        if hasattr(sel.artist,'get_data_3d'): #3d line
                            result = [sel.artist.get_data_3d()[0][sel.index],
                                      sel.artist.get_data_3d()[1][sel.index],
                                      sel.artist.get_data_3d()[2][sel.index]] 
                            
                        elif hasattr(sel.artist,'_offsets3d'): #scatter
                            result = [sel.artist._offsets3d[0].data[sel.index],
                                      sel.artist._offsets3d[1].data[sel.index],
                                      sel.artist._offsets3d[2][sel.index]]
                        else: #other z is a projectio. so it can not reflrct a real value
                            result = get_xyz_mouse_click(self.myevent, self.figure.axes[0])
                    except:
                        result = get_xyz_mouse_click(self.myevent, self.figure.axes[0])

                    self.cursor_alpha = 1.0
                    
                    ax=self.figure.axes[0]
                    
                    self.last_x=result[0]
                    self.last_y=result[1]
                    self.last_z=result[2]
                    
                    x = ax.xaxis.get_major_formatter().format_data_short(result[0])
                    y = ax.yaxis.get_major_formatter().format_data_short(result[1])
                    z = ax.yaxis.get_major_formatter().format_data_short(result[2])
                    # self.text.set_text(f"x={x}, y={y}, z={z}")
                    self.cursor_label.label_x_value = f"{x}"
                    self.cursor_label.label_y_value = f"{y}"
                    self.cursor_label.label_z_value = f"{z}"
                    
                    self.recalcul_cursor()

            elif self.touch_mode == 'pan':
                touch =event
                # let the child widgets handle the event if they want
                if self.collide_point(x, y) and not touch.grab_current == self:
                    touch.push()
                    touch.apply_transform_2d(self.to_local)
                    if super(MatplotFigure3D, self).on_touch_move(touch):
                        touch.pop()
                        return True
                    touch.pop()
        
                # rotate/scale/translate
                if touch in self._touches and touch.grab_current == self:
                    self.transform_with_touch2(touch)
                    self._last_touch_pos[touch] = (touch.pos[0],
                                                   touch.pos[1])
        
                # stop propagating if its within our bounds
                if self.collide_point(x, y):
                    return True   

            elif self.touch_mode == 'zoom':
                ax=self.figure.axes[0]                    
            else:

                x = (event.x) / self.crop_factor
                real_y = (event.y - self.pos[1]) / self.crop_factor
                y = (event.y) / self.crop_factor
                
                self.figcanvas._lastx, self.figcanvas._lasty = x, real_y
                
                s = 'motion_notify_event'
                event = MouseEvent(s, self.figcanvas, x, y, self.figcanvas._button, self.figcanvas._key,
                                    guiEvent=None)
                event.inaxes = self.figure.axes[0]
                self.figcanvas.callbacks.process(s, event)
                
                if self.cursor_alpha == 1.0:
                    self.recalcul_cursor()

    def recalcul_cursor(self):
        ax=self.figure.axes[0]
        x, y, z = mplot3d.proj3d.transform(self.last_x, self.last_y, self.last_z, ax.M)
        xy_pos = ax.transData.transform([(x,y)]) 
        self.center_graph = (float(xy_pos[0][0])*self.crop_factor + self.x  ,float(xy_pos[0][1])*self.crop_factor + self.y)
        
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
        self.figure.set_size_inches(winch / self.crop_factor, hinch / self.crop_factor)
        
        s = 'resize_event'
        event = ResizeEvent(s, self.figcanvas)
        self.figcanvas.callbacks.process(s, event)
        self.figcanvas.draw_idle()   
        
        self.figcanvas.draw()  
        
        l, b, w, h = self.figure.bbox.bounds

        if self.cursor_label and self.figure and self.cursor_label is not None:
            self.cursor_label.xmin_line = self.parent.x + dp(20)
            self.cursor_label.ymax_line = self.parent.y +  int(math.ceil(h))*self.crop_factor  - dp(48)

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
        
class MatplotFigure3DLayout(ScreenManager):
    """This handle figure zoom and pan inside the widget. 
    Cursor is also not rescale when zooming
    """

    pickradius = NumericProperty(dp(50))
    projection = BooleanProperty(False)
    figure_wgt = ObjectProperty(None)
    max_hover_rate =  NumericProperty(None,allownone=True) 
    crop_factor = NumericProperty(1.0)     
    cursor_size=NumericProperty("10dp") 

    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs) 
        
class CursorInfo(FloatLayout):
    figure_wgt = ObjectProperty(None)
    xmin_line = NumericProperty(1)
    ymax_line = NumericProperty(1)     
    show_cursor = BooleanProperty(False)
    label_x = StringProperty('x')  
    label_y = StringProperty('y')  
    label_z = StringProperty('z') 
    label_x_value = StringProperty('')  
    label_y_value = StringProperty('') 
    label_z_value = StringProperty('') 
    text_color=ColorProperty([0,0,0,1])
    text_font=StringProperty("Roboto")
    text_size = NumericProperty(dp(14))
    background_color=ColorProperty([1,1,1,1])
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)      

from kivy.factory import Factory

Factory.register('MatplotFigure3D', MatplotFigure3D)

Builder.load_string('''                            
<MatplotFigure3DLayout>
    figure_wgt : figure_wgt.__self__
    
    Screen:
        size: root.size
        pos: root.pos 
        BoxLayout:
            MatplotFigure3D:
                id:figure_wgt
                pickradius : root.pickradius
                projection : root.projection
                max_hover_rate : root.max_hover_rate 
                crop_factor : root.crop_factor
                cursor_size : root.cursor_size   
                matplot_figure_layout:root
                    
<MatplotFigure3D>
    canvas.before:
        Color:
            rgba: (1, 1, 1, 1)
        Rectangle:
            pos: self.pos
            size: self.size
            texture: self._img_texture
            

        Color:
            rgba: (0, 0, 0, self.cursor_alpha)
        Rectangle:
            pos: (self.center_graph[0]-root.cursor_size/2,self.center_graph[1]-root.cursor_size/2)
            size: root.cursor_size,root.cursor_size  
            
<CursorInfo>
    custom_color: [0,0,0,1] 
    size_hint: None, None
    height: dp(0.01)
    width: dp(0.01)
    
    BoxLayout:
        id:main_box
        x:root.xmin_line
        y: root.ymax_line + dp(4) 
        size_hint: None, None
        height: self.minimum_height
        width: 
            self.minimum_width + dp(12) if root.show_cursor \
            else dp(0.0001)
        orientation:'vertical'
        padding: 0,dp(4),0,dp(4)
        

        
        BoxLayout:
            size_hint:None,None
            width:label.texture_size[0] + dp(12)
            height:label.texture_size[1] + dp(12)
            canvas.before:            
                Color:
                    rgb: root.background_color
                    a:0.8
                Rectangle:
                    pos: self.pos
                    size: self.size            
            Label:
                id:label
                text: 
                    root.label_x + ': ' + root.label_x_value + \
                        '  ' + root.label_y + ': ' + root.label_y_value + \
                            '  ' + root.label_z + ': ' + root.label_z_value
                font_size:root.text_size
                font_name : root.text_font
                color: root.text_color
        
''')
