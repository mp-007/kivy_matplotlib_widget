""" Custom MatplotFigure 
"""

import matplotlib
matplotlib.use('Agg')
import numpy as np
from kivy_matplotlib_widget.uix.graph_widget import MatplotFigure 
from kivy_matplotlib_widget.uix.hover_widget import add_hover
from kivy.utils import get_color_from_hex
from matplotlib.colors import to_hex
from kivy.metrics import dp
from kivy_matplotlib_widget.tools.cursors import cursor
from kivy.properties import NumericProperty,BooleanProperty


class MatplotlibEvent:
    x:None
    y:None
    pickradius:None
    inaxes:None
    projection:False
    compare_xdata:False

class MatplotFigureCustom(MatplotFigure):
    """Custom MatplotFigure
    """
    cursor_cls=None
    pickradius = NumericProperty(dp(50))
    projection = BooleanProperty(False)
    hist_range = BooleanProperty(True)
    myevent = MatplotlibEvent()

    def __init__(self, **kwargs):
        super(MatplotFigureCustom, self).__init__(**kwargs)

    def register_cursor(self,pickables=None):
        
        remove_artists=[]
        if hasattr(self,'horizontal_line'):
            remove_artists.append(self.horizontal_line)
        if hasattr(self,'vertical_line'):
            remove_artists.append(self.vertical_line) 
        if hasattr(self,'text'):
            remove_artists.append(self.text)
            
        self.cursor_cls = cursor(self.figure,pickables=pickables,remove_artists=remove_artists)
        
    def hover(self, event) -> None:
        """ hover cursor method (cursor to nearest value)
        
        Args:
            event: touch kivy event
            
        Return:
            None
        
        """
           
        #if cursor is set -> hover is on
        if self.hover_on:

            #mimic matplotlib mouse event with kivy touch evant
            self.myevent.x=event.x - self.pos[0]
            self.myevent.y=event.y - self.pos[1]
            # self.myevent.inaxes=self.figure.axes[0]
            self.myevent.inaxes=self.figure.canvas.inaxes((event.x - self.pos[0], 
                                                           event.y - self.pos[1]))
            self.myevent.pickradius=self.pickradius
            self.myevent.projection=self.projection
            self.myevent.compare_xdata=self.compare_xdata
            #find closest artist from kivy event
            sel = self.cursor_cls.xy_event(self.myevent) 
            
            #case if no good result
            if not sel:
                if hasattr(self,'horizontal_line'):
                    self.set_cross_hair_visible(False)  
                if self.hover_instance:
                    self.hover_instance.x_hover_pos=self.x
                    self.hover_instance.y_hover_pos=self.y      
                    self.hover_instance.show_cursor=False
                    self.x_hover_data = None
                    self.y_hover_data = None
                return

            if self.compare_xdata:
                 if not self.hover_instance or not hasattr(self.hover_instance,'children_list'):
                     return

                 ax=None
                 line=sel[0].artist
                 custom_x=None
                 if not hasattr(line,'axes'):
                     if hasattr(line,'_ContainerArtist__keep_alive'): 
                         if self.hist_range:
                            x_hist, y_hist, width_hist, height_hist = line[sel.index].get_bbox().bounds
                            if self.cursor_xaxis_formatter:
                                custom_x = f"{self.cursor_xaxis_formatter.format_data(x_hist)}-{self.cursor_xaxis_formatter.format_data(x_hist+ width_hist)}" 
                            else:
                                custom_x = f"{x_hist}-{x_hist+ width_hist}"
                       
                     line =line._ContainerArtist__keep_alive[0]
                 ax=line.axes
                    
                 if ax is None:
                     return
                 # idx_best_list = np.flatnonzero(np.array(distance) == np.nanmin(distance))
                 
                 #get datas from closest line
                 x = sel[0].target[0]
                 y = sel[0].target[1]
                 # print(sel)

                 xy_pos = ax.transData.transform([(x,y)]) 
                 self.x_hover_data = x
                 self.y_hover_data = y
                 self.hover_instance.x_hover_pos=float(xy_pos[0][0]) + self.x
                 self.hover_instance.y_hover_pos=float(xy_pos[0][1]) + self.y
                 self.hover_instance.y_touch_pos=float(event.y)
                 
                 if self.first_call_compare_hover:
                     self.hover_instance.show_cursor=True 
                 else:
                     self.first_call_compare_hover=True
                 
                 available_widget = self.hover_instance.children_list
                 nb_widget=len(available_widget)
                 index_list=list(range(nb_widget))

                 for i in range(len(sel)):
                     
                     if i > nb_widget-1:
                         break
                     else:
                         
                         line=sel[i].artist
                         line_label = line.get_label()
                         if line_label in self.hover_instance.children_names:
                             # index= self.hover_instance.children_names.index(line_label) 
                             index = [ii for ii, x in enumerate(self.hover_instance.children_names) \
                                      if x == line_label and ii in index_list][0]
                             
                             y = sel[i].target[1] 

                             xy_pos = ax.transData.transform([(x,y)]) 
                             pos_y=float(xy_pos[0][1]) + self.y
 
                             if pos_y<self.y+self.axes.bbox.bounds[1] + self.axes.bbox.bounds[3] and \
                                 pos_y>self.y+self.axes.bbox.bounds[1]:
                                 available_widget[index].x_hover_pos=float(xy_pos[0][0]) + self.x
                                 available_widget[index].y_hover_pos=float(xy_pos[0][1]) + self.y
                                 available_widget[index].custom_color = get_color_from_hex(to_hex(line.get_color()))
                                
                                 if self.cursor_yaxis_formatter:
                                     y = self.cursor_yaxis_formatter.format_data(y) 
                                 available_widget[index].label_y_value=f"{y}"
                                 available_widget[index].show_widget=True
                                 index_list.remove(index)
                                 
                 if i<nb_widget-1:
                     for ii in index_list:
                         available_widget[ii].show_widget=False

                 if self.cursor_xaxis_formatter:
                     x = self.cursor_xaxis_formatter.format_data(x) 
                    
                 self.hover_instance.label_x_value=f"{x}"
            
                 self.hover_instance.ymin_line = float(ax.bbox.bounds[1])  + self.y
                 self.hover_instance.ymax_line = float(ax.bbox.bounds[1] + ax.bbox.bounds[3])  + self.y
                
                 if self.hover_instance.x_hover_pos>self.x+self.axes.bbox.bounds[2] + self.axes.bbox.bounds[0] or \
                     self.hover_instance.x_hover_pos<self.x+self.axes.bbox.bounds[0] or len(index_list)==nb_widget:              
                     self.hover_instance.hover_outside_bound=True                            
                 else:
                     self.hover_instance.hover_outside_bound=False                      
                
                 return

            else:
                x = sel.target[0]
                y = sel.target[1] 
                # print(sel.target)
                
                if not self.hover_instance:
                    self.set_cross_hair_visible(True)
                
                # update the cursor x,y data  
                ax=None
                line=sel.artist
                custom_x=None
                if not hasattr(line,'axes'):
                   if hasattr(line,'_ContainerArtist__keep_alive'): 
                       if self.hist_range:
                           x_hist, y_hist, width_hist, height_hist = line[sel.index].get_bbox().bounds
                           if self.cursor_xaxis_formatter:
                               custom_x = f"{self.cursor_xaxis_formatter.format_data(x_hist)}-{self.cursor_xaxis_formatter.format_data(x_hist+ width_hist)}" 
                           else:
                               custom_x = f"{x_hist}-{x_hist+ width_hist}"
                       
                       line =line._ContainerArtist__keep_alive[0]
                ax=line.axes
                    
                if ax is None:
                    return
                
                if hasattr(self,'horizontal_line'):
                    self.horizontal_line.set_ydata(y)
                if hasattr(self,'vertical_line'):
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
                    if self.cursor_yaxis_formatter:
                        y = self.cursor_yaxis_formatter.format_data(y) 
                    if custom_x:
                        self.hover_instance.label_x_value=custom_x
                    else:
                        self.hover_instance.label_x_value=f"{x}"
                    self.hover_instance.label_y_value=f"{y}"
            
                    self.hover_instance.ymin_line = float(ax.bbox.bounds[1])  + self.y
                    self.hover_instance.ymax_line = float(ax.bbox.bounds[1] + ax.bbox.bounds[3])  + self.y
                    
                    if hasattr(line,'get_label'):
                        self.hover_instance.custom_label = line.get_label()
                    if hasattr(line,'get_color'):
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
                    if self.cursor_yaxis_formatter:
                        y = self.cursor_yaxis_formatter.format_data(y) 
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
                    
