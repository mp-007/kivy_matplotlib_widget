""" Custom MatplotFigure 
"""

import matplotlib
matplotlib.use('Agg')
import numpy as np
from line_setting import LineSettingFloatLayout
from line_data import LineDataFloatLayout
from kivy_matplotlib_widget.uix.graph_widget import MatplotFigure 
from kivy.utils import get_color_from_hex
from matplotlib.colors import to_hex
from kivy.metrics import dp


class MatplotFigureCustom(MatplotFigure):
    """Custom MatplotFigure
    """

    def __init__(self, **kwargs):
        super(MatplotFigureCustom, self).__init__(**kwargs)

        self.line_setting_box = LineSettingFloatLayout()
        self.line_data_box = LineDataFloatLayout()

    def on_kv_post(self,_):
        self.line_setting = self.line_setting_box.ids.line_setting
        self.line_setting.figure_wgt = self    
        self.parent.add_widget(self.line_setting_box)
        
        self.line_data_widget = self.line_data_box.ids.line_data
        self.line_data_widget.figure_wgt = self            
        self.parent.add_widget(self.line_data_box)

    def search_line(self, event):
        closest_line = None
        trans = self.axes.transData.inverted()
        xdata, ydata = trans.transform_point((event.x - self.pos[0], event.y - self.pos[1]))
        good_line=[]
        distance =[]
        for line in self.axes.lines:
            x, y = line.get_data()
            
            if line.get_visible():
                if len(x)!=0:
                    index = np.argsort(abs(x - xdata))[0]
                    x = x[index]
                    y = y[index]
                    ax=line.axes
                    xy_pixels_mouse = ax.transData.transform([(xdata,ydata)])
                    xy_pixels = ax.transData.transform([(x,y)])
                    dx2 = (xy_pixels_mouse[0][0]-xy_pixels[0][0])**2
                    dy2 = (xy_pixels_mouse[0][1]-xy_pixels[0][1])**2
                    distance.append((dx2 + dy2)**0.5)
                    good_line.append(line)
        if len(good_line)==0:
            return
        if min(distance)<dp(20):           
            idx_best=np.argmin(distance)
            closest_line=good_line[idx_best]

            self.line_setting.show_setting=True
            color = get_color_from_hex(to_hex(closest_line.get_color()))
            self.line_setting.ids.color_picker_button.mycolor = color
            self.line_setting.line_name = closest_line
            self.line_setting.x=event.x - self.pos[0] 
            self.line_setting.y=event.y - self.pos[1]
            
            linewidth = closest_line.get_linewidth()
            linestyle = closest_line.get_linestyle()
            
            self.line_setting.ids.line_width_button.text2=str(int(linewidth))
            self.line_setting.ids.line_type_button.text2=str(linestyle)

        else:
            self.line_setting.show_setting=False

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
                elif self.touch_mode=='line_setting':
                    self.search_line(event)
                elif self.touch_mode=='line_data':
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