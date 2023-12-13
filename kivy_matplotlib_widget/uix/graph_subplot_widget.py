""" Custom MatplotFigure 
"""

import math
import copy
import time

import matplotlib
matplotlib.use('Agg')
import numpy as np
from kivy_matplotlib_widget.uix.graph_widget import _FigureCanvas ,MatplotFigure
from kivy_matplotlib_widget.uix.hover_widget import add_hover
from kivy.utils import get_color_from_hex
from matplotlib.colors import to_hex
from kivy.metrics import dp
from kivy_matplotlib_widget.tools.cursors import cursor
from kivy.properties import NumericProperty,BooleanProperty
from kivy.graphics.texture import Texture

def _iter_axes_subartists(ax):
    r"""Yield all child `Artist`\s (*not* `Container`\s) of *ax*."""
    return ax.collections + ax.images + ax.lines + ax.texts + ax.patches

class MatplotlibEvent:
    x:None
    y:None
    pickradius:None
    inaxes:None
    projection:False
    compare_xdata:False

class MatplotFigureSubplot(MatplotFigure):
    """Custom MatplotFigure
    """
    cursor_cls=None
    pickradius = NumericProperty(dp(50))
    projection = BooleanProperty(False)
    hist_range = BooleanProperty(True)
    myevent = MatplotlibEvent()
    interactive_axis_pad= NumericProperty(dp(100))
    _pick_info = None
    draw_all_axes = BooleanProperty(False)
    max_hover_rate =  NumericProperty(None,allownone=True) 
    last_hover_time=None   
    cursor_last_axis=None
        
    def my_in_axes(self,ax, mouseevent):
        """
        variante of matplotlib in_axes (get interactive axis)
        
        Return whether the given event (in display coords) is in the Axes or in margin axis.
        """
        result1 = False#ax.patch.contains(mouseevent)[0]
        
        result2 = False
        if not result1:
            
            xlabelsize = self.interactive_axis_pad
            ylabelsize = self.interactive_axis_pad           
            
            #get label left/right information
            xlabelbottom = ax.xaxis._major_tick_kw.get('tick1On')
            xlabeltop = ax.xaxis._major_tick_kw.get('tick2On')
            ylabelleft = ax.yaxis._major_tick_kw.get('tick1On')
            ylabelright = ax.yaxis._major_tick_kw.get('tick2On')             
                   
            # print(ylabelright)
            
            #check if tick zone
            #y left axis
            if ylabelleft and  mouseevent.x>self.x +ax.bbox.bounds[0] - ylabelsize and \
                mouseevent.x<self.x + ax.bbox.bounds[0] and \
                mouseevent.y<self.y + ax.bbox.bounds[1] + ax.bbox.bounds[3] and \
                mouseevent.y>self.y + ax.bbox.bounds[1]:
                result2 = True

            #x bottom axis
            elif xlabelbottom and mouseevent.x>self.x +ax.bbox.bounds[0] and \
                mouseevent.x<self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                mouseevent.y>self.y + ax.bbox.bounds[1] - xlabelsize and \
                mouseevent.y<self.y + ax.bbox.bounds[1]:
                result2 = True

            #y right axis                 
            elif ylabelright and mouseevent.x<self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] + self.interactive_axis_pad and \
                mouseevent.x>self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                mouseevent.y<self.y + ax.bbox.bounds[1] + ax.bbox.bounds[3] and \
                mouseevent.y>self.y + ax.bbox.bounds[1]:                     
                result2 = True

            # #x top axis
            elif xlabeltop and xlabelbottom and mouseevent.x>self.x +ax.bbox.bounds[0] and \
                mouseevent.x<self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                mouseevent.y>self.y + ax.bbox.bounds[1] + xlabelsize and \
                mouseevent.y<self.y + ax.bbox.bounds[1]:
                result2 = True
        
        if result1 == result2:
            result=result1
        elif result1 or result2:
            result=True
        
        return result

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
            for ax in self.figure.axes:
                # ax=self.figure.axes[0]
                patch_cpy=copy.copy(ax.patch)
                patch_cpy.set_visible(False)
                for pos in ['right', 'top', 'bottom', 'left']:
                    ax.spines[pos].set_zorder(10)
                patch_cpy.set_zorder(9)
                self.background_patch_copy.append(ax.add_patch(patch_cpy))
            
            #set default axes
            self.axes = self.figure.axes[0]
            
            #set min/max axes attribute
            self.xmin,self.xmax = [],[]
            self.ymin,self.ymax = [],[]
            for my_axes in self.figure.axes:
                #set default xmin/xmax and ymin/ymax
                xmin,xmax = my_axes.get_xlim()
                ymin,ymax = my_axes.get_ylim()
                
                self.xmin.append(xmin)
                self.xmax.append(xmax)
                self.ymin.append(ymin)
                self.ymax.append(ymax)
        
        if self.legend_instance:
            self.legend_instance.reset_legend()
            self.legend_instance=None
            
        # Texture
        self._img_texture = Texture.create(size=(w, h))
        
        #close last figure in memory (avoid max figure warning)
        matplotlib.pyplot.close()
        
    def __init__(self, **kwargs):
        
        super(MatplotFigureSubplot, self).__init__(**kwargs)
        self.background_patch_copy=[] 

    def register_cursor(self,pickables=None):
        
        remove_artists=[]
        if hasattr(self,'horizontal_line'):
            remove_artists.append(self.horizontal_line)
        if hasattr(self,'vertical_line'):
            remove_artists.append(self.vertical_line) 
        if hasattr(self,'text'):
            remove_artists.append(self.text)
            
        self.cursor_cls = cursor(self.figure,pickables=pickables,remove_artists=remove_artists)


    def main_home(self, *args):
        """
        Restore the original view.

        For convenience of being directly connected as a GUI callback, which
        often get passed additional parameters, this method accepts arbitrary
        parameters, but does not use them.
        """
        self._nav_stack.home()
        self.set_history_buttons()
        self._update_view()
 
    def home(self, event=None):
 
        if self.xmin is not None and \
            self.xmax is not None and \
            self.ymin is not None and \
            self.ymax is not None:
                
            if event:
                self.myevent.x=event.x - self.pos[0]
                self.myevent.y=event.y - self.pos[1]
                self.myevent.inaxes=self.figure.canvas.inaxes((event.x - self.pos[0], 
                                                               event.y - self.pos[1])) 
                
                axes = [a for a in self.figure.canvas.figure.get_axes()
                        if a.in_axes(self.myevent)]   

                if not axes:
                    return
                
                for ax in axes:
                    xleft,xright=ax.get_xlim()
                    ybottom,ytop=ax.get_ylim() 
                    
                    #check inverted data
                    inverted_x = False
                    if xleft>xright:
                        inverted_x=True
                    inverted_y = False
                    if ybottom>ytop:
                        inverted_y=True  
                        
                    index = self.figure.axes.index(ax)
                    xmin=self.xmin[index]
                    xmax=self.xmax[index]
                    ymin=self.ymin[index]
                    ymax=self.ymax[index]
                    
                    if inverted_x:
                        ax.set_xlim(right=xmin,left=xmax)
                    else:
                        ax.set_xlim(left=xmin,right=xmax)
                    if inverted_y:
                        ax.set_ylim(top=ymin,bottom=ymax)
                    else:
                        ax.set_ylim(bottom=ymin,top=ymax) 

            else:
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
                    
                index = self.figure.axes.index(ax)
                xmin=self.xmin[index]
                xmax=self.xmax[index]
                ymin=self.ymin[index]
                ymax=self.ymax[index]
                
                if inverted_x:
                    ax.set_xlim(right=xmin,left=xmax)
                else:
                    ax.set_xlim(left=xmin,right=xmax)
                if inverted_y:
                    ax.set_ylim(top=ymin,bottom=ymax)
                else:
                    ax.set_ylim(bottom=ymin,top=ymax)                              
    
            self.update_cursor()
            ax.figure.canvas.draw_idle()
            ax.figure.canvas.flush_events() 

    def on_touch_down(self, event):
        """ Manage Mouse/touch press """
        x, y = event.x, event.y

        if self.collide_point(x, y) and self.figure:
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
                    self.zoom_factory(event, ax, base_scale=1.2)
                return True

            elif event.is_double_tap:
                if not self.disable_double_tap:
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
                 
                event.grab(self)
                self._touches.append(event)
                self._last_touch_pos[event] = event.pos
                if len(self._touches)>1:
                    #new touch, reset background
                    self.background=None
                    
                return True

        else:
            return False    

    def update_cursor(self):
        if self.cursor_last_axis:
            horizontal_line=False
            if hasattr(self,'horizontal_line'):
                if self.horizontal_line.get_visible():
                    horizontal_line=True
            if horizontal_line or self.hover_instance:
                
                if self.cursor_last_axis!=self.axes:
          
                    if self.hover_instance:

                        if self.hover_instance.show_cursor and self.x_hover_data and self.y_hover_data: 
                            xy_pos = self.cursor_last_axis.transData.transform([(self.x_hover_data,self.y_hover_data)]) 
                            self.hover_instance.y_hover_pos=float(xy_pos[0][1]) + self.y
                        
                    else:
                        y = self.horizontal_line.get_ydata() 
                        x = self.vertical_line.get_xdata()  
                        trans = self.cursor_last_axis.transData.inverted()
                        xy_pos = self.horizontal_line.axes.transData.transform([(x,y)])
                        xdata, ydata = trans.transform_point((xy_pos[0][0], xy_pos[0][1]))                        
                        self.horizontal_line.set_ydata(ydata)

    def hover(self, event) -> None:
        """ hover cursor method (cursor to nearest value)
        
        Args:
            event: touch kivy event
            
        Return:
            None
        
        """
           
        #if cursor is set -> hover is on
        if self.hover_on:
            
            #trick to improve app fps
            if self.max_hover_rate is not None:
                if self.last_hover_time is None:
                    self.last_hover_time = time.time()
                    
                elif time.time() - self.last_hover_time < self.max_hover_rate:
                    return
                else:
                    self.last_hover_time=None

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

                 self.cursor_last_axis=ax
                 #get datas from closest line
                 x = sel[0].target[0]
                 y = sel[0].target[1]

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
 
                             if pos_y<self.y+ax.bbox.bounds[1] + ax.bbox.bounds[3] and \
                                 pos_y>self.y+ax.bbox.bounds[1]:
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
                
                 if self.hover_instance.x_hover_pos>self.x+ax.bbox.bounds[2] + ax.bbox.bounds[0] or \
                     self.hover_instance.x_hover_pos<self.x+ax.bbox.bounds[0] or len(index_list)==nb_widget:              
                     self.hover_instance.hover_outside_bound=True                            
                 else:
                     self.hover_instance.hover_outside_bound=False                      
                
                 return

            else:
                x = sel.target[0]
                y = sel.target[1] 
               
                if not self.hover_instance:
                    self.set_cross_hair_visible(True)
                
                # update the cursor x,y data  
                ax=None
                line=sel.artist
                custom_x=None
                invert_xy = False
                if not hasattr(line,'axes'):
                   if hasattr(line,'_ContainerArtist__keep_alive'): 
                       if self.hist_range:
                           
                           x_hist, y_hist, width_hist, height_hist = line[sel.index].get_bbox().bounds
                           if line._ContainerArtist__keep_alive[0].container.orientation=='horizontal':
                               x_hist = y_hist
                               width_hist = height_hist 
                               invert_xy=True
                               x=line._ContainerArtist__keep_alive[0].container.datavalues[sel.index]
                           if self.cursor_xaxis_formatter:
                               custom_x = f"{self.cursor_xaxis_formatter.format_data(x_hist)}-{self.cursor_xaxis_formatter.format_data(x_hist+ width_hist)}" 
                           else:
                               custom_x = f"{x_hist}-{x_hist+ width_hist}"
                       
                       line =line._ContainerArtist__keep_alive[0]
                extra_data=None
                if hasattr(self.myevent.inaxes,'patch'):
                    if sel.artist is not self.myevent.inaxes.patch and hasattr(sel.artist,'get_cursor_data'):
                        extra_data = sel.artist.get_cursor_data(self.myevent)

                ax=line.axes
                    
                if ax is None:
                    return
                
                self.cursor_last_axis=ax
                
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
                        
                    if invert_xy:
                        self.hover_instance.label_y_value=f"{x}"
                    else:
                        self.hover_instance.label_y_value=f"{y}"
                        
                    if extra_data is not None:
                        self.hover_instance.label_y_value+=' [' + str(extra_data) + ']'
            
                    self.hover_instance.ymin_line = float(ax.bbox.bounds[1])  + self.y
                    self.hover_instance.ymax_line = float(ax.bbox.bounds[1] + ax.bbox.bounds[3])  + self.y
                    
                    if hasattr(line,'get_label'):
                        self.hover_instance.custom_label = line.get_label()
                    if hasattr(line,'get_color'):
                        self.hover_instance.custom_color = get_color_from_hex(to_hex(line.get_color()))
                    
                    if self.hover_instance.x_hover_pos>self.x+ax.bbox.bounds[2] + ax.bbox.bounds[0] or \
                        self.hover_instance.x_hover_pos<self.x+ax.bbox.bounds[0] or \
                        self.hover_instance.y_hover_pos>self.y+ax.bbox.bounds[1] + ax.bbox.bounds[3] or \
                        self.hover_instance.y_hover_pos<self.y+ax.bbox.bounds[1]:               
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
                    self.figcanvas.draw_idle()
                    self.figcanvas.flush_events()                   
                    self.background = self.figcanvas.copy_from_bbox(ax.figure.bbox)
                    self.set_cross_hair_visible(True)  
    
                self.figcanvas.restore_region(self.background)
                ax.draw_artist(self.text)
    
                ax.draw_artist(self.horizontal_line)
                ax.draw_artist(self.vertical_line)  
    
                #draw (blit method)
                self.figcanvas.blit(ax.bbox)                 
                self.figcanvas.flush_events()

    def apply_zoom(self, scale_factor, ax, anchor=(0, 0),new_line=None):
        """ zoom touch method """
                
        x = anchor[0]-self.pos[0]
        y = anchor[1]-self.pos[1]

        #manage press and drag
        if self._pick_info is None:
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
        for ax in self._pick_info:
            
            self.axes = ax

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

        self.update_cursor()
        
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
            
        else:
            self.figcanvas.draw_idle()
            self.figcanvas.flush_events()   


    def apply_pan(self, my_ax, event, mode='pan'):
        """ pan method """

        #manage press and drag
        if self._pick_info is None:
            self.myevent.x=event.x - self.pos[0]
            self.myevent.y=event.y - self.pos[1]
            self.myevent.inaxes=self.figure.canvas.inaxes((event.x - self.pos[0], 
                                                           event.y - self.pos[1])) 
            #press event
            axes = [a for a in self.figure.canvas.figure.get_axes()
                    if a.in_axes(self.myevent)]               
            if not axes: 
                if self.first_touch_pan!='pan' and self.interactive_axis:
                    axes = [a for a in self.figure.canvas.figure.get_axes()
                            if self.my_in_axes(a,self.myevent)] 

            self._pick_info = axes
            
        if not self._pick_info:
            return

        artists=[]
        for ax in self._pick_info:
            
            self.axes = ax

            artists.extend(_iter_axes_subartists(ax))

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
    
            xleft,xright=ax.get_xlim()
            ybottom,ytop=ax.get_ylim()
            
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
                xlabelsize = self.interactive_axis_pad
                ylabelsize = self.interactive_axis_pad                 
                
                xlabelbottom = ax.xaxis._major_tick_kw.get('tick1On')
                xlabeltop = ax.xaxis._major_tick_kw.get('tick2On')
                ylabelleft = ax.yaxis._major_tick_kw.get('tick1On')
                ylabelright = ax.yaxis._major_tick_kw.get('tick2On')
                
                # if (ydata < cur_ylim[0] and not inverted_y) or (ydata > cur_ylim[1] and inverted_y):
                if xlabelbottom and event.x>self.x +ax.bbox.bounds[0] and \
                    event.x<self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                    event.y>self.y + ax.bbox.bounds[1] - xlabelsize and \
                    event.y<self.y + ax.bbox.bounds[1]:                   
                                        
                    right_lim = self.x+ax.bbox.bounds[2]+ax.bbox.bounds[0]
                    left_lim = self.x+ax.bbox.bounds[0]
                    left_anchor_zone= (right_lim - left_lim)*.2 + left_lim
                    right_anchor_zone= (right_lim - left_lim)*.8 + left_lim

                    if event.x < left_anchor_zone or event.x > right_anchor_zone:
                        mode = 'adjust_x'
                    else:
                        mode = 'pan_x'
                    self.touch_mode = mode
                # elif (xdata < cur_xlim[0] and not inverted_x) or (xdata > cur_xlim[1] and inverted_x):
                elif ylabelleft and  event.x>self.x +ax.bbox.bounds[0] - ylabelsize and \
                    event.x<self.x + ax.bbox.bounds[0] and \
                    event.y<self.y + ax.bbox.bounds[1] + ax.bbox.bounds[3] and \
                    event.y>self.y + ax.bbox.bounds[1]:
                    
                    top_lim = self.y+ax.bbox.bounds[3]+ax.bbox.bounds[1]
                    bottom_lim = self.y+ax.bbox.bounds[1]                    
                    bottom_anchor_zone=  (top_lim - bottom_lim)*.2 + bottom_lim
                    top_anchor_zone= (top_lim - bottom_lim)*.8 + bottom_lim  

                    if event.y < bottom_anchor_zone or event.y > top_anchor_zone:
                        mode = 'adjust_y'
                    else:
                        mode= 'pan_y' 
                    self.touch_mode = mode
                
                elif ylabelright and event.x<self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] + self.interactive_axis_pad and \
                    event.x>self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                    event.y<self.y + ax.bbox.bounds[1] + ax.bbox.bounds[3] and \
                    event.y>self.y + ax.bbox.bounds[1]:                     

                    top_lim = self.y+ax.bbox.bounds[3]+ax.bbox.bounds[1]
                    bottom_lim = self.y+ax.bbox.bounds[1]                    
                    bottom_anchor_zone=  (top_lim - bottom_lim)*.2 + bottom_lim
                    top_anchor_zone= (top_lim - bottom_lim)*.8 + bottom_lim  

                    if event.y < bottom_anchor_zone or event.y > top_anchor_zone:
                        mode = 'adjust_y'
                    else:
                        mode= 'pan_y' 
                    self.touch_mode = mode 

                elif xlabeltop and xlabelbottom and event.x>self.x +ax.bbox.bounds[0] and \
                    event.x<self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                    event.y>self.y + ax.bbox.bounds[1] + xlabelsize and \
                    event.y<self.y + ax.bbox.bounds[1]:                    
                    right_lim = self.x+ax.bbox.bounds[2]+ax.bbox.bounds[0]
                    left_lim = self.x+ax.bbox.bounds[0]
                    left_anchor_zone= (right_lim - left_lim)*.2 + left_lim
                    right_anchor_zone= (right_lim - left_lim)*.8 + left_lim

                    if event.x < left_anchor_zone or event.x > right_anchor_zone:
                        mode = 'adjust_x'
                    else:
                        mode = 'pan_x'
                    self.touch_mode = mode                    
                else:
                    self.touch_mode = 'pan'
    
            if not mode=='pan_y' and not mode=='adjust_y':             
                if mode=='adjust_x':
                    if self.anchor_x is None: 
                        midpoint =  ((self.x+ax.bbox.bounds[2] + ax.bbox.bounds[0]) + (self.x+ax.bbox.bounds[0]))/2
                        if event.x > midpoint:
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
                        midpoint =  ((self.y+ax.bbox.bounds[3] + ax.bbox.bounds[1]) + (self.y+ax.bbox.bounds[1]))/2
                        if event.y  > midpoint:
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

        self.update_cursor()
        
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
            
        else:
            self.figcanvas.draw_idle()
            self.figcanvas.flush_events()                    

    def on_touch_up(self, event):
        """ Manage Mouse/touch release """
        # remove it from our saved touches
        if event in self._touches and event.grab_state:
            event.ungrab(self)
            del self._last_touch_pos[event]
            self._touches.remove(event)
            if self.touch_mode=='pan' or self.touch_mode=='zoombox' or \
                self.touch_mode=='pan_x' or self.touch_mode=='pan_y' \
                or self.touch_mode=='adjust_x' or self.touch_mode=='adjust_y':   
                self.push_current()
                self._pick_info=None
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

    def draw_box(self, event, x0, y0, x1, y1,onpress=False) -> None:
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
        
        if onpress:
            ax = self.figure.canvas.inaxes((event.x - self.pos[0], 
                                            event.y - self.pos[1]))
            if ax is None:
                return
            self.axes = ax
        else:
            ax=self.axes  

        trans = ax.transData.inverted()
        xdata, ydata = trans.transform_point((event.x-pos_x, event.y-pos_y)) 

        xleft,xright=ax.get_xlim()
        ybottom,ytop=ax.get_ylim()
        
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
            x1_min = ax.transData.transform([(xmin,ymin)])
            if (x1<x0 and not inverted_x) or (x1>x0 and inverted_x):
                x1=x1_min[0][0]+pos_x
            else:
                x0=x1_min[0][0]

        if xdata>xmax:
            x0_max = ax.transData.transform([(xmax,ymin)])
            if (x1>x0 and not inverted_x) or (x1<x0 and inverted_x):
                x1=x0_max[0][0]+pos_x 
            else:
                x0=x0_max[0][0]                  

        if ydata<ymin:
            y1_min = ax.transData.transform([(xmin,ymin)])
            if (y1<y0 and not inverted_y) or (y1>y0 and inverted_y):
                y1=y1_min[0][1]+pos_y
            else:
                y0=y1_min[0][1]+pos_y

        if ydata>ymax:
            y0_max = ax.transData.transform([(xmax,ymax)])
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
        
    def _draw_bitmap(self):
        """ draw bitmap method. based on kivy scatter method"""
        if self._bitmap is None:
            print("No bitmap!")
            return
        self._img_texture = Texture.create(size=(self.bt_w, self.bt_h))
        self._img_texture.blit_buffer(
            bytes(self._bitmap), colorfmt="rgba", bufferfmt='ubyte')
        self._img_texture.flip_vertical()
        
        if self.hover_instance:
            if self.compare_xdata and self.hover_instance:
                if (self.touch_mode!='cursor' or len(self._touches) > 1) and not self.show_compare_cursor:
                    self.hover_instance.hover_outside_bound=True
  
                elif self.show_compare_cursor and self.touch_mode=='cursor':
                    self.show_compare_cursor=False
                else:
                    self.hover_instance.hover_outside_bound=True

            #update hover pos if needed
            elif self.hover_instance.show_cursor and self.x_hover_data and self.y_hover_data:      
                if self.cursor_last_axis:
                    xy_pos = self.cursor_last_axis.transData.transform([(self.x_hover_data,self.y_hover_data)])
                else:
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