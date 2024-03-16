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
from matplotlib import cbook
from matplotlib.colors import to_hex
from matplotlib.backend_bases import ResizeEvent
from weakref import WeakKeyDictionary
from kivy.metrics import dp
import numpy as np
from kivy.utils import get_color_from_hex


class MatplotFigure(Widget):
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
    legend_instance = ObjectProperty(None, allownone=True)
    legend_do_scroll_x = BooleanProperty(True)
    legend_do_scroll_y = BooleanProperty(True)
    interactive_axis = BooleanProperty(False) 
    do_pan_x = BooleanProperty(True)
    do_pan_y = BooleanProperty(True)    
    do_zoom_x = BooleanProperty(True)
    do_zoom_y = BooleanProperty(True)  
    fast_draw = BooleanProperty(True) #True will don't draw axis
    xsorted = BooleanProperty(False) #to manage x sorted data
    minzoom = NumericProperty(dp(40))
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
    
    def on_figure(self, obj, value):
        self.figcanvas = _FigureCanvas(self.figure, self)
        self.figcanvas._isDrawn = False
        l, b, w, h = self.figure.bbox.bounds
        w = int(math.ceil(w))
        h = int(math.ceil(h))
        self.width = w
        self.height = h

        if self.figure.axes[0]:
            #add copy patch
            ax=self.figure.axes[0]
            patch_cpy=copy.copy(ax.patch)
            patch_cpy.set_visible(False)
            for pos in ['right', 'top', 'bottom', 'left']:
                ax.spines[pos].set_zorder(10)
            patch_cpy.set_zorder(9)
            self.background_patch_copy= ax.add_patch(patch_cpy)
            
            #set xmin axes attribute
            self.axes = self.figure.axes[0]
            
            #set default xmin/xmax and ymin/ymax
            self.xmin,self.xmax = self.axes.get_xlim()
            self.ymin,self.ymax = self.axes.get_ylim()
        
        if self.legend_instance:
            self.legend_instance.reset_legend()
            self.legend_instance=None
            
        if self.auto_cursor:
            self.register_lines(list(self.axes.lines))
            
        # Texture
        self._img_texture = Texture.create(size=(w, h))
        
        #close last figure in memory (avoid max figure warning)
        matplotlib.pyplot.close()

    def __init__(self, **kwargs):
        super(MatplotFigure, self).__init__(**kwargs)
        
        #figure info
        self.figure = None
        self.axes = None
        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None
        self.lines = []
        
        #option
        self.touch_mode='pan'
        self.hover_on = False
        self.cursor_xaxis_formatter=None #used matplotlib formatter to display x cursor value
        self.cursor_yaxis_formatter=None #used matplotlib formatter to display y cursor value

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

        #manage adjust x and y
        self.anchor_x = None
        self.anchor_y = None 
        
        #trick to manage wrong canvas size on first call (compare_hover)
        self.first_call_compare_hover=False
        
        #manage hover data
        self.x_hover_data = None
        self.y_hover_data = None
        
        #pan management
        self.first_touch_pan = None
        
        #manage show compare cursor on release
        self.show_compare_cursor = False
        
        #manage back and next event
        self._nav_stack = cbook.Stack()
        self.set_history_buttons()         
        
        self.bind(size=self._onSize)
      
    def transform_eval(self,x,axis):
        custom_transform=axis.get_transform()
        return custom_transform.transform_non_affine(np.array([x]))[0]
        
    def inv_transform_eval(self,x,axis):
        inv_custom_transform=axis.get_transform().inverted()
        return inv_custom_transform.transform_non_affine(np.array([x]))[0]
    
    def register_lines(self,lines:list) -> None:
        """ register lines method
        
        Args:
            lines (list): list of matplolib line class
            
        Return:
            None        
        """ 
        
        #create cross hair cusor
        self.horizontal_line = self.axes.axhline(color='k', lw=0.8, ls='--', visible=False)
        self.vertical_line = self.axes.axvline(color='k', lw=0.8, ls='--', visible=False)
        
        #register lines
        self.lines=lines
                
        #cursor text
        self.text = self.axes.text(1.0, 1.01, '', 
                                      transform=self.axes.transAxes,
                                      ha='right')

    def set_cross_hair_visible(self, visible:bool) -> None:
        """ set curcor visibility
        
        Args:
            visible (bool): make cursor visble or not
            
        Return:
            None
        
        """       
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        self.text.set_visible(visible)

    def hover(self, event) -> None:
        """ hover cursor method (cursor to nearest value)
        
        Args:
            event: touch kivy event
            
        Return:
            None
        
        """
           
        #if cursor is set -> hover is on
        if self.hover_on:

            #transform kivy x,y touch event to x,y data
            trans = self.axes.transData.inverted()
            xdata, ydata = trans.transform_point((event.x - self.pos[0], event.y - self.pos[1]))

            #loop all register lines and find closest x,y data for each valid line
            distance=[]
            good_line=[]
            good_index=[]
            for line in self.lines:
                #get only visible lines
                if line.get_visible():  
                    #get line x,y datas
                    self.x_cursor, self.y_cursor = line.get_data()
                    
                    #check if line is not empty
                    if len(self.x_cursor)!=0:                        
                        
                        #find closest data index from touch (x axis)
                        if self.xsorted:
                            index = min(np.searchsorted(self.x_cursor, xdata), len(self.y_cursor) - 1)
                            
                        else:
                            index = np.argsort(abs(self.x_cursor - xdata))[0]

                        #get x data from index
                        x = self.x_cursor[index]
                        
                        if self.compare_xdata:
                            y = self.y_cursor[index]
                            
                            #get distance between line and touch (in pixels)
                            ax=line.axes 
                            #left axis
                            xy_pixels_mouse = ax.transData.transform([(xdata,ydata)])
                            if np.ma.is_masked(x) or np.ma.is_masked(y) or np.isnan(x) or np.isnan(y):
                                distance.append(np.nan)
                            else:
                                xy_pixels = ax.transData.transform([(x,ydata)])
                                dx2 = (xy_pixels_mouse[0][0]-xy_pixels[0][0])
                                distance.append(abs(dx2))
                        else:    
                            
                            #find ydata corresponding to xdata
                            y = self.y_cursor[index]
                                                   
                            #get distance between line and touch (in pixels)
                            ax=line.axes 
                            #left axis
                            xy_pixels_mouse = ax.transData.transform([(xdata,ydata)])
                            if np.ma.is_masked(x) or np.ma.is_masked(y):
                                distance.append(np.nan)
                            else:
                                xy_pixels = ax.transData.transform([(x,y)])
                                dx2 = (xy_pixels_mouse[0][0]-xy_pixels[0][0])**2
                                dy2 = (xy_pixels_mouse[0][1]-xy_pixels[0][1])**2 
                                
                                #store distance
                                distance.append((dx2 + dy2)**0.5)
                        
                        #store all best lines and index
                        good_line.append(line)
                        good_index.append(index)
 
            #case if no good line
            if len(good_line)==0:
                return

            #if minimum distance if lower than 50 pixels, get line datas with 
            #minimum distance 
            if np.nanmin(distance)<dp(50):
                #index of minimum distance
                if self.compare_xdata:
                    if not self.hover_instance or not hasattr(self.hover_instance,'children_list'):
                        return
                    
                    idx_best_list = np.flatnonzero(np.array(distance) == np.nanmin(distance))
                    
                    #get datas from closest line
                    line=good_line[idx_best_list[0]]
                    self.x_cursor, self.y_cursor = line.get_data()
                    x = self.x_cursor[good_index[idx_best_list[0]]]
                    y = self.y_cursor[good_index[idx_best_list[0]]] 

                    xy_pos = ax.transData.transform([(x,y)]) 
                    self.x_hover_data = x
                    self.y_hover_data = y
                    self.hover_instance.x_hover_pos=float(xy_pos[0][0]) + self.x
                    self.hover_instance.y_hover_pos=float(xy_pos[0][1]) + self.y
                    self.hover_instance.y_touch_pos=float(xy_pixels[0][1]) + self.y
                    
                    if self.first_call_compare_hover:
                        self.hover_instance.show_cursor=True 
                    else:
                        self.first_call_compare_hover=True
                    
                    if len(idx_best_list)>0:
                        available_widget = self.hover_instance.children_list
                        nb_widget=len(available_widget)
                        index_list=list(range(nb_widget))
                        for i, current_idx_best in enumerate(idx_best_list):
                            if i > nb_widget-1:
                                break
                            else:
                                line=good_line[idx_best_list[i]]
                                line_label = line.get_label()
                                if line_label in self.hover_instance.children_names:
                                    index= self.hover_instance.children_names.index(line_label)                                   
                                    y_cursor = line.get_ydata()
                                    y = y_cursor[good_index[idx_best_list[i]]] 

                                    xy_pos = ax.transData.transform([(x,y)]) 
                                    pos_y=float(xy_pos[0][1]) + self.y
  
                                    if pos_y<self.y+self.axes.bbox.bounds[1] + self.axes.bbox.bounds[3] and \
                                        pos_y>self.y+self.axes.bbox.bounds[1]:
                                        available_widget[index].x_hover_pos=float(xy_pos[0][0]) + self.x
                                        available_widget[index].y_hover_pos=float(xy_pos[0][1]) + self.y
                                        available_widget[index].custom_color = get_color_from_hex(to_hex(line.get_color()))
                                        
                                        if self.cursor_yaxis_formatter:
                                            y = self.cursor_yaxis_formatter.format_data(y) 
                                        else:
                                            y = ax.yaxis.get_major_formatter().format_data_short(y)
                                        available_widget[index].label_y_value=f"{y}"
                                        available_widget[index].show_widget=True
                                        index_list.remove(index)
                                    
                        for ii in index_list:
                            available_widget[ii].show_widget=False

                        if self.cursor_xaxis_formatter:
                            x = self.cursor_xaxis_formatter.format_data(x) 
                        else:
                            x = ax.xaxis.get_major_formatter().format_data_short(x)
                            
                        self.hover_instance.label_x_value=f"{x}"
                        
                        if hasattr(self.hover_instance,'overlap_check'):
                            self.hover_instance.overlap_check()
                    
                        self.hover_instance.ymin_line = float(ax.bbox.bounds[1])  + self.y
                        self.hover_instance.ymax_line = float(ax.bbox.bounds[1] + ax.bbox.bounds[3])  + self.y
                        
                        if self.hover_instance.x_hover_pos>self.x+self.axes.bbox.bounds[2] + self.axes.bbox.bounds[0] or \
                            self.hover_instance.x_hover_pos<self.x+self.axes.bbox.bounds[0] or len(index_list)==nb_widget:              
                            self.hover_instance.hover_outside_bound=True                            
                        else:
                            self.hover_instance.hover_outside_bound=False                      
                        
                        return
                        
                
                else:
                    idx_best=np.nanargmin(distance)
                    
                    #get datas from closest line
                    line=good_line[idx_best]
                    self.x_cursor, self.y_cursor = line.get_data()
                    x = self.x_cursor[good_index[idx_best]]
                    y = self.y_cursor[good_index[idx_best]]  
                    
                    if not self.hover_instance:
                        self.set_cross_hair_visible(True)
                    
                    # update the cursor x,y data               
                    ax=line.axes
                    self.horizontal_line.set_ydata(y)
                    self.vertical_line.set_xdata(x)
    
                    #x y label
                    if self.hover_instance:                     
                        xy_pos = ax.transData.transform([(x,y)]) 
                        self.x_hover_data = x
                        self.y_hover_data = y
                        self.hover_instance.x_hover_pos=float(xy_pos[0][0]) + self.x
                        self.hover_instance.y_hover_pos=float(xy_pos[0][1]) + self.y
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
                
                        self.hover_instance.ymin_line = float(ax.bbox.bounds[1])  + self.y
                        self.hover_instance.ymax_line = float(ax.bbox.bounds[1] + ax.bbox.bounds[3])  + self.y
                        
                        self.hover_instance.custom_label = line.get_label()
                        self.hover_instance.custom_color = get_color_from_hex(to_hex(line.get_color()))
                        
                        if self.hover_instance.x_hover_pos>self.x+self.axes.bbox.bounds[2] + self.axes.bbox.bounds[0] or \
                            self.hover_instance.x_hover_pos<self.x+self.axes.bbox.bounds[0] or \
                            self.hover_instance.y_hover_pos>self.y+self.axes.bbox.bounds[1] + self.axes.bbox.bounds[3] or \
                            self.hover_instance.y_hover_pos<self.y+self.axes.bbox.bounds[1]:               
                            self.hover_instance.hover_outside_bound=True
                        else:
                            self.hover_instance.hover_outside_bound=False                      
                        
                        return
                    else:
                        if self.cursor_xaxis_formatter:
                            x = self.cursor_xaxis_formatter.format_data(x)
                        else:
                            x = ax.xaxis.get_major_formatter().format_data_short(x)
                        if self.cursor_yaxis_formatter:
                            y = self.cursor_yaxis_formatter.format_data(y) 
                        else:
                            y = ax.yaxis.get_major_formatter().format_data_short(y)
                        self.text.set_text(f"x={x}, y={y}")
    
                    #blit method (always use because same visual effect as draw)                  
                    if self.background is None:
                        self.set_cross_hair_visible(False)
                        self.axes.figure.canvas.draw_idle()
                        self.axes.figure.canvas.flush_events()                   
                        self.background = self.axes.figure.canvas.copy_from_bbox(self.axes.figure.bbox)
                        self.set_cross_hair_visible(True)  
    
                    self.axes.figure.canvas.restore_region(self.background)
                    self.axes.draw_artist(self.text)
    
                    self.axes.draw_artist(self.horizontal_line)
                    self.axes.draw_artist(self.vertical_line)  
    
                    #draw (blit method)
                    self.axes.figure.canvas.blit(self.axes.bbox)                 
                    self.axes.figure.canvas.flush_events()

            #if touch is too far, hide cross hair cursor
            else:
                self.set_cross_hair_visible(False)  
                if self.hover_instance:
                    self.hover_instance.x_hover_pos=self.x
                    self.hover_instance.y_hover_pos=self.y      
                    self.hover_instance.show_cursor=False
                    self.x_hover_data = None
                    self.y_hover_data = None

    def home(self) -> None:
        """ reset data axis
        
        Return:
            None
        """
        #do nothing is all min/max are not set
        if self.xmin is not None and \
            self.xmax is not None and \
            self.ymin is not None and \
            self.ymax is not None:
                
            ax = self.axes
            xleft,xright=ax.get_xlim()
            ybottom,ytop=ax.get_ylim() 
            
            #check inverted data
            inverted_x = False
            if xleft>xright:
                inverted_x=True
            inverted_y = False
            if ybottom>ytop:
                inverted_y=True         
            
            if inverted_x:
                ax.set_xlim(right=self.xmin,left=self.xmax)
            else:
                ax.set_xlim(left=self.xmin,right=self.xmax)
            if inverted_y:
                ax.set_ylim(top=self.ymin,bottom=self.ymax)
            else:
                ax.set_ylim(bottom=self.ymin,top=self.ymax)                              
    
            ax.figure.canvas.draw_idle()
            ax.figure.canvas.flush_events() 

    def back(self, *args):
        """
        Move back up the view lim stack.
        For convenience of being directly connected as a GUI callback, which
        often get passed additional parameters, this method accepts arbitrary
        parameters, but does not use them.
        """
        self._nav_stack.back()
        self.set_history_buttons()
        self._update_view()

    def forward(self, *args):
        """
        Move forward in the view lim stack.
        For convenience of being directly connected as a GUI callback, which
        often get passed additional parameters, this method accepts arbitrary
        parameters, but does not use them.
        """
        self._nav_stack.forward()
        self.set_history_buttons()
        self._update_view()
 
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
        self.figure.canvas.draw_idle() 
        self.figure.canvas.flush_events()

    def set_history_buttons(self):
        """Enable or disable the back/forward button."""

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

        # XXX float calculation are not accurate, and then, scale can be
        # throwed again even with only the position change. So to
        # prevent anything wrong with scale, just avoid to dispatch it
        # if the scale "visually" didn't change. #947
        # Remove this ugly hack when we'll be Python 3 only.
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
    '''Scale value of the scatter.

    :attr:`scale` is an :class:`~kivy.properties.AliasProperty` and defaults to
    1.0.
    '''

    def _draw_bitmap(self):
        """ draw bitmap method. based on kivy scatter method"""
        if self._bitmap is None:
            print("No bitmap!")
            return
        self._img_texture = Texture.create(size=(self.bt_w, self.bt_h))
        self._img_texture.blit_buffer(
            bytes(self._bitmap), colorfmt="rgba", bufferfmt='ubyte')
        self._img_texture.flip_vertical()
        
        self.update_hover()           
        

    def transform_with_touch(self, event):
        """ manage touch behaviour. based on kivy scatter method"""
        # just do a simple one finger drag
        changed = False

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
 
            elif self.touch_mode=='drag_legend':
                if self.legend_instance:
                    self.apply_drag_legend(self.axes, event)
            
            elif self.touch_mode=='zoombox':
                if self._nav_stack() is None:
                    self.push_current()                
                real_x, real_y = event.x - self.pos[0], event.y - self.pos[1]
                #in case x_init is not create
                if not hasattr(self,'x_init'):
                    self.x_init = event.x
                    self.y_init = real_y
                self.draw_box(event, self.x_init,self.y_init, event.x, real_y)
                
            #mode cursor
            elif self.touch_mode=='cursor':
                self.hover_on=True
                self.hover(event)
                
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

        if self.auto_zoom:
            v1 = Vector(0, 10)
            angle = v1.angle(new_line) + 180
            if angle<0+self.zoom_angle_detection or angle>360-self.zoom_angle_detection:
                self.do_zoom_x=False
                self.do_zoom_y=True
            elif angle>90-self.zoom_angle_detection and angle<90+self.zoom_angle_detection:
                self.do_zoom_x=True
                self.do_zoom_y=False           
            elif angle>180-self.zoom_angle_detection and angle<180+self.zoom_angle_detection:
                self.do_zoom_x=False
                self.do_zoom_y=True  
            elif angle>270-self.zoom_angle_detection and angle<270+self.zoom_angle_detection:
                self.do_zoom_x=True
                self.do_zoom_y=False            
            else:
                self.do_zoom_x=True
                self.do_zoom_y=True

        if self.do_scale:
            #            scale = new_line.length() / old_line.length()
            scale = old_line.length() / new_line.length()
            new_scale = scale * self.scale
            if new_scale < self.scale_min:
                scale = self.scale_min / self.scale
            elif new_scale > self.scale_max:
                scale = self.scale_max / self.scale
                
            self.apply_zoom(scale, self.axes, anchor=anchor,new_line=new_line)

            changed = True
        return changed

    def on_motion(self,*args):
        '''Kivy Event to trigger mouse event on motion
           `enter_notify_event`.
        '''
        if self._pressed or self.disabled:  # Do not process this event if there's a touch_move
            return
        pos = args[1]
        newcoord = self.to_widget(pos[0], pos[1])
        x = newcoord[0]
        y = newcoord[1]
        inside = self.collide_point(x,y)
        if inside: 

            # will receive all motion events.
            if self.figcanvas and self.hover_instance:
                #avoid in motion if touch is detected
                if not len(self._touches)==0:
                    return
                FakeEvent.x=x
                FakeEvent.y=y
                self.hover(FakeEvent)

    def on_touch_down(self, event):
        """ Manage Mouse/touch press """
        if self.disabled:
            return
        x, y = event.x, event.y

        if self.collide_point(x, y) and self.figure:
            self._pressed = True
            self.show_compare_cursor=False
            if self.legend_instance:
                if self.legend_instance.box.collide_point(x, y):
                    if self.touch_mode!='drag_legend':
                        return False   
                    else:
                        event.grab(self)
                        self._touches.append(event)
                        self._last_touch_pos[event] = event.pos
                        if len(self._touches)>1:
                            #new touch, reset background
                            self.background=None
                            
                        return True 
                       
            if event.is_mouse_scrolling:
                if not self.disable_mouse_scrolling:
                    ax = self.axes
                    ax = self.axes
                    self.zoom_factory(event, ax, base_scale=1.2)
                return True

            elif event.is_double_tap:
                if not self.disable_double_tap:
                    self.home()
                return True
                  
            else:
                if self.touch_mode=='cursor':
                    self.hover_on=True
                    self.hover(event)                
                elif self.touch_mode=='zoombox':
                    real_x, real_y = x - self.pos[0], y - self.pos[1]
                    self.x_init=x
                    self.y_init=real_y
                    self.draw_box(event, x, real_y, x, real_y) 

                elif self.touch_mode=='minmax':
                    self.min_max(event)
                    
                event.grab(self)
                self._touches.append(event)
                self._last_touch_pos[event] = event.pos
                if len(self._touches)>1:
                    #new touch, reset background
                    self.background=None
                    
                return True

        else:
            return False

    def on_touch_move(self, event):
        """ Manage Mouse/touch move while pressed """
        if self.disabled:
            return
        x, y = event.x, event.y

        if event.is_double_tap:
            if not self.disable_double_tap:
                self.home()               
            return True

        # scale/translate
        if event in self._touches and event.grab_current == self:

            if self.transform_with_touch(event):
                self.transform_with_touch(event)
            self._last_touch_pos[event] = event.pos

        # stop propagating if its within our bounds
        if self.collide_point(x, y):
            return True

    def on_touch_up(self, event):
        """ Manage Mouse/touch release """
        if self.disabled:
            return
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

    def apply_zoom(self, scale_factor, ax, anchor=(0, 0),new_line=None):
        """ zoom touch method """
                
        x = anchor[0]-self.pos[0]
        y = anchor[1]-self.pos[1]

        trans = ax.transData.inverted()
        xdata, ydata = trans.transform_point((x+new_line.x/2, y+new_line.y/2))        
        
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim() 

        scale=ax.get_xscale()
        yscale=ax.get_yscale()
        
        if scale == 'linear':
            old_min=cur_xlim[0]
            old_max=cur_xlim[1]

        else:
            min_=cur_xlim[0]
            max_=cur_xlim[1]            
            old_min = self.transform_eval(min_,ax.yaxis)
            xdata = self.transform_eval(xdata,ax.yaxis)
            old_max = self.transform_eval(max_,ax.yaxis)  

        if yscale == 'linear':
            yold_min=cur_ylim[0]
            yold_max=cur_ylim[1]

        else:
            ymin_=cur_ylim[0]
            ymax_=cur_ylim[1]            
            yold_min = self.transform_eval(ymin_,ax.yaxis)
            ydata = self.transform_eval(ydata,ax.yaxis)
            yold_max = self.transform_eval(ymax_,ax.yaxis)

        new_width = (old_max - old_min) * scale_factor
        new_height = (yold_max - yold_min) * scale_factor

        relx = (old_max - xdata) / (old_max - old_min)
        rely = (yold_max - ydata) / (yold_max - yold_min)

        if self.do_zoom_x:
            if scale == 'linear':
                ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * (relx)])
            else:
                new_min = xdata - new_width * (1 - relx)
                new_max = xdata + new_width * (relx)
                try:
                    new_min, new_max = self.inv_transform_eval(new_min,ax.yaxis), self.inv_transform_eval(new_max,ax.yaxis)
                except OverflowError:  # Limit case
                    new_min, new_max = min_, max_
                    if new_min <= 0. or new_max <= 0.:  # Limit case
                        new_min, new_max = min_, max_ 
                ax.set_xlim([new_min, new_max])
    
        if self.do_zoom_y:
            if yscale == 'linear':
                ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * (rely)])
            else:
                new_ymin = ydata - new_height * (1 - rely)
                new_ymax = ydata + new_height * (rely)
                try:
                    new_ymin, new_ymax = self.inv_transform_eval(new_ymin,ax.yaxis), self.inv_transform_eval(new_ymax,ax.yaxis)
                except OverflowError:  # Limit case
                    new_ymin, new_ymax = ymin_, ymax_
                    if new_ymin <= 0. or new_ymax <= 0.:  # Limit case
                        new_ymin, new_ymax = ymin_, ymax_ 
                ax.set_ylim([new_ymin, new_ymax]) 

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

            self.update_hover()
        else:
            ax.figure.canvas.draw_idle()
            ax.figure.canvas.flush_events()           

    def apply_pan(self, ax, event, mode='pan'):
        """ pan method """
        
        trans = ax.transData.inverted()
        xdata, ydata = trans.transform_point((event.x-self.pos[0], event.y-self.pos[1]))
        xpress, ypress = trans.transform_point((self._last_touch_pos[event][0]-self.pos[0], self._last_touch_pos[event][1]-self.pos[1]))
        
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
                            cur_xlim -= dx/2
                        else:
                            try:
                                cur_xlim = [self.inv_transform_eval((self.transform_eval(cur_xlim[0],ax.xaxis) - dx/2),ax.xaxis),
                                           self.inv_transform_eval((self.transform_eval(cur_xlim[1],ax.xaxis) - dx/2),ax.xaxis)]  
                            except (ValueError, OverflowError):
                                cur_xlim = cur_xlim  # Keep previous limits                                  
                        if inverted_x:
                            ax.set_xlim(cur_xlim[1],None)
                        else:
                            ax.set_xlim(None,cur_xlim[1])
                else:
                    if xdata< cur_xlim[1]:
                        if scale == 'linear':
                            cur_xlim -= dx/2
                        else:
                            try:
                                cur_xlim = [self.inv_transform_eval((self.transform_eval(cur_xlim[0],ax.xaxis) - dx/2),ax.xaxis),
                                           self.inv_transform_eval((self.transform_eval(cur_xlim[1],ax.xaxis) - dx/2),ax.xaxis)]  
                            except (ValueError, OverflowError):
                                cur_xlim = cur_xlim  # Keep previous limits  
                        if inverted_x:
                            ax.set_xlim(None,cur_xlim[0])
                        else:
                            ax.set_xlim(cur_xlim[0],None)
            else:
                if scale == 'linear':
                    cur_xlim -= dx/2
                else:
                    try:
                        cur_xlim = [self.inv_transform_eval((self.transform_eval(cur_xlim[0],ax.xaxis) - dx/2),ax.xaxis),
                                   self.inv_transform_eval((self.transform_eval(cur_xlim[1],ax.xaxis) - dx/2),ax.xaxis)]  
                    except (ValueError, OverflowError):
                        cur_xlim = cur_xlim  # Keep previous limits                   
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
                            cur_ylim -= dy/2 
                        
                        else:
                            try:
                                cur_ylim = [self.inv_transform_eval((self.transform_eval(cur_ylim[0],ax.yaxis) - dy/2),ax.yaxis),
                                           self.inv_transform_eval((self.transform_eval(cur_ylim[1],ax.yaxis) - dy/2),ax.yaxis)]
                            except (ValueError, OverflowError):
                                cur_ylim = cur_ylim  # Keep previous limits                        
                        
                        if inverted_y:
                            ax.set_ylim(cur_ylim[1],None)
                        else:
                            ax.set_ylim(None,cur_ylim[1])
                else:
                    if ydata< cur_ylim[1]:
                        if yscale == 'linear':
                            cur_ylim -= dy/2 
                        
                        else:
                            try:
                                cur_ylim = [self.inv_transform_eval((self.transform_eval(cur_ylim[0],ax.yaxis) - dy/2),ax.yaxis),
                                           self.inv_transform_eval((self.transform_eval(cur_ylim[1],ax.yaxis) - dy/2),ax.yaxis)]
                            except (ValueError, OverflowError):
                                cur_ylim = cur_ylim  # Keep previous limits 
                        if inverted_y:
                            ax.set_ylim(None,cur_ylim[0]) 
                        else:
                            ax.set_ylim(cur_ylim[0],None)
            else:            
                if yscale == 'linear':
                    cur_ylim -= dy/2 
                
                else:
                    try:
                        cur_ylim = [self.inv_transform_eval((self.transform_eval(cur_ylim[0],ax.yaxis) - dy/2),ax.yaxis),
                                   self.inv_transform_eval((self.transform_eval(cur_ylim[1],ax.yaxis) - dy/2),ax.yaxis)]
                    except (ValueError, OverflowError):
                        cur_ylim = cur_ylim  # Keep previous limits 
                if inverted_y:
                    ax.set_ylim(cur_ylim[1],cur_ylim[0])
                else:
                    ax.set_ylim(cur_ylim)

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
            
            self.update_hover()
            
        else:
            ax.figure.canvas.draw_idle()
            ax.figure.canvas.flush_events()

    def update_hover(self):
        """ update hover on fast draw (if exist)"""
        if self.hover_instance:
            if self.compare_xdata:
                if (self.touch_mode!='cursor' or len(self._touches) > 1) and not self.show_compare_cursor:
                    self.hover_instance.hover_outside_bound=True
  
                elif self.show_compare_cursor and self.touch_mode=='cursor':
                    self.show_compare_cursor=False
                else:
                    self.hover_instance.hover_outside_bound=True

            #update hover pos if needed
            elif self.hover_instance.show_cursor and self.x_hover_data and self.y_hover_data:        
                xy_pos = self.axes.transData.transform([(self.x_hover_data,self.y_hover_data)]) 
                self.hover_instance.x_hover_pos=float(xy_pos[0][0]) + self.x
                self.hover_instance.y_hover_pos=float(xy_pos[0][1]) + self.y
     
                self.hover_instance.ymin_line = float(self.axes.bbox.bounds[1]) + self.y
                self.hover_instance.ymax_line = float(self.axes.bbox.bounds[1] + self.axes.bbox.bounds[3] )+ self.y
    
                if self.hover_instance.x_hover_pos>self.x+self.axes.bbox.bounds[2] + self.axes.bbox.bounds[0] or \
                    self.hover_instance.x_hover_pos<self.x+self.axes.bbox.bounds[0] or \
                    self.hover_instance.y_hover_pos>self.y+self.axes.bbox.bounds[1] + self.axes.bbox.bounds[3] or \
                    self.hover_instance.y_hover_pos<self.y+self.axes.bbox.bounds[1]:               
                    self.hover_instance.hover_outside_bound=True
                else:
                    self.hover_instance.hover_outside_bound=False 

    def min_max(self, event):
        """ manage min/max touch mode """
        ax=self.axes
        xlabelbottom = ax.xaxis._major_tick_kw.get('tick1On')
        ylabelleft = ax.yaxis._major_tick_kw.get('tick1On')

        if xlabelbottom and event.x>self.x +ax.bbox.bounds[0] and \
            event.x<self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
            event.y<self.y + ax.bbox.bounds[1]:                   

            right_lim = self.x+ax.bbox.bounds[2]+ax.bbox.bounds[0]
            left_lim = self.x+ax.bbox.bounds[0]
            left_anchor_zone= (right_lim - left_lim)*.2 + left_lim
            right_anchor_zone= (right_lim - left_lim)*.8 + left_lim

            if event.x < left_anchor_zone or event.x > right_anchor_zone:            

                if self.text_instance:
                    if not self.text_instance.show_text:
                        midpoint =  ((self.x+ax.bbox.bounds[2] + ax.bbox.bounds[0]) + (self.x+ax.bbox.bounds[0]))/2
                        if event.x < midpoint:
                            anchor='left'
                            self.text_instance.x_text_pos=float(self.x+ax.bbox.bounds[0])
                            self.text_instance.y_text_pos=float(self.y+ax.bbox.bounds[1]) - self.text_instance.text_height
                            self.text_instance.offset_text = False
                        else:
                            anchor='right'
                            self.text_instance.x_text_pos=float(self.x+ax.bbox.bounds[2] + ax.bbox.bounds[0])
                            self.text_instance.y_text_pos=float(self.y+ax.bbox.bounds[1]) - self.text_instance.text_height
                            self.text_instance.offset_text = True

                        self.text_instance.current_axis = ax
                        self.text_instance.kind = {'axis':'x','anchor':anchor}

                        self.text_instance.show_text=True
                        return

        elif ylabelleft and  event.x<self.x +ax.bbox.bounds[0]  and \
            event.y<self.y + ax.bbox.bounds[1] + ax.bbox.bounds[3] and \
            event.y>self.y + ax.bbox.bounds[1]:

            top_lim = self.y+ax.bbox.bounds[3]+ax.bbox.bounds[1]
            bottom_lim = self.y+ax.bbox.bounds[1]                    
            bottom_anchor_zone=  (top_lim - bottom_lim)*.2 + bottom_lim
            top_anchor_zone= (top_lim - bottom_lim)*.8 + bottom_lim  

            if event.y < bottom_anchor_zone or event.y > top_anchor_zone:
                if self.text_instance:
                    if not self.text_instance.show_text:
                        midpoint =  ((self.y+ax.bbox.bounds[3] + ax.bbox.bounds[1]) + (self.y+ax.bbox.bounds[1]))/2
                        if event.y  > midpoint:
                            anchor='top'
                            self.text_instance.x_text_pos=float(self.x+ax.bbox.bounds[0]) - dp(40)
                            self.text_instance.y_text_pos=float(self.y+ax.bbox.bounds[1] + ax.bbox.bounds[3]) - self.text_instance.text_height
                            self.text_instance.offset_text = False
                        else:
                            anchor='bottom'
                            self.text_instance.x_text_pos=float(self.x+ax.bbox.bounds[0]) - dp(40)
                            self.text_instance.y_text_pos=float(self.y+ax.bbox.bounds[1]) - dp(6)
                            self.text_instance.offset_text = False
                        self.text_instance.current_axis = ax
                        self.text_instance.kind = {'axis':'y','anchor':anchor}

                        self.text_instance.show_text=True
                        return
            
    def apply_drag_legend(self, ax, event):
        """ drag legend method """
                        
        dx = event.x - self._last_touch_pos[event][0]
        if not self.legend_do_scroll_x:
            dx=0
        dy = event.y - self._last_touch_pos[event][1]      
        if not self.legend_do_scroll_y:
            dy=0        
        legend = ax.get_legend()
        if legend is not None:
        
            bbox = legend.get_window_extent()
            legend_x = bbox.xmin
            legend_y = bbox.ymin
               
            loc_in_canvas = legend_x +dx/2, legend_y+dy/2
            loc_in_norm_axes = legend.parent.transAxes.inverted().transform_point(loc_in_canvas)
            legend._loc = tuple(loc_in_norm_axes)
            
            #use blit method               
            if self.background is None:
                ax.get_legend().set_visible(False)
                ax.figure.canvas.draw_idle()
                ax.figure.canvas.flush_events()                   
                self.background = ax.figure.canvas.copy_from_bbox(ax.figure.bbox)
                ax.get_legend().set_visible(True)
            ax.figure.canvas.restore_region(self.background)   
    
            ax.draw_artist(legend)
                
            ax.figure.canvas.blit(ax.bbox)
            ax.figure.canvas.flush_events() 

            self.legend_instance.update_size()

    def zoom_factory(self, event, ax, base_scale=1.1):
        """ zoom with scrolling mouse method """

        newcoord = self.to_widget(event.x, event.y, relative=True)
        x = newcoord[0]
        y = newcoord[1]

        trans = ax.transData.inverted()
        xdata, ydata = trans.transform_point((x, y))     

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()

        scale=ax.get_xscale()
        yscale=ax.get_yscale()
        
        if scale == 'linear':
            old_min=cur_xlim[0]
            old_max=cur_xlim[1]

        else:
            min_=cur_xlim[0]
            max_=cur_xlim[1]            
            old_min = self.transform_eval(min_,ax.yaxis)
            xdata = self.transform_eval(xdata,ax.yaxis)
            old_max = self.transform_eval(max_,ax.yaxis)  

        if yscale == 'linear':
            yold_min=cur_ylim[0]
            yold_max=cur_ylim[1]

        else:
            ymin_=cur_ylim[0]
            ymax_=cur_ylim[1]            
            yold_min = self.transform_eval(ymin_,ax.yaxis)
            ydata = self.transform_eval(ydata,ax.yaxis)
            yold_max = self.transform_eval(ymax_,ax.yaxis)

        if event.button == 'scrolldown':
            # deal with zoom in
            scale_factor = 1 / base_scale
        elif event.button == 'scrollup':
            # deal with zoom out
            scale_factor = base_scale
        else:
            # deal with something that should never happen
            scale_factor = 1
            print(event.button)

        new_width = (old_max - old_min) * scale_factor
        new_height = (yold_max - yold_min) * scale_factor

        relx = (old_max - xdata) / (old_max - old_min)
        rely = (yold_max - ydata) / (yold_max - yold_min)

        if self.do_zoom_x:
            if scale == 'linear':
                ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * (relx)])
            else:
                new_min = xdata - new_width * (1 - relx)
                new_max = xdata + new_width * (relx)
                try:
                    new_min, new_max = self.inv_transform_eval(new_min,ax.yaxis), self.inv_transform_eval(new_max,ax.yaxis)
                except OverflowError:  # Limit case
                    new_min, new_max = min_, max_
                    if new_min <= 0. or new_max <= 0.:  # Limit case
                        new_min, new_max = min_, max_ 
                ax.set_xlim([new_min, new_max])
    
        if self.do_zoom_y:
            if yscale == 'linear':
                ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * (rely)])
            else:
                new_ymin = ydata - new_height * (1 - rely)
                new_ymax = ydata + new_height * (rely)
                try:
                    new_ymin, new_ymax = self.inv_transform_eval(new_ymin,ax.yaxis), self.inv_transform_eval(new_ymax,ax.yaxis)
                except OverflowError:  # Limit case
                    new_ymin, new_ymax = ymin_, ymax_
                    if new_ymin <= 0. or new_ymax <= 0.:  # Limit case
                        new_ymin, new_ymax = ymin_, ymax_ 
                ax.set_ylim([new_ymin, new_ymax]) 

        ax.figure.canvas.draw_idle()
        ax.figure.canvas.flush_events()    

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
        if self.legend_instance:
            self.legend_instance.update_size()
        if self.hover_instance:
            self.hover_instance.figwidth = self.width

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
            self.x0_box, self.y0_box = trans.transform_point((self._box_pos[0]-self.pos[0], self._box_pos[1]-self.pos[1])) 
            self.x1_box, self.y1_box = trans.transform_point((self._box_size[0]+self._box_pos[0]-self.pos[0], self._box_size[1]+self._box_pos[1]-self.pos[1]))
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
        xdata, ydata = trans.transform_point((event.x-pos_x, event.y-pos_y)) 

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

        x0data, y0data = trans.transform_point((x0-pos_x, y0-pos_y)) 
         
        if x0data>xmax or x0data<xmin or y0data>ymax or y0data<ymin:
            return

        if xdata<xmin:
            x1_min = self.axes.transData.transform([(xmin,ymin)])
            if (x1<x0 and not inverted_x) or (x1>x0 and inverted_x):
                x1=x1_min[0][0]+pos_x
            else:
                x0=x1_min[0][0]

        if xdata>xmax:
            x0_max = self.axes.transData.transform([(xmax,ymin)])
            if (x1>x0 and not inverted_x) or (x1<x0 and inverted_x):
                x1=x0_max[0][0]+pos_x 
            else:
                x0=x0_max[0][0]                  

        if ydata<ymin:
            y1_min = self.axes.transData.transform([(xmin,ymin)])
            if (y1<y0 and not inverted_y) or (y1>y0 and inverted_y):
                y1=y1_min[0][1]+pos_y
            else:
                y0=y1_min[0][1]+pos_y

        if ydata>ymax:
            y0_max = self.axes.transData.transform([(xmax,ymax)])
            if (y1>y0 and not inverted_y) or (y1<y0 and inverted_y):
                y1=y0_max[0][1]+pos_y
            else:
                y0=y0_max[0][1]+pos_y
                
        if abs(x1-x0)<dp(20) and abs(y1-y0)>self.minzoom:
            self.pos_x_rect_ver=x0
            self.pos_y_rect_ver=y0   
            
            x1_min = self.axes.transData.transform([(xmin,ymin)])
            x0=x1_min[0][0]+pos_x

            x0_max = self.axes.transData.transform([(xmax,ymin)])
            x1=x0_max[0][0]+pos_x

            self._alpha_ver=1
            self._alpha_hor=0
                
        elif abs(y1-y0)<dp(20) and abs(x1-x0)>self.minzoom:
            self.pos_x_rect_hor=x0
            self.pos_y_rect_hor=y0  

            y1_min = self.axes.transData.transform([(xmin,ymin)])
            y0=y1_min[0][1]+pos_y
             
            y0_max = self.axes.transData.transform([(xmax,ymax)])
            y1=y0_max[0][1]+pos_y         

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

class FakeEvent:
    x:None
    y:None
    
from kivy.factory import Factory

Factory.register('MatplotFigure', MatplotFigure)

Builder.load_string('''
<MatplotFigure>
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
