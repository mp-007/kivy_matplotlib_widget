""" MatplotFigure is based on https://github.com/jeysonmc/kivy_matplotlib 
and kivy scatter
"""

import math

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

class MatplotFigure3D(Widget):
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
        self.touch_mode='pan'
        self.hover_on = False
        self.xsorted = True #to manage x sorted data (if numpy is used)

        #zoom box coordonnate
        self.x0_box = None
        self.y0_box = None
        self.x1_box = None
        self.y1_box = None
        
        #clear touches on touch up
        self._touches = []
        self._last_touch_pos = {}
              
        self.bind(size=self._onSize)

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
                
        #white background for blit method (fast draw)
        props = dict(boxstyle='square',edgecolor='w', facecolor='w', alpha=1.0)
        self.text_background=self.axes.text(0.5, 1.01, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', color='w', transform=self.axes.transAxes, bbox=props)       
        
        #cursor text
        self.text = self.axes.text(0.52, 1.01, '', transform=self.axes.transAxes, bbox=props)

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
            xdata, ydata = trans.transform_point((event.x, event.y))

            #loop all register lines and find closest x,y data for each valid line
            distance=[]
            good_line=[]
            good_index=[]
            good_index2=[]
            for line in self.lines:
                #get only visible lines
                if line.get_visible():  
                    #get line x,y datas
                    self.x_cursor, self.y_cursor = line.get_data()
                    
                    #check if line is not empty
                    if len(self.x_cursor)!=0:                        
                        #!!!! if numpy is available you can used this for faster results !!!!
                        #case 1 : x are sorted
                        #index = min(np.searchsorted(self.x_cursor, xdata), len(self.y_cursor) - 1)
                        #case 2:  x are not sorted
                        #index = np.argsort(abs(self.x_cursor - xdata))[0]
                        
                        #find closest data index from touch (x axis)
                        if self.xsorted:
                            index = sorted(range(len(abs(self.x_cursor - xdata))), 
                                           key=abs(self.x_cursor - xdata).__getitem__)[0] 
                        else:
                            index = sorted(range(len(abs(self.x_cursor - xdata))), 
                                           key=abs(self.x_cursor - xdata).__getitem__)[0] 

                        #get x data from index
                        x = self.x_cursor[index]
                        
                        #find ydata corresponding to xdata
                        y = self.y_cursor[index]
                                               
                        #get distance between line and touch (in pixels)
                        ax=line.axes 
                        #left axis
                        # xy_pixels_mouse = ax.transData.transform(np.vstack([xdata,ydata]).T)
                        xy_pixels_mouse = ax.transData.transform([(xdata,ydata)])
                        # xy_pixels = ax.transData.transform(np.vstack([x,y]).T)
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
            if min(distance)<dp(50):
                #!!! if numpy is available, argmin can be used form faster result !!!
                #idx_best=np.argmin(distance)
                
                #index of minimum distance
                idx_best=distance.index(min(distance))
                
                #get datas from closest line
                line=good_line[idx_best]
                self.x_cursor, self.y_cursor = line.get_data()
                x = self.x_cursor[good_index[idx_best]]
                y = self.y_cursor[good_index[idx_best]]                
                self.set_cross_hair_visible(True)
                
                # update the cursor x,y data               
                ax=line.axes
                self.horizontal_line.set_ydata(y)
                self.vertical_line.set_xdata(x)

                #x y label
                self.text.set_text(f"x={x}, y={y}")

                #blit method (always use because same visual effect as draw)
                self.axes.draw_artist(self.axes.patch)
                self.axes.draw_artist(self.text_background)
                self.axes.draw_artist(self.text)
                self.axes.draw_artist(list(self.axes.spines.values())[0])

                for line in self.axes.lines:
                    self.axes.draw_artist(line)

                mybbox=self.my_blit_box(ax.bbox.bounds[0],ax.bbox.bounds[1],ax.bbox.bounds[2],ax.bbox.bounds[3]+50)                    
                
                #draw (blit method)
                self.axes.figure.canvas.blit(mybbox)                 
                self.axes.figure.canvas.flush_events()

            #if touch is too far, hide cross hair cursor
            else:
                self.set_cross_hair_visible(False)  

    def home(self) -> None:
        """ reset data axis
        
        Return:
            None
        """
        ax = self.axes
        ax.set_xlim(self.xmin, self.xmax)  
        ax.set_ylim(self.ymin, self.ymax)                                

        ax.figure.canvas.draw_idle()
        ax.figure.canvas.flush_events() 

    def reset_touch(self) -> None:
        """ reset touch
        
        Return:
            None
        """
        self._touches = []
        self._last_touch_pos = {}

    @staticmethod
    def my_blit_box(x0, y0, width, height):
        """ build custom matplotlib bbox """
        return Bbox.from_bounds(x0, y0, width, height)
        
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

    def transform_with_touch(self, event):
        """ manage touch behaviour. based on kivy scatter method"""
        # just do a simple one finger drag
        changed = False

        if len(self._touches) == self.translation_touches:
            if self.touch_mode=='pan':
                self.apply_pan(self.axes, event)
            
            elif self.touch_mode=='zoombox':
                real_x, real_y = event.x - self.pos[0], event.y - self.pos[1]
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


    def on_touch_down(self, event):
        """ Manage Mouse/touch press """
        x, y = event.x, event.y
        
        if self.collide_point(x, y):
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
                               guiEvent=None)
            self.figcanvas.callbacks.process(s, event)

    # def on_touch_down(self, event):
    #     """ Manage Mouse/touch press """
    #     x, y = event.x, event.y

    #     if self.collide_point(x, y):
    #         if event.is_mouse_scrolling:
    #             ax = self.axes
    #             ax = self.axes
    #             self.zoom_factory(event, ax, base_scale=1.2)

    #         elif event.is_double_tap:
                
    #             ax = self.axes
    #             ax.set_xlim(self.xmin, self.xmax)
    #             yoffset = abs(self.ymax - self.ymin) * 0.01
    #             ax.set_ylim(self.ymin - yoffset, self.ymax + yoffset)
                
    #             self.reset_touch()
    #             ax.figure.canvas.draw_idle()
    #             ax.figure.canvas.flush_events() 
    #             return True
                  
    #         else:
    #             if self.touch_mode=='cursor':
    #                 self.hover_on=True
    #                 self.hover(event)                
    #             elif self.touch_mode=='zoombox':
    #                 real_x, real_y = x - self.pos[0], y - self.pos[1]
    #                 self.x_init=x
    #                 self.y_init=real_y
    #                 self.draw_box(event, x, real_y, x, real_y) 
                 
    #             event.grab(self)
    #             self._touches.append(event)
    #             self._last_touch_pos[event] = event.pos
    
    #             return True

    #     else:
    #         return False

    # def on_touch_move(self, event):
    #     """ Manage Mouse/touch move while pressed """

    #     x, y = event.x, event.y

    #     if event.is_double_tap:
    #         ax = self.axes
    #         ax.set_xlim(self.xmin, self.xmax)
    #         yoffset = abs(self.ymax - self.ymin) * 0.01
    #         ax.set_ylim(self.ymin - yoffset, self.ymax + yoffset)

    #         self.reset_touch()
    #         ax.figure.canvas.draw_idle()
    #         ax.figure.canvas.flush_events()                
    #         return True

    #     # scale/translate
    #     if event in self._touches and event.grab_current == self:

    #         if self.transform_with_touch(event):
    #             self.transform_with_touch(event)
    #         self._last_touch_pos[event] = event.pos

    #     # stop propagating if its within our bounds
    #     if self.collide_point(x, y):
    #         return True

    # def on_touch_up(self, event):
    #     """ Manage Mouse/touch release """
    #     # remove it from our saved touches
    #     if event in self._touches and event.grab_state:
    #         event.ungrab(self)
    #         del self._last_touch_pos[event]
    #         self._touches.remove(event)

    #     x, y = event.x, event.y
    #     if abs(self._box_size[0]) > 1 or abs(self._box_size[1]) > 1 or self.touch_mode=='zoombox':
    #         self.reset_box()     
            
    #     # stop propagating if its within our bounds
    #     if self.collide_point(x, y):

    #         if self.do_update:
    #             self.update_lim()            

    #         ax=self.axes
    #         ax.figure.canvas.draw_idle()
    #         ax.figure.canvas.flush_events()                           
            
    #         return True

    def apply_zoom(self, scale_factor, ax, anchor=(0, 0),new_line=None):
        """ zoom touch method """
                
        x = anchor[0]
        y = anchor[1]-self.pos[1]

        trans = ax.transData.inverted()
        xdata, ydata = trans.transform_point((x+new_line.x, y+new_line.y))        
        
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim() 

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * (relx)])
        ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * (rely)])

        if self.fast_draw:   
            #use blit method            
            ax.draw_artist(ax.patch)
            
            #if you want the left spline during on_move (slower) 
            if self.draw_left_spline:
                ax.draw_artist(list(ax.spines.values())[0])
           
            for line in ax.lines:
                ax.draw_artist(line)
            ax.figure.canvas.blit(ax.bbox)
            ax.figure.canvas.flush_events()
        else:
            ax.figure.canvas.draw_idle()
            ax.figure.canvas.flush_events()           

    def apply_pan(self, ax, event):
        """ pan method """
        
        trans = ax.transData.inverted()
        xdata, ydata = trans.transform_point((event.x, event.y))
        xpress, ypress = trans.transform_point((self._last_touch_pos[event][0], self._last_touch_pos[event][1]))
        dx = xdata - xpress
        dy = ydata - ypress

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        cur_xlim -= dx
        cur_ylim -= dy
        ax.set_xlim(cur_xlim)
        ax.set_ylim(cur_ylim)

        if self.fast_draw: 
            #use blit method
            ax.draw_artist(ax.patch)
            #if you want the left spline during on_move (slower) 
            if self.draw_left_spline:
                ax.draw_artist(list(ax.spines.values())[0])
           
            for line in ax.lines:
                ax.draw_artist(line)
                
            ax.figure.canvas.blit(ax.bbox)
            ax.figure.canvas.flush_events() 
            
        else:
            ax.figure.canvas.draw_idle()
            ax.figure.canvas.flush_events()

    def zoom_factory(self, event, ax, base_scale=1.1):
        """ zoom with scrolling mouse method """

        newcoord = self.to_widget(event.x, event.y, relative=True)
        x = newcoord[0]
        y = newcoord[1]

        trans = ax.transData.inverted()
        xdata, ydata = trans.transform_point((x, y))     

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()

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

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * (relx)])
        ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * (rely)])

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

    def update_lim(self):
        """ update axis lim if zoombox is used"""
        ax=self.axes

        self.do_update=False
        
        ax.set_xlim(left=min(self.x0_box,self.x1_box),right=max(self.x0_box,self.x1_box))
        ax.set_ylim(bottom=min(self.y0_box,self.y1_box),top=max(self.y0_box,self.y1_box))

    def reset_box(self):
        """ reset zoombox and apply zoombox limit if zoombox option if selected"""
        if abs(self._box_size[0])>dp(50) and abs(self._box_size[1])>dp(50):
            trans = self.axes.transData.inverted()
            self.x0_box, self.y0_box = trans.transform_point((self._box_pos[0], self._box_pos[1]-self.pos[1])) 
            self.x1_box, self.y1_box = trans.transform_point((self._box_size[0]+self._box_pos[0], self._box_size[1]+self._box_pos[1]-self.pos[1]))
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
        xdata, ydata = trans.transform_point((event.x, event.y-pos_y)) 

        xmin,xmax=self.axes.get_xlim()
        ymin,ymax=self.axes.get_ylim()
        
        x0data, y0data = trans.transform_point((x0, y0-pos_y)) 
        if x0data>xmax or x0data<xmin or y0data>ymax or y0data<ymin:
            return

        if xdata<xmin:
            x1_min = self.axes.transData.transform([(xmin,ymin)])
            if x1<x0:
                x1=x1_min[0][0]
            else:
                x0=x1_min[0][0]

        if xdata>xmax:
            x0_max = self.axes.transData.transform([(xmax,ymin)])
            if x1>x0:
                x1=x0_max[0][0]  
            else:
                x0=x0_max[0][0]                  

        if ydata<ymin:
            y1_min = self.axes.transData.transform([(xmin,ymin)])
            if y1<y0:
                y1=y1_min[0][1]+pos_y
            else:
                y0=y1_min[0][1]+pos_y
                
        if ydata>ymax:
            y0_max = self.axes.transData.transform([(xmax,ymax)])
            if y1>y0:
                y1=y0_max[0][1]+pos_y
            else:
                y0=y0_max[0][1]+pos_y
                
        if abs(x1-x0)<dp(20) and abs(y1-y0)>dp(50):
            self.pos_x_rect_ver=x0
            self.pos_y_rect_ver=y0   
            
            x1_min = self.axes.transData.transform([(xmin,ymin)])
            x0=x1_min[0][0]

            x0_max = self.axes.transData.transform([(xmax,ymin)])
            x1=x0_max[0][0]             

            self._alpha_ver=1 
             
        elif abs(y1-y0)<dp(20) and abs(x1-x0)>dp(50):
            self.pos_x_rect_hor=x0
            self.pos_y_rect_hor=y0  

            y1_min = self.axes.transData.transform([(xmin,ymin)])
            y0=y1_min[0][1]+pos_y
             
            y0_max = self.axes.transData.transform([(xmax,ymax)])
            y1=y0_max[0][1]+pos_y         

            self._alpha_hor=1
                        
        else:
            self._alpha_hor=0   
            self._alpha_ver=0
            
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

Factory.register('MatplotFigure3D', MatplotFigure3D)

Builder.load_string('''
<MatplotFigure3D>
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
            border: 3, 3, 3, 3
            
    canvas.after:            
        #horizontal rectangle left
		Color:
			rgba:0, 0, 0, self._alpha_hor
		Line:
			width: dp(1)
			rectangle:
				(self.pos_x_rect_hor-dp(3), self.pos_y_rect_hor-dp(20), dp(4),dp(40))            

        #horizontal rectangle right
		Color:
			rgba:0, 0, 0, self._alpha_hor
		Line:
			width: dp(1)
			rectangle:
				(self.pos_x_rect_hor-dp(1)+self._box_size[0], self.pos_y_rect_hor-dp(20), dp(4),dp(40))             

        #vertical rectangle bottom
		Color:
			rgba:0, 0, 0, self._alpha_ver
		Line:
			width: dp(1)
			rectangle:
				(self.pos_x_rect_ver-dp(20), self.pos_y_rect_ver-dp(1), dp(40),dp(4))            

        #horizontal rectangle right
		Color:
			rgba:0, 0, 0, self._alpha_ver
		Line:
			width: dp(1)
			rectangle:
				(self.pos_x_rect_ver-dp(20), self.pos_y_rect_ver-dp(3)+self._box_size[1], dp(40),dp(4))             

        ''')
