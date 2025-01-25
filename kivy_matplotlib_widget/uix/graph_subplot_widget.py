""" Custom MatplotFigure 
"""

import math
import copy
import time

import matplotlib
matplotlib.use('Agg')
from kivy_matplotlib_widget.uix.graph_widget import _FigureCanvas ,MatplotFigure
from kivy.utils import get_color_from_hex
from matplotlib.colors import to_hex
from kivy.metrics import dp
from kivy_matplotlib_widget.tools.cursors import cursor
from kivy.properties import NumericProperty,BooleanProperty,OptionProperty
from kivy.graphics.texture import Texture
import matplotlib.image as mimage
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms
from matplotlib.container import BarContainer

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
    myevent_cursor = MatplotlibEvent()
    interactive_axis_pad= NumericProperty(dp(100))
    _pick_info = None
    draw_all_axes = BooleanProperty(False)
    max_hover_rate =  NumericProperty(None,allownone=True) 
    last_hover_time=None   
    cursor_last_axis=None
    current_anchor_axis=None
    min_max_option = BooleanProperty(False)
    box_axes=[]  

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
                   
            #check if tick zone
            #y left axis
            if ylabelleft and  mouseevent.x > ax.bbox.bounds[0] - ylabelsize and \
                mouseevent.x < ax.bbox.bounds[0] and \
                mouseevent.y < ax.bbox.bounds[1] + ax.bbox.bounds[3] and \
                mouseevent.y > ax.bbox.bounds[1]:
                result2 = True

            #x bottom axis
            elif xlabelbottom and mouseevent.x > ax.bbox.bounds[0] and \
                mouseevent.x < ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                mouseevent.y > ax.bbox.bounds[1] - xlabelsize and \
                mouseevent.y < ax.bbox.bounds[1]:
                result2 = True

            #y right axis                 
            elif ylabelright and mouseevent.x < ax.bbox.bounds[2] + ax.bbox.bounds[0] + self.interactive_axis_pad and \
                mouseevent.x > ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                mouseevent.y < ax.bbox.bounds[1] + ax.bbox.bounds[3] and \
                mouseevent.y > ax.bbox.bounds[1]:                     
                result2 = True

            # #x top axis
            elif xlabeltop and mouseevent.x > ax.bbox.bounds[0] and \
                mouseevent.x < ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                mouseevent.y > ax.bbox.bounds[1] + ax.bbox.bounds[3] and \
                mouseevent.y < ax.bbox.bounds[1] + ax.bbox.bounds[3] + xlabelsize:
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

        if len(self.figure.axes) > 0 and self.figure.axes[0]:
            #add copy patch
            for ax in self.figure.axes:
                # ax=self.figure.axes[0]
                patch_cpy=copy.copy(ax.patch)
                patch_cpy.set_visible(False)
                if hasattr(ax,'PolarTransform'):
                    for pos in list(ax.spines._dict.keys()):
                        ax.spines[pos].set_zorder(10)
                    #note: make an other widget if you need polar graph with other type of graph
                    self.disabled = True #polar graph do not handle pan/zoom
                else:
                    for pos in ['right', 'top', 'bottom', 'left']:
                        ax.spines[pos].set_zorder(10)
                patch_cpy.set_zorder(9)
                self.background_patch_copy.append(ax.add_patch(patch_cpy))
            
            #set default axes
            self.axes = self.figure.axes[0]
            self.cursor_last_axis = self.figure.axes[0]
            
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
            #remove all legend_instance from parent widget
            for current_legend in self.legend_instance:
                current_legend.parent.remove_widget(current_legend)
            self.legend_instance=[]
            
        if self.auto_cursor and len(self.figure.axes) > 0:
            lines=[]
            for ax in self.figure.axes:
                if ax.lines:
                    lines.extend(ax.lines)
            self.register_lines(lines) #create maplotlib text and cursor (if needed)
            self.register_cursor()
            
        # Texture
        self._img_texture = Texture.create(size=(w, h))
        
        #close last figure in memory (avoid max figure warning)
        matplotlib.pyplot.close()
        
    def __init__(self, **kwargs):
        self.kv_post_done = False
        self.selector = None        
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

    def autoscale(self):
        if self.disabled:
            return
        axes=self.figure.axes
        for i,ax in enumerate(axes):
            twinx = any(ax.get_shared_x_axes().joined(ax, prev)
                        for prev in axes[:i])
            
            twiny = any(ax.get_shared_y_axes().joined(ax, prev)
                        for prev in axes[:i])
            
            autoscale_axis = self.autoscale_axis
            if twinx:
                autoscale_axis = "y"
            if twiny:
                autoscale_axis = "x"
            no_visible = self.myrelim(ax,visible_only=self.autoscale_visible_only)
            ax.autoscale_view(tight=self.autoscale_tight,
                              scalex=True if autoscale_axis!="y" else False, 
                              scaley=True if autoscale_axis!="x" else False)
            ax.autoscale(axis=autoscale_axis,tight=self.autoscale_tight)  
    
            current_xlim = ax.get_xlim()
            current_ylim = ax.get_ylim()
            lim_collection,invert_xaxis,invert_yaxis = self.data_limit_collection(ax,visible_only=self.autoscale_visible_only)
            if lim_collection:
                xchanged=False
                if self.autoscale_tight:
                    current_margins = (0,0)
                else:
                    current_margins = ax.margins()
                
                if self.autoscale_axis!="y":
                    if invert_xaxis:
                        if lim_collection[0]>current_xlim[0] or no_visible:
                            ax.set_xlim(left=lim_collection[0])
                            xchanged=True
                        if lim_collection[2]<current_xlim[1] or no_visible:
                            ax.set_xlim(right=lim_collection[2])
                            xchanged=True                
                    else:
                        if lim_collection[0]<current_xlim[0] or no_visible:
                            ax.set_xlim(left=lim_collection[0])
                            xchanged=True
                        if lim_collection[2]>current_xlim[1] or no_visible:
                            ax.set_xlim(right=lim_collection[2])
                            xchanged=True
                    
                #recalculed margin
                if xchanged:
                    xlim =  ax.get_xlim()
                    ax.set_xlim(left=xlim[0] - current_margins[0]*(xlim[1]-xlim[0]))
                    ax.set_xlim(right=xlim[1] + current_margins[0]*(xlim[1]-xlim[0]))
                    
                ychanged=False 
                
                if self.autoscale_axis!="x":
                    if invert_yaxis:
                        if lim_collection[1]>current_ylim[0] or no_visible:
                            ax.set_ylim(bottom=lim_collection[1])
                            ychanged=True
                        if lim_collection[3]<current_ylim[1] or no_visible:
                            ax.set_ylim(top=lim_collection[3]) 
                            ychanged=True
                    else:
                        if lim_collection[1]<current_ylim[0] or no_visible:
                            ax.set_ylim(bottom=lim_collection[1])
                            ychanged=True
                        if lim_collection[3]>current_ylim[1] or no_visible:
                            ax.set_ylim(top=lim_collection[3]) 
                            ychanged=True
                    
                if ychanged:
                    ylim =  ax.get_ylim()
                    ax.set_ylim(bottom=ylim[0] - current_margins[1]*(ylim[1]-ylim[0]))
                    ax.set_ylim(top=ylim[1] + current_margins[1]*(ylim[1]-ylim[0]))   
    
            index = self.figure.axes.index(ax)
            self.xmin[index],self.xmax[index] = ax.get_xlim()
            self.ymin[index],self.ymax[index] = ax.get_ylim()
        ax.set_autoscale_on(False)
            
        ax.figure.canvas.draw_idle()
        ax.figure.canvas.flush_events() 
        

    def myrelim(self,ax, visible_only=False):
       """
       Recompute the data limits based on current artists.

       At present, `.Collection` instances are not supported.

       Parameters
       ----------
       visible_only : bool, default: False
           Whether to exclude invisible artists.
       """
       # Collections are deliberately not supported (yet); see
       # the TODO note in artists.py.
       ax.dataLim.ignore(True)
       ax.dataLim.set_points(mtransforms.Bbox.null().get_points())
       ax.ignore_existing_data_limits = True
       no_visible=True
       for artist in ax._children:
           if not visible_only or artist.get_visible():
               if isinstance(artist, mlines.Line2D):
                   ax._update_line_limits(artist)
                   no_visible=False
               elif isinstance(artist, mpatches.Patch):
                   ax._update_patch_limits(artist)
                   no_visible=False
               elif isinstance(artist, mimage.AxesImage):
                   ax._update_image_limits(artist)   
                   no_visible=False
        
       return no_visible
   
    def data_limit_collection(self,ax,visible_only=False):
        datalim = None
        datalim_list = []
        for collection in ax.collections:
            eval_lim=True
            if visible_only:
                if not collection.get_visible():
                    eval_lim=False
                    
            if eval_lim:
                datalim_list.append(collection.get_datalim(ax.transData))

        invert_xaxis=False
        invert_yaxis=False
        if datalim_list:
            if ax.xaxis_inverted():
                invert_xaxis=True
            if ax.yaxis_inverted():
                invert_yaxis=True              
            for i,current_datalim in enumerate(datalim_list):
                if i==0:
                    if invert_xaxis:
                        xleft = current_datalim.x1
                        xright = current_datalim.x0
                    else:
                        xleft = current_datalim.x0
                        xright = current_datalim.x1 
                    if invert_yaxis:
                        ybottom = current_datalim.y1
                        ytop = current_datalim.y0  
                    else:
                        ybottom = current_datalim.y0
                        ytop = current_datalim.y1
                      
                else:                   
                    if invert_xaxis:
                        if current_datalim.x1>xleft:
                            xleft = current_datalim.x1
                        if current_datalim.x0<xright:
                            xright = current_datalim.x0                       
                    else:
                        if current_datalim.x0<xleft:
                            xleft = current_datalim.x0
                        if current_datalim.x1>xright:
                            xright = current_datalim.x1
                    if invert_yaxis:
                        if current_datalim.y1>ybottom:
                            ybottom = current_datalim.y1
                        if current_datalim.y0<ytop:    
                            ytop = current_datalim.y0                        
                    else:
                        if current_datalim.y0<ybottom:
                            ybottom = current_datalim.y0
                        if current_datalim.y1>ytop:    
                            ytop = current_datalim.y1                    

            datalim = [xleft,ybottom,xright,ytop]
               
        return datalim,invert_xaxis,invert_yaxis   

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
    
            ax.figure.canvas.draw_idle()
            ax.figure.canvas.flush_events() 

    def get_data_xy(self,x,y):
        """ manage x y data in navigation bar """
        self.myevent_cursor.x=x - self.pos[0]
        self.myevent_cursor.y=y - self.pos[1]
        self.myevent_cursor.inaxes=self.figure.canvas.inaxes((x - self.pos[0],
                                                              y - self.pos[1]))               
        #find all axis
        axes = [a for a in self.figure.canvas.figure.get_axes()
                if a.in_axes(self.myevent_cursor)]  
        
        if axes:
            trans = axes[0].transData.inverted() #always use first axis
            xdata, ydata = trans.transform_point((x - self.pos[0],
                                                  y - self.pos[1]))
    
            if self.cursor_xaxis_formatter:
                x_format = self.cursor_xaxis_formatter.format_data(xdata) 
            else:
                x_format = self.axes.xaxis.get_major_formatter().format_data_short(xdata)
            
            if self.cursor_yaxis_formatter:
                y_format = self.cursor_yaxis_formatter.format_data(ydata) 
            else:
                y_format = self.axes.yaxis.get_major_formatter().format_data_short(ydata)
                
            return x_format,y_format
        else:
            return None,None

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
                if not self.disable_mouse_scrolling:
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
                         if self.hist_range and isinstance(line,BarContainer):
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
                                 else:
                                     y = ax.yaxis.get_major_formatter().format_data_short(y)
                                 available_widget[index].label_y_value=f"{y}"
                                 available_widget[index].show_widget=True
                                 index_list.remove(index)
                                 
                 if i<nb_widget-1:
                     for ii in index_list:
                         available_widget[ii].show_widget=False

                 if self.cursor_xaxis_formatter:
                     x = self.cursor_xaxis_formatter.format_data(x) 
                 else:
                     x = ax.xaxis.get_major_formatter().format_data_short(x)
                 self.hover_instance.label_x_value=f"{x}"

                 if hasattr(self.hover_instance,'overlap_check'):
                     self.hover_instance.overlap_check()

                 self.hover_instance.xmin_line = float(ax.bbox.bounds[0]) + self.x
                 self.hover_instance.xmax_line = float(ax.bbox.bounds[0] + ax.bbox.bounds[2]) + self.x                              
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
                       
                       if self.hist_range and isinstance(line,BarContainer):
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
                    self.horizontal_line.set_ydata([y,])
                    
                if hasattr(self,'vertical_line'):
                    self.vertical_line.set_xdata([x,])
    
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

                    self.hover_instance.xmin_line = float(ax.bbox.bounds[0]) + self.x
                    self.hover_instance.xmax_line = float(ax.bbox.bounds[0] + ax.bbox.bounds[2]) + self.x            
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

    def zoom_factory(self, event, base_scale=1.1):
        """ zoom with scrolling mouse method """

        x = event.x - self.pos[0]
        y = event.y - self.pos[1]

        if not self._pick_info:
            self.myevent.x=event.x - self.pos[0]
            self.myevent.y=event.y - self.pos[1]
            self.myevent.inaxes=self.figure.canvas.inaxes((x,y))               
            #press event
            axes = [a for a in self.figure.canvas.figure.get_axes()
                    if a.in_axes(self.myevent)]               

            self._pick_info = axes
            
        if not self._pick_info:
            return        

        for i,ax in enumerate(self._pick_info):
            self.axes = ax
            
            twinx = any(ax.get_shared_x_axes().joined(ax, prev)
                        for prev in self._pick_info[:i])
            
            twiny = any(ax.get_shared_y_axes().joined(ax, prev)
                        for prev in self._pick_info[:i])
            
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

        self._pick_info = None
        ax.figure.canvas.draw_idle()
        ax.figure.canvas.flush_events()

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
            xdata, ydata = trans.transform_point((x+new_line.x, y+new_line.y))        
            
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


    def apply_pan(self, my_ax, event, mode='pan'):
        """ pan method """

        #manage press and drag
        if not self._pick_info:
            self.myevent.x=event.x - self.pos[0]
            self.myevent.y=event.y - self.pos[1]
            self.myevent.inaxes=self.figure.canvas.inaxes((event.x, 
                                                           event.y)) 
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
        for i,ax in enumerate(self._pick_info):
            
            self.axes = ax

            artists.extend(_iter_axes_subartists(ax))

            twinx = any(ax.get_shared_x_axes().joined(ax, prev)
                        for prev in self._pick_info[:i])
            
            twiny = any(ax.get_shared_y_axes().joined(ax, prev)
                        for prev in self._pick_info[:i])

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
                        self.current_anchor_axis = ax
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
                        self.current_anchor_axis = ax
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
                        self.current_anchor_axis = ax
                    else:
                        mode= 'pan_y' 
                    self.touch_mode = mode 

                elif xlabeltop and event.x>self.x +ax.bbox.bounds[0] and \
                    event.x<self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                    event.y>self.y +ax.bbox.bounds[1] + ax.bbox.bounds[3] and \
                    event.y<self.y + ax.bbox.bounds[1] + ax.bbox.bounds[3] + xlabelsize:                  
                    right_lim = self.x+ax.bbox.bounds[2]+ax.bbox.bounds[0]
                    left_lim = self.x+ax.bbox.bounds[0]
                    left_anchor_zone= (right_lim - left_lim)*.2 + left_lim
                    right_anchor_zone= (right_lim - left_lim)*.8 + left_lim

                    if event.x < left_anchor_zone or event.x > right_anchor_zone:
                        mode = 'adjust_x'
                        self.current_anchor_axis = ax
                    else:
                        mode = 'pan_x'
                    self.touch_mode = mode                    
                else:
                    self.touch_mode = 'pan'
    
            if not mode=='pan_y' and not mode=='adjust_y':             
                if mode=='adjust_x':
                    if self.current_anchor_axis == ax:
                        if self.anchor_x is None: 
                            midpoint =  ((self.x+ax.bbox.bounds[2] + ax.bbox.bounds[0]) + (self.x+ax.bbox.bounds[0]))/2
                            if event.x > midpoint:
                                if inverted_x:
                                    self.anchor_x='right'
                                else:
                                    self.anchor_x='left'
                            else:
                                if inverted_x:
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
                                if inverted_x:
                                    ax.set_xlim(None,cur_xlim[0])
                                else:
                                    ax.set_xlim(cur_xlim[0],None)
                else:
                   if not twinx:
                        if scale == 'linear':
                            cur_xlim -= dx
                        else:
                            try:
                                cur_xlim = [self.inv_transform_eval((self.transform_eval(cur_xlim[0],ax.xaxis) - dx),ax.xaxis),
                                            self.inv_transform_eval((self.transform_eval(cur_xlim[1],ax.xaxis) - dx),ax.xaxis)]  
                            except (ValueError, OverflowError):
                                cur_xlim = cur_xlim  # Keep previous limits                   
                        if inverted_x:
                            ax.set_xlim(cur_xlim[1],cur_xlim[0])
                        else:
                            ax.set_xlim(cur_xlim)
                    
            if not mode=='pan_x' and not mode=='adjust_x':
                if mode=='adjust_y':
                    if self.current_anchor_axis == ax:
                        if self.anchor_y is None:
                            midpoint =  ((self.y+ax.bbox.bounds[3] + ax.bbox.bounds[1]) + (self.y+ax.bbox.bounds[1]))/2
                            if event.y  > midpoint:
                                if inverted_y:
                                    self.anchor_y='bottom' 
                                else:
                                    self.anchor_y='top'
                            else:
                                if inverted_y:
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
                    if not twiny:
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

        if self.first_touch_pan is None:
            self.first_touch_pan=self.touch_mode
        
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

    def update_hover(self):
        """ update hover on fast draw (if exist)"""
        if self.hover_instance:
            #update hover pos if needed
            if self.hover_instance.show_cursor and self.x_hover_data and self.y_hover_data: 
                # if self.cursor_last_axis.axes==self.axes:
                xy_pos = self.cursor_last_axis.transData.transform([(self.x_hover_data,self.y_hover_data)]) 
                self.hover_instance.x_hover_pos=float(xy_pos[0][0]) + self.x
                self.hover_instance.y_hover_pos=float(xy_pos[0][1]) + self.y

                self.hover_instance.xmin_line = float(self.axes.bbox.bounds[0]) + self.x
                self.hover_instance.xmax_line = float(self.axes.bbox.bounds[0] + self.axes.bbox.bounds[2]) + self.x                    
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
        
        self.myevent.x=event.x  - self.pos[0]
        self.myevent.y=event.y  - self.pos[1]
        self.myevent.inaxes=self.figure.canvas.inaxes((event.x, 
                                                       event.y)) 
        axes = [a for a in self.figure.canvas.figure.get_axes()
                if self.my_in_axes(a,self.myevent)] 

        for ax in axes:

            xlabelsize = self.interactive_axis_pad
            ylabelsize = self.interactive_axis_pad            
            xlabelbottom = ax.xaxis._major_tick_kw.get('tick1On')
            xlabeltop = ax.xaxis._major_tick_kw.get('tick2On')
            ylabelleft = ax.yaxis._major_tick_kw.get('tick1On')
            ylabelright = ax.yaxis._major_tick_kw.get('tick2On')

            if xlabelbottom and event.x>self.x +ax.bbox.bounds[0] and \
                event.x<self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                event.y>self.y + ax.bbox.bounds[1] - xlabelsize and \
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

            elif ylabelleft and  event.x>self.x +ax.bbox.bounds[0] - ylabelsize and \
                event.x<self.x + ax.bbox.bounds[0] and \
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
            elif ylabelright and event.x<self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] + ylabelsize and \
                event.x>self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
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
                                self.text_instance.x_text_pos=float(self.x+ax.bbox.bounds[0] + ax.bbox.bounds[2]) + dp(40)
                                self.text_instance.y_text_pos=float(self.y+ax.bbox.bounds[1] + ax.bbox.bounds[3]) - self.text_instance.text_height
                                self.text_instance.offset_text = True
                            else:
                    
                                anchor='bottom'
                                self.text_instance.x_text_pos=float(self.x+ax.bbox.bounds[0] + ax.bbox.bounds[2]) + dp(40)
                                self.text_instance.y_text_pos=float(self.y+ax.bbox.bounds[1]) - dp(6)
                                self.text_instance.offset_text = True
                            self.text_instance.current_axis = ax
                            self.text_instance.kind = {'axis':'y','anchor':anchor}
                                
                            self.text_instance.show_text=True
                            return 
                        
            elif xlabeltop and event.x>self.x +ax.bbox.bounds[0] and \
                event.x<self.x + ax.bbox.bounds[2] + ax.bbox.bounds[0] and \
                event.y>self.y +ax.bbox.bounds[1] + ax.bbox.bounds[3] and \
                event.y<self.y + ax.bbox.bounds[1] + ax.bbox.bounds[3] + xlabelsize:                    
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
                                self.text_instance.y_text_pos=float(self.y+ax.bbox.bounds[1] + ax.bbox.bounds[3]) + dp(2)
                                self.text_instance.offset_text = False
                            else:
                                anchor='right'
                                self.text_instance.x_text_pos=float(self.x+ax.bbox.bounds[2] + ax.bbox.bounds[0])
                                self.text_instance.y_text_pos=float(self.y+ax.bbox.bounds[1] + ax.bbox.bounds[3]) + dp(2)
                                self.text_instance.offset_text = True
                                
                            self.text_instance.current_axis = ax
                            self.text_instance.kind = {'axis':'x','anchor':anchor}
                                
                            self.text_instance.show_text=True
                            return
        
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
            
            self.myevent.x=event.x - self.pos[0]
            self.myevent.y=event.y - self.pos[1]
            self.myevent.inaxes=self.figure.canvas.inaxes((event.x - self.pos[0], 
                                                           event.y - self.pos[1])) 
            
            self.box_axes = [a for a in self.figure.canvas.figure.get_axes()
                    if a.in_axes(self.myevent)]   
            
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
        
    def update_lim(self):
        """ update axis lim if zoombox is used"""
        ax=self.axes

        self.do_update=False
        
        if not self.box_axes:

            self.box_axes=[ax]
            
        for index,ax in enumerate(self.box_axes):
            #check if inverted axis
            xleft,xright=ax.get_xlim()
            ybottom,ytop=ax.get_ylim()
            
            if xright>xleft:
                ax.set_xlim(left=min(self.x0_box[index],self.x1_box[index]),right=max(self.x0_box[index],self.x1_box[index]))
            else:
                ax.set_xlim(right=min(self.x0_box[index],self.x1_box[index]),left=max(self.x0_box[index],self.x1_box[index]))
            if ytop>ybottom:
                ax.set_ylim(bottom=min(self.y0_box[index],self.y1_box[index]),top=max(self.y0_box[index],self.y1_box[index]))
            else:
                ax.set_ylim(top=min(self.y0_box[index],self.y1_box[index]),bottom=max(self.y0_box[index],self.y1_box[index]))    

    def reset_box(self):
        """ reset zoombox and apply zoombox limit if zoombox option if selected"""
        if min(abs(self._box_size[0]),abs(self._box_size[1]))>self.minzoom:
            self.x0_box, self.y0_box = [], []
            self.x1_box, self.y1_box = [], [] 
            for ax in self.box_axes:
                trans = ax.transData.inverted()
                x0_box, y0_box = trans.transform_point((self._box_pos[0]-self.pos[0], self._box_pos[1]-self.pos[1])) 
                x1_box, y1_box = trans.transform_point((self._box_size[0]+self._box_pos[0]-self.pos[0], self._box_size[1]+self._box_pos[1]-self.pos[1]))
                self.x0_box.append(x0_box)
                self.y0_box.append(y0_box)
                self.x1_box.append(x1_box)
                self.y1_box.append(y1_box)
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