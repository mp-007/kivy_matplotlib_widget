""" Custom MatplotFigure 
"""

import matplotlib
matplotlib.use('Agg')
import numpy as np
selector_widgets_available = False
try:
    selector_widgets_available = True
    from selector_widget import ResizeRelativeLayout,LassoRelativeLayout,EllipseRelativeLayout,SpanRelativeLayout
except ImportError:
    print('Selector widgets are not available')
    
from kivy_matplotlib_widget.uix.graph_subplot_widget import MatplotFigureSubplot
from kivy.properties import BooleanProperty,OptionProperty
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.clock import Clock

from matplotlib.backend_bases import ResizeEvent

def _iter_axes_subartists(ax):
    r"""Yield all child `Artist`\s (*not* `Container`\s) of *ax*."""
    return ax.collections + ax.images + ax.lines + ax.texts + ax.patches

class MatplotFigureSelector(MatplotFigureSubplot):
    """Custom MatplotFigure
    """
    desktop_mode = BooleanProperty(True)
    current_selector = OptionProperty("None",
                                     options = ["None",'rectangle','lasso','ellipse','span','custom'])
    
    def __init__(self, **kwargs):
        self.kv_post_done = False
        self.selector = None
        super(MatplotFigureSelector, self).__init__(**kwargs)

    def on_kv_post(self,_):
        # if not self.selector:
        if self.current_selector != "None" and selector_widgets_available:
            if self.current_selector == 'rectangle':
                self.set_selector(ResizeRelativeLayout)
            elif self.current_selector == 'lasso':
                self.set_selector(LassoRelativeLayout) 
            elif self.current_selector == 'ellipse':
                self.set_selector(EllipseRelativeLayout)     
            elif self.current_selector == 'span':
                self.set_selector(SpanRelativeLayout)                  
        self.kv_post_done=True
        
    def on_current_selector(self,instance,value,*args):
        
        if self.kv_post_done and selector_widgets_available:

            if value == 'rectangle':
                self.set_selector(ResizeRelativeLayout)
            elif value == 'lasso':
                self.set_selector(LassoRelativeLayout)   
            elif value == 'ellipse':
                self.set_selector(EllipseRelativeLayout) 
            elif self.current_selector == 'span':
                self.set_selector(SpanRelativeLayout)                   
            elif value == "None":
                if self.selector:
                    Window.unbind(mouse_pos=self.selector.resize_wgt.on_mouse_pos)
                    self.parent.remove_widget(self.selector)
                self.selector = None
        
    def set_selector(self,selector,*args):
        selector_collection=None
        selector_line=None
        callback = None
        callback_clear = None
        if self.selector:
            selector_collection = self.selector.resize_wgt.collection
            selector_line = self.selector.resize_wgt.line
            callback = self.selector.resize_wgt.callback
            callback_clear  = self.selector.resize_wgt.callback_clear
            Window.unbind(mouse_pos=self.selector.resize_wgt.on_mouse_pos)
            self.parent.remove_widget(self.selector)
            
        self.selector = selector(figure_wgt=self,desktop_mode=self.desktop_mode)
        self.selector.resize_wgt.ax = self.axes
        if selector_collection:
            self.set_collection()
        if selector_line:
            self.set_line(selector_line)
        if callback:
            self.set_callback(callback)
        if callback_clear:
            self.set_callback_clear(callback_clear)
            
        self.parent.add_widget(self.selector)  
        

    def set_collection(self):          
        self.selector.resize_wgt.ax = self.axes
        collections = self.axes.collections      
        
        if collections:
           self.selector.resize_wgt.set_collection(collections[0]) 
           # self.selector.resize_wgt.update_bg_color()
           
    def set_line(self,line):

        self.selector.resize_wgt.ax = self.axes  
        self.selector.resize_wgt.set_line(line) 
        # self.selector.resize_wgt.update_bg_color()
           
    def set_callback(self,callback):
        self.selector.resize_wgt.set_callback(callback)
        
    def set_callback_clear(self,callback):
        self.selector.resize_wgt.set_callback_clear(callback)
        
    def on_touch_down(self, event):
        """ Manage Mouse/touch press """
        if self.disabled:
            return
        x, y = event.x, event.y

        if self.collide_point(x, y) and self.figure:
            self._pressed = True
            self.show_compare_cursor=False
            if self.legend_instance:
                select_legend=False
                for current_legend in self.legend_instance:
                    if current_legend.box.collide_point(x, y):
                        select_legend=True
                        self.current_legend = current_legend
                        break
                if select_legend:
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
                else:
                    self.current_legend = None
                       
            if event.is_mouse_scrolling:
                if not self.disable_mouse_scrolling and self.touch_mode!='selector':
                    self.zoom_factory(event, base_scale=1.2)
                return True

            elif event.is_double_tap:
                if not self.disable_double_tap:
                    if self.touch_mode!='selector': 
                        self.home(event)
                return True
                  
            else:
                if self.touch_mode=='cursor':
                    self.hover_on=True
                    self.hover(event)                
                elif self.touch_mode=='zoombox':
                    real_x, real_y = x - self.pos[0], y - self.pos[1]
                    self.x_init=x
                    self.y_init=real_y
                    self.draw_box(event, x, real_y, x, real_y,onpress=True) 
                elif self.touch_mode=='minmax':
                    self.min_max(event) 
                elif self.touch_mode=='selector':
                    pass                    
                                     
                event.grab(self)
                self._touches.append(event)
                self._last_touch_pos[event] = event.pos
                if len(self._touches)>1:
                    #new touch, reset background
                    self.background=None
                    
                return True

        else:
            return False  
        
    def apply_zoom(self, scale_factor, ax, anchor=(0, 0),new_line=None):
        """ zoom touch method """
        if self.touch_mode=='selector':
            return
                
        x = anchor[0]-self.pos[0]
        y = anchor[1]-self.pos[1]

        #manage press and drag
        if not self._pick_info:
            self.myevent.x=x
            self.myevent.y=y
            self.myevent.inaxes=self.figure.canvas.inaxes((x,y))               
            #press event
            axes = [a for a in self.figure.canvas.figure.get_axes()
                    if a.in_axes(self.myevent)]               

            self._pick_info = axes
            
        if not self._pick_info:
            return        
        
        artists=[]
        for i,ax in enumerate(self._pick_info):
            
            self.axes = ax
            
            twinx = any(ax.get_shared_x_axes().joined(ax, prev)
                        for prev in self._pick_info[:i])
            
            twiny = any(ax.get_shared_y_axes().joined(ax, prev)
                        for prev in self._pick_info[:i])

            artists.extend(_iter_axes_subartists(ax))

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
    
            if self.do_zoom_x and not twinx:
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
        
            if self.do_zoom_y and not twiny:
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
                if self.draw_all_axes:
                    for myax in self.figure.canvas.figure.get_axes():
                        index = self.figure.axes.index(myax)  
                        self.background_patch_copy[index].set_visible(True)                   
                else:
                    index = self.figure.axes.index(ax) 
                    self.background_patch_copy[index].set_visible(True)
                self.figcanvas.draw_idle()
                self.figcanvas.flush_events()    
                self.background = self.figcanvas.copy_from_bbox(ax.figure.bbox)
                if self.draw_all_axes:
                    for myax in self.figure.canvas.figure.get_axes():
                        index = self.figure.axes.index(myax)  
                        self.background_patch_copy[index].set_visible(False)                   
                else:                   
                    self.background_patch_copy[index].set_visible(False)  
            self.figcanvas.restore_region(self.background)                
           

            if self.draw_all_axes:
                for myax in self.figure.canvas.figure.get_axes():
                    artists = _iter_axes_subartists(myax)
                    for artist in artists: 
                        ax.draw_artist(artist)
                    
            else:
                for artist in artists: 
                    ax.draw_artist(artist)
                
            self.figcanvas.blit(ax.bbox)
            self.figcanvas.flush_events() 
            
            self.update_hover()
            
        else:
            self.figcanvas.draw_idle()
            self.figcanvas.flush_events()           

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
        self.figcanvas.flush_events()
        
        # self.figcanvas.draw()  
        if self.legend_instance:
            for current_legend in self.legend_instance:
                current_legend.update_size()
        if self.hover_instance:
            self.hover_instance.figwidth = self.width

        # if self.touch_mode=='selector':
        if self.selector and self.selector.resize_wgt.verts:
            #update selector next frame to have correct position
            Clock.schedule_once(self.update_selector)         

            
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
        self.update_selector()  

        
    def update_selector(self,*args):
        """ update selector on fast draw (if exist)"""
        if self.selector:
            # print(len(args))
            #update selector pos if needed
            if self.selector.resize_wgt.verts and (len(args)!=0 or self.touch_mode!='selector'): 
                resize_wgt = self.selector.resize_wgt

                if hasattr(resize_wgt,'shapes'):
                    #lasso widget or ellipse
                    if resize_wgt.shapes:
                        if hasattr(resize_wgt.shapes[0],'radius_x'):
                            #ellipse widget
                            xy_pos = resize_wgt.ax.transData.transform([(resize_wgt.verts[1][0],resize_wgt.verts[1][1])])
                            new_pos=resize_wgt.to_widget(*(float(xy_pos[0][0]),float(xy_pos[0][1])))
                            pos0 = new_pos[0] + self.x
                            pos1 = new_pos[1] + self.y 
                            
                            xy_pos2 = resize_wgt.ax.transData.transform([(resize_wgt.verts[2][0],resize_wgt.verts[2][1])])
                            new_pos2=resize_wgt.to_widget(*(float(xy_pos2[0][0]),float(xy_pos2[0][1])))
                            pos0_2 = new_pos2[0] + self.x
                            pos1_2 = new_pos2[1] + self.y 
    
                            current_shape=resize_wgt.shapes[0]
                            dataxy1 = current_shape.selection_point_inst.points
                            dataxy2 = current_shape.selection_point_inst2.points 
                            
                            #note: the 2 first points are the same in current_shape.points
                            pos0_old = dataxy1[0]
                            pos1_old = dataxy1[1]
    
                            pos0_2_old = dataxy2[0]
                            pos1_2_old = dataxy2[1]                            
                            
                            old_length = np.sqrt((pos0_2_old - pos0_old)**2 + (pos1_2_old - pos1_old)**2)
                            new_length = np.sqrt((pos0_2 - pos0)**2 + (pos1_2 - pos1)**2)
                            
                            scale = float(new_length / old_length)
                            
                            xy_pos3 = resize_wgt.ax.transData.transform([(resize_wgt.verts[0][0],resize_wgt.verts[0][1])])
                            new_pos3=resize_wgt.to_widget(*(float(xy_pos3[0][0]),float(xy_pos3[0][1])))
                            pos0_c = new_pos3[0] + self.x
                            pos1_c = new_pos3[1] + self.y
                            
                            for s in resize_wgt.shapes:
                                s.rescale(scale)
                                
                            for s in resize_wgt.shapes:
                                s.translate(pos=(pos0_c,pos1_c))                            
                            
                            xmin,xmax,ymin,ymax = resize_wgt.shapes[0].get_min_max()
                        else:
                            #lasso widget
                            xy_pos = resize_wgt.ax.transData.transform([(resize_wgt.verts[0][0],resize_wgt.verts[0][1])])
                            new_pos=resize_wgt.to_widget(*(float(xy_pos[0][0]),float(xy_pos[0][1])))
                            pos0 = new_pos[0] + self.x
                            pos1 = new_pos[1] + self.y 
                            
                            xy_pos2 = resize_wgt.ax.transData.transform([(resize_wgt.verts[1][0],resize_wgt.verts[1][1])])
                            new_pos2=resize_wgt.to_widget(*(float(xy_pos2[0][0]),float(xy_pos2[0][1])))
                            pos0_2 = new_pos2[0] + self.x
                            pos1_2 = new_pos2[1] + self.y 
    
                            current_shape=resize_wgt.shapes[0]
                            dataxy = np.array(current_shape.points).reshape(-1,2) 
                            
                            #note: the 2 first points are the same in current_shape.points
                            pos0_old = dataxy[1][0]
                            pos1_old = dataxy[1][1]
    
                            pos0_2_old = dataxy[2][0]
                            pos1_2_old = dataxy[2][1]
                            
                            old_length = np.sqrt((pos0_2_old - pos0_old)**2 + (pos1_2_old - pos1_old)**2)
                            new_length = np.sqrt((pos0_2 - pos0)**2 + (pos1_2 - pos1)**2)
                            
                            scale = new_length / old_length
                            
                            for s in resize_wgt.shapes:
                                s.rescale(scale)
                                
                            for s in resize_wgt.shapes:
                                s.translate(pos=(pos0,pos1))                            
    
                            xmax, ymax = dataxy.max(axis=0)
                            xmin, ymin = dataxy.min(axis=0)                    
                        
                        if self.collide_point(*resize_wgt.to_window(xmin,ymin)) and \
                            self.collide_point(*resize_wgt.to_window(xmax,ymax)):
                            resize_wgt.opacity = 1
                        else:
                            resize_wgt.opacity = 0                   
     
                elif self.selector.resize_wgt.verts and (len(args)!=0 or self.touch_mode!='selector'): 
                    resize_wgt = self.selector.resize_wgt
                    if not (resize_wgt.size[0] > 1 and resize_wgt.size[1] > 1):
                        return
                    
                    #rectangle or spann selector
                    if hasattr(resize_wgt,'span_orientation'):
                        #span selector
                        if resize_wgt.span_orientation == 'vertical':
                            xy_pos = resize_wgt.ax.transData.transform([(resize_wgt.verts[0][0],resize_wgt.verts[0][1])]) 
                            new_pos=resize_wgt.to_widget(*(float(xy_pos[0][0]),float(xy_pos[0][1])))
                            resize_wgt.pos[0] = new_pos[0] + self.x
                            
                            top_bound = float(self.y +resize_wgt.ax.bbox.bounds[3] + resize_wgt.ax.bbox.bounds[1])
                            bottom_bound = float(self.y +resize_wgt.ax.bbox.bounds[1])
                            resize_wgt.pos[1] = bottom_bound - self.y
                            
                            #recalcul size
                            xy_pos2 = resize_wgt.ax.transData.transform([(resize_wgt.verts[3][0],resize_wgt.verts[3][1])]) 
                            resize_wgt.size[0] = float(xy_pos2[0][0] - xy_pos[0][0])
                            resize_wgt.size[1] = top_bound-bottom_bound
                        
                        elif resize_wgt.span_orientation == 'horizontal':
                            xy_pos = resize_wgt.ax.transData.transform([(resize_wgt.verts[0][0],resize_wgt.verts[0][1])]) 
                            new_pos=resize_wgt.to_widget(*(float(xy_pos[0][0]),float(xy_pos[0][1])))
                            left_bound = float(self.x +resize_wgt.ax.bbox.bounds[0])
                            right_bound = float(self.x +resize_wgt.ax.bbox.bounds[2] +resize_wgt.ax.bbox.bounds[0] )
                            
                            width = right_bound-left_bound
                            
                            left_bound,right_bound = resize_wgt.to_widget(left_bound,right_bound)
                            
                            resize_wgt.pos[0] = left_bound
                            resize_wgt.pos[1] = new_pos[1] + self.y

                            #recalcul size
                            xy_pos2 = resize_wgt.ax.transData.transform([(resize_wgt.verts[0][1],resize_wgt.verts[1][1])]) 
                            resize_wgt.size[0] = width
                            resize_wgt.size[1] = float(xy_pos2[0][1] - xy_pos[0][1])                        
                        
                    else:
                        #rectangle selector
                        
                        #update all selector pts
                        #recalcul pos
                        xy_pos = resize_wgt.ax.transData.transform([(resize_wgt.verts[0][0],resize_wgt.verts[0][1])]) 
                        new_pos=resize_wgt.to_widget(*(float(xy_pos[0][0]),float(xy_pos[0][1])))
                        resize_wgt.pos[0] = new_pos[0] + self.x
                        resize_wgt.pos[1] = new_pos[1] + self.y
                        
                        #recalcul size
                        xy_pos2 = resize_wgt.ax.transData.transform([(resize_wgt.verts[2][0],resize_wgt.verts[2][1])]) 
                        resize_wgt.size[0] = float(xy_pos2[0][0] - xy_pos[0][0])
                        resize_wgt.size[1] = float(xy_pos2[0][1] - xy_pos[0][1])
                        
                    if self.collide_point(*resize_wgt.to_window(resize_wgt.pos[0],resize_wgt.pos[1])) and \
                        self.collide_point(*resize_wgt.to_window(resize_wgt.pos[0] + resize_wgt.size[0],resize_wgt.pos[1]+ resize_wgt.size[1])):
                        resize_wgt.opacity = 1
                    else:
                        resize_wgt.opacity = 0                        