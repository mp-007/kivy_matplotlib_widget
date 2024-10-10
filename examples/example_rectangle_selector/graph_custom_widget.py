""" Custom MatplotFigure 
"""

import matplotlib
matplotlib.use('Agg')
import numpy as np
from resizable_widget import ResizeRelativeLayout
from kivy_matplotlib_widget.uix.graph_subplot_widget import MatplotFigureSubplot
from kivy.utils import get_color_from_hex
from matplotlib.colors import to_hex
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.graphics.texture import Texture


class MatplotFigureCustom(MatplotFigureSubplot):
    """Custom MatplotFigure
    """
    desktop_mode = BooleanProperty(True)
    
    def __init__(self, **kwargs):
        super(MatplotFigureCustom, self).__init__(**kwargs)

    def on_kv_post(self,_):
        self.selector = ResizeRelativeLayout(figure_wgt=self,desktop_mode=self.desktop_mode)       
        self.selector.figure_wgt = self    
        self.parent.add_widget(self.selector)

    def set_collection(self):
        self.selector.resize_wgt.ax = self.axes
        collections = self.axes.collections      
        
        if collections:
           self.selector.resize_wgt.set_collection(collections[0]) 
           self.selector.resize_wgt.update_bg_color()
           
    def set_line(self,line):
        self.selector.resize_wgt.ax = self.axes  
        self.selector.resize_wgt.set_line(line) 
        self.selector.resize_wgt.update_bg_color()
           
    def set_callback(self,callback):
        self.selector.resize_wgt.set_callback(callback)

    def on_touch_down(self, event):
        """ Manage Mouse/touch press """
        

        x, y = event.x, event.y

        if self.collide_point(x, y) and self.figure:
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
        
    def update_selector(self):
        """ update hover on fast draw (if exist)"""
        if self.selector:
            #update selector pos if needed
            if self.selector.resize_wgt.verts and self.touch_mode!='selector': 
                resize_wgt = self.selector.resize_wgt
                #update all selector pts
                xy_pos = resize_wgt.ax.transData.transform([(resize_wgt.verts[0][0],resize_wgt.verts[0][1])]) 
                new_pos=resize_wgt.to_widget(*(float(xy_pos[0][0]),float(xy_pos[0][1])))
                resize_wgt.pos[0] = new_pos[0] + self.x
                resize_wgt.pos[1] = new_pos[1] + self.y
                if self.collide_point(*resize_wgt.to_window(resize_wgt.pos[0],resize_wgt.pos[1])) and \
                    self.collide_point(*resize_wgt.to_window(resize_wgt.pos[0] + resize_wgt.size[0],resize_wgt.pos[1]+ resize_wgt.size[1])):
                    if resize_wgt.size[0] > 1 and resize_wgt.size[1] > 1:
                        resize_wgt.opacity = 1
                else:
                    resize_wgt.opacity = 0