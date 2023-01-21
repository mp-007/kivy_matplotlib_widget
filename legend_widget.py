from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.config import Config
from kivy.utils import platform
from functools import partial

from kivy.properties import (
    StringProperty,
    ObjectProperty,
    NumericProperty,
    ListProperty,
    BooleanProperty,
    ColorProperty
    )

from kivy.lang import Builder
from kivy.uix.widget import Widget
from matplotlib.colors import to_hex
import matplotlib as mpl
from math import ceil
import numpy as np


class LegendGestures(Widget):
    """ This widget is based on CommonGestures from gestures4kivy project
    https://github.com/Android-for-Python/gestures4kivy
      
    For more gesture features like long press or swipe, replace LegendGestures
    by CommonGestures (available on gestures4kivy project).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mobile = platform == 'android' or platform == 'ios'
        self._new_gesture()
        #### Sensitivity
        self._DOUBLE_TAP_TIME     = Config.getint('postproc',
                                                  'double_tap_time') / 1000
        self._DOUBLE_TAP_DISTANCE = Config.getint('postproc',
                                                  'double_tap_distance')

        self._persistent_pos = [(0,0),(0,0)]


    #####################
    # Kivy Touch Events
    #####################
    # In the case of a RelativeLayout, the touch.pos value is not persistent.
    # Because the same Touch is called twice, once with Window relative and
    # once with the RelativeLayout relative values. 
    # The on_touch_* callbacks have the required value because of collide_point
    # but only within the scope of that touch callback.
    #
    # This is an issue for gestures with persistence, for example two touches.
    # So if we have a RelativeLayout we can't rely on the value in touch.pos .
    # So regardless of there being a RelativeLayout, we save each touch.pos
    # in self._persistent_pos[] and use that when the current value is
    # required. 
    
    ### touch down ###
    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            if len(self._touches) == 1 and touch.id == self._touches[0].id:
                # Filter noise from Kivy, one touch.id touches down twice
                pass
            elif platform == 'ios' and 'mouse' in str(touch.id):
                # Filter more noise from Kivy, extra mouse events
                return super().on_touch_down(touch)
            else:
                self._touches.append(touch)

            if len(self._touches) == 1:
                if 'button' in touch.profile and touch.button == 'right':
                    # Two finger tap or right click
                    pass
                else:
                    self._gesture_state = 'Dont Know' 
                    # schedule a posssible tap 
                    if not self._single_tap_schedule:
                        self._single_tap_schedule =\
                            Clock.schedule_once(partial(self._single_tap_event,
                                                        touch ,
                                                        touch.x, touch.y),
                                                self._DOUBLE_TAP_TIME)

                self._persistent_pos[0] = tuple(touch.pos)
            elif len(self._touches) == 2:
                # two fingers 
                self._not_single_tap()
                self._persistent_pos[1] = tuple(touch.pos)

        return super().on_touch_down(touch)

    ### touch up ###
    def on_touch_up(self, touch):
        if touch in self._touches:

            x, y = self._pos_to_widget(touch.x, touch.y)

            if self._gesture_state == 'Dont Know':
                if touch.is_double_tap:
                    self._not_single_tap()
                    self.cg_double_tap(touch, x, y)
                    self._new_gesture()
                else:
                    self._remove_gesture(touch)
            else:
                self._new_gesture()

        return super().on_touch_up(touch)                

    ############################################
    # gesture utilities
    ############################################
    #

    ### single tap clock ###
    def _single_tap_event(self, touch, x, y, dt):
        if self._gesture_state == 'Dont Know':
            if not self._long_press_schedule:
                x, y = self._pos_to_widget(x, y)
                self.cg_tap(touch,x,y)
                self._new_gesture()

    def _not_single_tap(self):
        if self._single_tap_schedule:
            Clock.unschedule(self._single_tap_schedule)
            self._single_tap_schedule = None


    ### Every result is in the self frame ###

    def _pos_to_widget(self, x, y):
        return (x - self.x, y - self.y)

    ### gesture utilities ###

    def _remove_gesture(self, touch):
        if touch and len(self._touches):
            if touch in self._touches:
                self._touches.remove(touch)
            
    def _new_gesture(self):
        self._touches = []
        self._long_press_schedule = None
        self._single_tap_schedule = None
        self._velocity_schedule = None
        self._gesture_state = 'None'
        self._finger_distance = 0
        self._velocity = 0


    ############################################
    # User Events
    # define some subset in the derived class
    ############################################

    ############# Tap, Double Tap, and Long Press
    def cg_tap(self, touch, x, y):
        pass

    def cg_double_tap(self, touch, x, y):
        pass

class LegendRv(BoxLayout):
    """Legend class
    
    """     
    figure_wgt = ObjectProperty(None) 
    data=ListProperty()
    text_color=ColorProperty([0,0,0,1])
    background_color=ColorProperty([1,1,1,1])

    def __init__(self, **kwargs):
        """init class
        
        """ 
        super(LegendRv, self).__init__(**kwargs)
        self.data=[]        

    def set_data(self,content:list) -> None:
        """set legend data 
        
        Args:
            content (list):list of dictionary with matplotlib line(s) 
            
        Returns:
            None
        """       
        self.data=[]
        
        #reset scroll
        self.ids.view.scroll_y = 1

        for i,row_content in enumerate(content):
        
            r_data = {
                "row_index":int(i),
                "viewclass": "CellLegend"
                }
            r_data["text"] = str(row_content.get_label())
            r_data["mycolor"] = get_color_from_hex(to_hex(row_content.get_color()))
            r_data["line_type"] = row_content.get_linestyle()
            r_data["legend_rv"] = self  
            r_data["selected"] = False
            r_data["matplotlib_line"] = row_content
            r_data["text_color"] = self.text_color

            self.data.append(r_data)
       
    def add_data(self,line) -> None:
        """add line method
        
        Args:
            line:matplotlib line
            
        Returns:
            None
        """  
        nb_data=len(self.data)
        r_data = {
            "row_index":int(nb_data),
            "viewclass": "CellLegend"
            }
        r_data["text"] = str(line.get_label())
        r_data["mycolor"] = get_color_from_hex(to_hex(line.get_color()))
        r_data["line_type"] = line.get_linestyle()
        r_data["legend_rv"] = self  
        r_data["selected"] = False
        r_data["matplotlib_line"] = line
        r_data["text_color"] = self.text_color

        self.data.append(r_data)
        self.figure_wgt.figure.canvas.draw_idle()
        self.figure_wgt.figure.canvas.flush_events()  
            
    def remove_data(self,remove_line) -> None:
        """add line method
        
        Args:
            remove_line: matplotlib line
            
        Returns:
            None
        """     
        for idx,line in enumerate(self.figure_wgt.axes.lines):
            if line == remove_line:
                remove_idx=idx
                break        
        del self.data[remove_idx]
        remove_line.remove()
        self.figure_wgt.figure.canvas.draw_idle()
        self.figure_wgt.figure.canvas.flush_events()  
        
    def show_hide_wgt(self,row_index) -> None:
        if self.data[row_index]["selected"]:
            #show line
            self.data[row_index]["selected"] = False
            self.data[row_index]["matplotlib_line"].set_visible(True)
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()             
        else:
            #hide line
            self.data[row_index]["selected"] = True
            self.data[row_index]["matplotlib_line"].set_visible(False)
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()            
        self.ids.view.refresh_from_layout()
           
    def doubletap(self,row_index) -> None:  
        """ double tap behavior is based on plotly behavior """
        if not self.data[row_index]["selected"]:
            current_line = self.data[row_index]["matplotlib_line"]
            if current_line.get_visible():
                #check if we isolate line or show all lines
                need_isolate = False
                for line in self.figure_wgt.axes.lines:
                    if line != current_line and line.get_visible():
                        need_isolate=True
                        break            
            
                if need_isolate:
                   #isolate line'
                   for idx,line in enumerate(self.figure_wgt.axes.lines):
                       if line != current_line:                      
                           line.set_visible(False)  
                           self.data[idx]["selected"] = True
                       else:
                           self.data[idx]["selected"] = False
                else:
                    #show all lines'
                    for idx,line in enumerate(self.figure_wgt.axes.lines):                     
                        line.set_visible(True)
                        self.data[idx]["selected"] = False                                       
        else:
            #show all lines
            for idx,line in enumerate(self.figure_wgt.axes.lines): 
                line.set_visible(True)                   
                self.data[idx]["selected"] = False                     
               
        self.ids.view.refresh_from_layout()
        self.figure_wgt.figure.canvas.draw_idle()
        self.figure_wgt.figure.canvas.flush_events()
        
class LegendRvHorizontal(BoxLayout):
    """Legend Horizontal class
    
    """     
    figure_wgt = ObjectProperty(None) 
    data=ListProperty()
    text_color=ColorProperty([0,0,0,1])
    background_color=ColorProperty([1,1,1,1])
    
    def __init__(self, **kwargs):
        """init class
        
        """ 
        super(LegendRvHorizontal, self).__init__(**kwargs)
        self.data=[]        

    def set_data(self,content:list) -> None:
        """set legend data 
        
        Args:
            content (list):list of dictionary with matplotlib line(s) 
            
        Returns:
            None
        """       
        self.data=[]
        
        #reset scroll
        self.ids.view.scroll_y = 1

        for i,row_content in enumerate(content):
        
            r_data = {
                "row_index":int(i),
                "viewclass": "CellLegend"
                }
            r_data["text"] = str(row_content.get_label())
            r_data["mycolor"] = get_color_from_hex(to_hex(row_content.get_color()))
            r_data["line_type"] = row_content.get_linestyle()
            r_data["legend_rv"] = self  
            r_data["selected"] = False
            r_data["matplotlib_line"] = row_content
            r_data["text_color"] = self.text_color

            self.data.append(r_data)
       
    def add_data(self,line) -> None:
        """add line method
        
        Args:
            line:matplotlib line
            
        Returns:
            None
        """  
        nb_data=len(self.data)
        r_data = {
            "row_index":int(nb_data),
            "viewclass": "CellLegend"
            }
        r_data["text"] = str(line.get_label())
        r_data["mycolor"] = get_color_from_hex(to_hex(line.get_color()))
        r_data["line_type"] = line.get_linestyle()
        r_data["legend_rv"] = self  
        r_data["selected"] = False
        r_data["matplotlib_line"] = line
        r_data["text_color"] = self.text_color

        self.data.append(r_data)
        self.figure_wgt.figure.canvas.draw_idle()
        self.figure_wgt.figure.canvas.flush_events()  
            
    def remove_data(self,remove_line) -> None:
        """add line method
        
        Args:
            remove_line: matplotlib line
            
        Returns:
            None
        """     
        for idx,line in enumerate(self.figure_wgt.axes.lines):
            if line == remove_line:
                remove_idx=idx
                break        
        del self.data[remove_idx]
        remove_line.remove()
        self.figure_wgt.figure.canvas.draw_idle()
        self.figure_wgt.figure.canvas.flush_events()  
        
    def show_hide_wgt(self,row_index) -> None:
        if self.data[row_index]["selected"]:
            #show line
            self.data[row_index]["selected"] = False
            self.data[row_index]["matplotlib_line"].set_visible(True)
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()             
        else:
            #hide line
            self.data[row_index]["selected"] = True
            self.data[row_index]["matplotlib_line"].set_visible(False)
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()            
        self.ids.view.refresh_from_layout()
           
    def doubletap(self,row_index) -> None:  
        """ double tap behavior is based on plotly behavior """
        if not self.data[row_index]["selected"]:
            current_line = self.data[row_index]["matplotlib_line"]
            if current_line.get_visible():
                #check if we isolate line or show all lines
                need_isolate = False
                for line in self.figure_wgt.axes.lines:
                    if line != current_line and line.get_visible():
                        need_isolate=True
                        break            
            
                if need_isolate:
                   #isolate line'
                   for idx,line in enumerate(self.figure_wgt.axes.lines):
                       if line != current_line:                      
                           line.set_visible(False)  
                           self.data[idx]["selected"] = True
                       else:
                           self.data[idx]["selected"] = False
                else:
                    #show all lines'
                    for idx,line in enumerate(self.figure_wgt.axes.lines):                     
                        line.set_visible(True)
                        self.data[idx]["selected"] = False                                       
        else:
            #show all lines
            for idx,line in enumerate(self.figure_wgt.axes.lines): 
                line.set_visible(True)                   
                self.data[idx]["selected"] = False                     
               
        self.ids.view.refresh_from_layout()
        self.figure_wgt.figure.canvas.draw_idle()
        self.figure_wgt.figure.canvas.flush_events()

class CellLegendMatplotlib(LegendGestures, BoxLayout):
    """ Touch legend kivy class"""  
    selected = BooleanProperty(False)
    row_index = NumericProperty(0)
    matplotlib_legend_box = ObjectProperty(None)
    matplotlib_line = ObjectProperty(None)
    matplotlib_text = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)    

    def cg_tap(self, touch, x, y):
        #single tap
        if self.matplotlib_legend_box.figure_wgt.touch_mode!='drag_legend':
            self.matplotlib_legend_box.show_hide_wgt(self.row_index)

    def cg_double_tap(self, touch, x, y):
        #double tap
        self.matplotlib_legend_box.doubletap(self.row_index)
        
class CellLegend(LegendGestures, BoxLayout):
    """ Touch legend kivy class"""  
    selected = BooleanProperty(False)
    text = StringProperty("")
    row_index = NumericProperty(0)
    legend_rv = ObjectProperty(None)
    matplotlib_line = ObjectProperty(None)
    line_type = StringProperty('-')	
    mycolor= ListProperty([0,0,1])
    text_color=ColorProperty([0,0,0,1])
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)    

    def cg_tap(self, touch, x, y):
        #single tap
        self.legend_rv.show_hide_wgt(self.row_index)

    def cg_double_tap(self, touch, x, y):
        #double tap
        self.legend_rv.doubletap(self.row_index)
        
class CellLegendHorizontal(LegendGestures, BoxLayout):
    """ Touch legend kivy class"""  
    selected = BooleanProperty(False)
    text = StringProperty("")
    row_index = NumericProperty(0)
    legend_rv = ObjectProperty(None)
    matplotlib_line = ObjectProperty(None)
    line_type = StringProperty('-')	
    mycolor= ListProperty([0,0,1])
    text_color=ColorProperty([0,0,0,1])

    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)    

    def cg_tap(self, touch, x, y):
        #single tap
        self.legend_rv.show_hide_wgt(self.row_index)

    def cg_double_tap(self, touch, x, y):
        #double tap
        self.legend_rv.doubletap(self.row_index)
        
def MatplotlibInteractiveLegend(figure_wgt,legend_handles='auto'):
    """ transform matplotlib legend to interactive legend
    
    Args:
        figure_wgt: figure widget from kivy_matplotlib_widget package
        legend_handles : 'auto' (general purpose) or variante (ex: for seaborn legend)

    """
    
    #check if the figure has a legend
    leg = figure_wgt.figure.axes[0].get_legend()
    if leg is None:
        #create a defaut legend if no figure exist
        ax=figure_wgt.figure.axes[0]
        ax.legend()
        leg = figure_wgt.figure.axes[0].get_legend()   
        
    #put the legend on top (useful for drag behavior)
    leg.set_zorder(20)
        
    #detect is the legend use column (ex: horizontal legend)
    if hasattr(leg,'_ncols'):
        #matplotlib version >3.6
        legend_ncol = leg._ncols
    else:
        legend_ncol = leg._ncol
        
    if legend_ncol>1:
        ncol=legend_ncol
    else:
        ncol=None
        
    #get legend bbox position ater 2sec. Otherwise, bbox is not good
    Clock.schedule_once(partial(create_touch_legend,figure_wgt,leg,ncol,legend_handles),2)

def create_touch_legend(figure_wgt,leg,ncol,legend_handles,_):    
    """ create touch legend """
    
    bbox = leg.get_window_extent()
    
    ax=figure_wgt.figure.axes[0]
    legend_x0 = bbox.x0  
    legend_y0 = bbox.y0 
    legend_x1 = bbox.x1 
    legend_y1 = bbox.y1 
    pos_x, pos_y = figure_wgt.pos

    if leg._get_loc() == 0:
        #location best. Need to fix the legend location
        loc_in_canvas = bbox.xmin, bbox.ymin
        loc_in_norm_axes = leg.parent.transAxes.inverted().transform_point(loc_in_canvas)
        leg._loc = tuple(loc_in_norm_axes)    

    #position for kivy widget
    x0_pos=int(legend_x0)+pos_x
    y0_pos=int(legend_y0)+pos_y
    x1_pos=int(legend_x1)+pos_x
    y1_pos=int(legend_y1)+pos_y
    instance_dict = dict()
     
    #get legend handles and labels
    current_handles, current_labels = ax.get_legend_handles_labels()
    nb_group=len(current_labels)

    #check if a title exist
    have_title=False
    if leg.get_title().get_text():
        have_title=True
    
    if ncol:
        #reorder legend handles to fit with grid layout orientation
        #note: all kivy grid layout orientation don't fit with matpotlib grid position
        matplotlib_legend_box = MatplotlibLegendGrid()
        matplotlib_legend_box.ids.box.cols=ncol
        
        m, n = ceil(nb_group/ncol), ncol
        index_arr = np.pad(np.arange(nb_group).astype(float), (0, m*n - np.arange(nb_group).size), 
                            mode='constant', constant_values=np.nan)
        index_arr2 = np.pad(np.arange(nb_group).astype(float), (0, m*n - np.arange(nb_group).size), 
                           mode='constant', constant_values=np.nan).reshape(m,n) 
        
        i=0
        for col in range(ncol):
            for row in range(m):
                value=index_arr2[int(row),int(col)]
                if not np.isnan(value):
                    index_arr2[int(row),int(col)]=index_arr[i]
                    i+=1
        myorder = index_arr2.flatten()
        myorder = myorder[~np.isnan(myorder)]
        current_handles = [current_handles[int(i)] for i in myorder]

    else:
        matplotlib_legend_box = MatplotlibLegendBox()
        
    #update kivy widget attributes
    matplotlib_legend_box.x_pos = x0_pos
    matplotlib_legend_box.y_pos = y0_pos
    matplotlib_legend_box.legend_height = y1_pos-y0_pos
    
    if have_title:
        
        #we create an offset for the matplotlib position
        if ncol:
            title_padding = (y1_pos-y0_pos)/(ceil(nb_group/ncol)+1)

        else:
            title_padding = (y1_pos-y0_pos)/(nb_group+1)
            
        matplotlib_legend_box.title_padding = title_padding
        matplotlib_legend_box.legend_height -= title_padding
            
    matplotlib_legend_box.legend_width = x1_pos-x0_pos

    
    if leg.get_patches()[:] and legend_handles=='variante':
        #sometime the legend handles not perfectly match with graph
        #in this case, this experimenta section try to fix this
        ax_instances = ax.get_children()    
        hist_instance=[]
        for current_inst in ax_instances:
            if isinstance(current_inst, mpl.spines.Spine):
                break
            hist_instance.append(current_inst)
            
        nb_instance_by_hist = len(hist_instance)//nb_group        

        for i,leg_instance in enumerate(leg.get_patches()[:]):
            instance_dict[leg_instance] = hist_instance[int(i*nb_instance_by_hist):int((i+1)*nb_instance_by_hist)]  
            current_legend_cell = CellLegendMatplotlib()
            current_legend_cell.matplotlib_line = leg_instance
            current_legend_cell.matplotlib_text = leg.get_texts()[:][i]
            current_legend_cell.matplotlib_legend_box=matplotlib_legend_box
            current_legend_cell.row_index=i
            current_legend_cell.height=int(matplotlib_legend_box.legend_height/nb_group)
            matplotlib_legend_box.box.add_widget(current_legend_cell)

    else:
        ##general purpose interactive position        
        #get matplotlib text object
        legeng_marker=[]
        for i,current_instance in enumerate(leg.findobj()):
            if current_instance in leg.get_texts()[:]:
                legeng_marker.append(leg.findobj()[i-2])

        label_text_list=leg.get_texts()[:]
        if ncol:
            #reorder legend marker and text position to fit with grid layout orientation
            legeng_marker = [legeng_marker[int(i)] for i in myorder]
            label_text_list = [label_text_list[int(i)] for i in myorder]

        #create all legend cell in kivy
        for i,leg_instance in enumerate(label_text_list):

            current_legend_cell = CellLegendMatplotlib()
            if ncol:
                current_legend_cell.height=int(matplotlib_legend_box.legend_height/(ceil((nb_group-1)/ncol)))
                current_legend_cell.width=int(matplotlib_legend_box.legend_width/ncol)
            else:
                current_legend_cell.height=int(matplotlib_legend_box.legend_height/nb_group)
                current_legend_cell.width=matplotlib_legend_box.legend_width
                
            if isinstance(current_handles[i],mpl.container.BarContainer):
                instance_dict[legeng_marker[i]] = list(current_handles[i][:])
            else:
                instance_dict[legeng_marker[i]] = [current_handles[i]]
            current_legend_cell.matplotlib_line = legeng_marker[i]
            
            current_legend_cell.matplotlib_text = leg_instance
            current_legend_cell.matplotlib_legend_box=matplotlib_legend_box
            current_legend_cell.row_index=i
            
            #add cell in kivy widget
            matplotlib_legend_box.box.add_widget(current_legend_cell)     

    #update some attributes
    matplotlib_legend_box.figure_wgt=figure_wgt
    matplotlib_legend_box.instance_dict=instance_dict

    #add kivy legend widget in figure
    figure_wgt.parent.add_widget(matplotlib_legend_box)
    figure_wgt.legend_instance=matplotlib_legend_box
    
class MatplotlibLegendBox(FloatLayout):
    """ Touch egend kivy class"""
    figure_wgt= ObjectProperty(None)
    x_pos = NumericProperty(1)
    y_pos = NumericProperty(1)
    legend_height = NumericProperty(1)
    legend_width = NumericProperty(1) 
    title_padding = NumericProperty(0)    
    instance_dict=dict()
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)    

    def update_size(self):
        """ update size """
        if self.figure_wgt:
            leg = self.figure_wgt.figure.axes[0].get_legend()
            bbox = leg.get_window_extent()
            
            ax=self.figure_wgt.figure.axes[0]
            legend_x0 = bbox.x0  
            legend_y0 = bbox.y0 
            legend_x1 = bbox.x1 
            legend_y1 = bbox.y1 
            pos_x, pos_y = self.figure_wgt.pos
            x0_pos=int(legend_x0)+pos_x
            y0_pos=int(legend_y0)+pos_y
            x1_pos=int(legend_x1)+pos_x
            y1_pos=int(legend_y1)+pos_y        

            self.x_pos = x0_pos
            self.y_pos = y0_pos
            self.legend_height = y1_pos-y0_pos
            have_title=False
            if leg.get_title().get_text():
                have_title=True            
            if have_title:
                current_handles, current_labels = ax.get_legend_handles_labels()
                nb_group=len(current_labels)                
                if hasattr(leg,'_ncols'):
                    #matplotlib version >3.6
                    legend_ncol = leg._ncols
                else:
                    legend_ncol = leg._ncol
                    
                if legend_ncol>1:
                    ncol=legend_ncol
                else:
                    ncol=None               
                if ncol:
                    title_padding = (y1_pos-y0_pos)/(ceil(nb_group/ncol)+1)
                else:
                    title_padding = (y1_pos-y0_pos)/(nb_group+1)
                    
                self.title_padding = title_padding
                self.legend_height -= title_padding
            self.legend_width = x1_pos-x0_pos

    def show_hide_wgt(self,row_index) -> None:
        if self.box.children[::-1][row_index].selected:
            #show line
            self.box.children[::-1][row_index].selected = False
            self.box.children[::-1][row_index].matplotlib_line.set_alpha(1)
            self.box.children[::-1][row_index].matplotlib_text.set_alpha(1)
            
            hist = self.instance_dict[self.box.children[::-1][row_index].matplotlib_line]
            for current_hist in hist:
                current_hist.set_visible(True)
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()             
        else:
            #hide line
            self.box.children[::-1][row_index].selected = True
            self.box.children[::-1][row_index].matplotlib_line.set_alpha(0.5)
            self.box.children[::-1][row_index].matplotlib_text.set_alpha(0.5)
            
            hist = self.instance_dict[self.box.children[::-1][row_index].matplotlib_line]
            for current_hist in hist:
                current_hist.set_visible(False)            
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()
           
    def doubletap(self,row_index) -> None:  
        """ double tap behavior is based on plotly behavior """
        if not self.box.children[::-1][row_index].selected:
            hist = self.instance_dict
            current_line = hist[self.box.children[::-1][row_index].matplotlib_line][0]
            hist_keys= list(self.instance_dict.keys())           
            
            if current_line.get_visible():
                #check if we isolate line or show all lines
                need_isolate = False
                for line in hist_keys:
                    if hist[line][0] != current_line and hist[line][0].get_visible():
                        need_isolate=True
                        break            
            
                if need_isolate:
                   #isolate line'
                   for idx,line in enumerate(hist_keys):
                       if hist[line][0] != current_line:                      
                           for current_hist in hist[line]:
                               current_hist.set_visible(False)                           
                           self.box.children[::-1][idx].selected = True
                           self.box.children[::-1][idx].matplotlib_line.set_alpha(0.5)
                           self.box.children[::-1][idx].matplotlib_text.set_alpha(0.5)
                       else:
                           self.box.children[::-1][idx].selected = False
                           self.box.children[::-1][idx].matplotlib_line.set_alpha(1)
                           self.box.children[::-1][idx].matplotlib_text.set_alpha(1)
                else:
                    #show all lines'
                    for idx,line in enumerate(hist_keys):                     
                        for current_hist in hist[line]:
                            current_hist.set_visible(True) 
                        self.box.children[::-1][idx].selected = False  
                        self.box.children[::-1][idx].matplotlib_line.set_alpha(1)  
                        self.box.children[::-1][idx].matplotlib_text.set_alpha(1)                                   
        else:
            hist = self.instance_dict
            #show all lines
            for idx,line in enumerate(hist): 
                for current_hist in hist[line]:
                    current_hist.set_visible(True)                   
                self.box.children[::-1][idx].selected = False 
                self.box.children[::-1][idx].matplotlib_line.set_alpha(1) 
                self.box.children[::-1][idx].matplotlib_text.set_alpha(1)                   
               
        self.figure_wgt.figure.canvas.draw_idle()
        self.figure_wgt.figure.canvas.flush_events()
        
class MatplotlibLegendGrid(FloatLayout):
    """ Touch egend kivy class"""
    figure_wgt= ObjectProperty(None)
    x_pos = NumericProperty(1)
    y_pos = NumericProperty(1)
    legend_height = NumericProperty(1)
    legend_width = NumericProperty(1) 
    title_padding = NumericProperty(0)  
    
    instance_dict=dict()
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs) 

    def update_size(self):
        """ update size """
        if self.figure_wgt:
            leg = self.figure_wgt.figure.axes[0].get_legend()
            bbox = leg.get_window_extent()
            
            ax=self.figure_wgt.figure.axes[0]
            legend_x0 = bbox.x0  
            legend_y0 = bbox.y0 
            legend_x1 = bbox.x1 
            legend_y1 = bbox.y1 
            pos_x, pos_y = self.figure_wgt.pos
            x0_pos=int(legend_x0)+pos_x
            y0_pos=int(legend_y0)+pos_y
            x1_pos=int(legend_x1)+pos_x
            y1_pos=int(legend_y1)+pos_y        

            self.x_pos = x0_pos
            self.y_pos = y0_pos
            self.legend_height = y1_pos-y0_pos
            have_title=False
            if leg.get_title().get_text():
                have_title=True            
            if have_title:
                current_handles, current_labels = ax.get_legend_handles_labels()
                nb_group=len(current_labels)                
                if hasattr(leg,'_ncols'):
                    #matplotlib version >3.6
                    legend_ncol = leg._ncols
                else:
                    legend_ncol = leg._ncol
                    
                if legend_ncol>1:
                    ncol=legend_ncol
                else:
                    ncol=None               
                if ncol:
                    title_padding = (y1_pos-y0_pos)/(ceil(nb_group/ncol)+1)
                else:
                    title_padding = (y1_pos-y0_pos)/(nb_group+1)
                    
                self.title_padding = title_padding
                self.legend_height -= title_padding
            self.legend_width = x1_pos-x0_pos
        

    def show_hide_wgt(self,row_index) -> None:
        if self.box.children[::-1][row_index].selected:
            #show line
            self.box.children[::-1][row_index].selected = False
            self.box.children[::-1][row_index].matplotlib_line.set_alpha(1)
            self.box.children[::-1][row_index].matplotlib_text.set_alpha(1)
            
            hist = self.instance_dict[self.box.children[::-1][row_index].matplotlib_line]
            for current_hist in hist:
                current_hist.set_visible(True)
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()             
        else:
            #hide line
            self.box.children[::-1][row_index].selected = True
            self.box.children[::-1][row_index].matplotlib_line.set_alpha(0.5)
            self.box.children[::-1][row_index].matplotlib_text.set_alpha(0.5)
            
            hist = self.instance_dict[self.box.children[::-1][row_index].matplotlib_line]
            for current_hist in hist:
                current_hist.set_visible(False)
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()
           
    def doubletap(self,row_index) -> None:  
        """ double tap behavior is based on plotly behavior """
        if not self.box.children[::-1][row_index].selected:
            hist = self.instance_dict
            current_line = hist[self.box.children[::-1][row_index].matplotlib_line][0]
            hist_keys= list(self.instance_dict.keys())           
            
            if current_line.get_visible():
                #check if we isolate line or show all lines
                need_isolate = False
                for line in hist_keys:
                    if hist[line][0] != current_line and hist[line][0].get_visible():
                        need_isolate=True
                        break            
            
                if need_isolate:
                   #isolate line'
                   for idx,line in enumerate(hist_keys):
                       if hist[line][0] != current_line:
                           for current_hist in hist[line]:
                               current_hist.set_visible(False)                           
                           self.box.children[::-1][idx].selected = True
                           self.box.children[::-1][idx].matplotlib_line.set_alpha(0.5)
                           self.box.children[::-1][idx].matplotlib_text.set_alpha(0.5)
                       else:
                           self.box.children[::-1][idx].selected = False
                           self.box.children[::-1][idx].matplotlib_line.set_alpha(1)
                           self.box.children[::-1][idx].matplotlib_text.set_alpha(1)
                else:
                    #show all lines'
                    for idx,line in enumerate(hist_keys):                     
                        for current_hist in hist[line]:
                            current_hist.set_visible(True) 
                        self.box.children[::-1][idx].selected = False  
                        self.box.children[::-1][idx].matplotlib_line.set_alpha(1)  
                        self.box.children[::-1][idx].matplotlib_text.set_alpha(1)                                   
        else:
            hist = self.instance_dict
            #show all lines
            for idx,line in enumerate(hist): 
                for current_hist in hist[line]:
                    current_hist.set_visible(True)                   
                self.box.children[::-1][idx].selected = False 
                self.box.children[::-1][idx].matplotlib_line.set_alpha(1) 
                self.box.children[::-1][idx].matplotlib_text.set_alpha(1)                   
               
        self.figure_wgt.figure.canvas.draw_idle()
        self.figure_wgt.figure.canvas.flush_events()  
         
from kivy.factory import Factory

Factory.register('LegendRv', LegendRv)

Builder.load_string('''
<LegendRv>
    canvas.before:
        Color:
            rgba: root.background_color  
        Rectangle:
            pos: self.pos
            size: self.size    
    
    RecycleView:
        id:view
        viewclass: "CellLegend"
        size_hint_y:1  
        data: root.data
        scroll_timeout:5000
        effect_cls: "ScrollEffect"
          
        RecycleBoxLayout:
            default_size_hint: 1, None
            default_size: None, None
            id:body    
            orientation: 'vertical'
            size_hint_y:None
            height:self.minimum_height
            
<LegendRvHorizontal>
    canvas.before:
        Color:
            rgba: root.background_color 
        Rectangle:
            pos: self.pos
            size: self.size    
    
    RecycleView:
        id:view
        viewclass: "CellLegendHorizontal"
        size_hint_y:1  
        data: root.data
        scroll_timeout:5000
        effect_cls: "ScrollEffect"
          
        RecycleBoxLayout:
            default_size_hint: None, 1
            default_size: None, None
            id:body    
            orientation: 'horizontal'
            size_hint_y:1
            size_hint_x:None
            width: self.minimum_width 
 
<MatplotlibLegendBox>
    box:box
    size_hint: None,None
    width: dp(0.01) 
    height: dp(0.01) 
    
    BoxLayout:
        id:box         
        x:root.x_pos
        y:root.y_pos
        size_hint:None,None
        height:root.legend_height+root.title_padding
        width:root.legend_width
        orientation:'vertical'
 
<MatplotlibLegendGrid>
    box:box
    size_hint: None,None
    width: dp(0.01) 
    height: dp(0.01) 
    
    GridLayout:
        id:box         
        x:root.x_pos
        y:root.y_pos
        padding:0,root.title_padding,0,0
        size_hint:None,None
        height:root.legend_height+root.title_padding
        width:root.legend_width

<CellLegendMatplotlib>
    opacity: 0.5 if self.selected else 1
    size_hint_y: None
    height: dp(48)  
    size_hint_x: None
    width: dp(48)  
            
<CellLegendHorizontal>   
    mycolor: [1,0,0]
    line_type:'-'
    opacity: 0.5 if self.selected else 1
    size_hint_y: None
    height: dp(48) 
    size_hint_x:None
    width:dp(78) + line_label.texture_size[0]
    
    Widget:
		size_hint_x:None
		width:dp(18) 

    BoxLayout:
		size_hint_x:None
		width:dp(38)
		canvas:
			Color:
				rgb:root.mycolor
				a:
                    self.opacity if root.line_type=='-' or \
                    root.line_type!='--' or \
                    root.line_type!='-.' or \
                    root.line_type!=':' else 0
            Line:
                width: dp(2.5)
                cap:'square'
                points: 
                    self.pos[0], \
                    self.pos[1]+self.height/2, \
                    self.pos[0]+self. \
                    width,self.pos[1]+self.height/2

			Color:
    			rgb:root.mycolor
				a:self.opacity if root.line_type=='--' else 0
            Line:
                width: dp(2.5)
            	cap:'square'
				points: 
    				self.pos[0], \
    				self.pos[1]+self.height/2, \
    				self.pos[0]+self.width*0.4, \
    				self.pos[1]+self.height/2
			Line:
				width: dp(2.5)
				cap:'square'
                points:
                    self.pos[0]+self.width*0.6, \
                    self.pos[1]+self.height/2, \
                    self.pos[0]+self.width, \
                    self.pos[1]+self.height/2 

            Color:
                rgb:root.mycolor
                a:self.opacity if root.line_type=='-.' else 0
            Line:
                width: dp(2.5)
                cap:'square'
                points: 
                    self.pos[0], \
                    self.pos[1]+self.height/2, \
                    self.pos[0]+self.width*0.3, \
                    self.pos[1]+self.height/2
            Ellipse:
                size: (dp(5),dp(5))
                pos: 
                    (self.pos[0]+self.width*0.5-dp(5/2), \
                    self.pos[1]+self.height/2-dp(5/2))

            Line:
                width: dp(2.5)
                cap:'square'
                points: 
                    self.pos[0]+self.width*0.7, \
                    self.pos[1]+self.height/2, \
                    self.pos[0]+self.width, \
                    self.pos[1]+self.height/2               

            Color:
                rgb:root.mycolor            
                a:self.opacity if root.line_type==':' else 0
            Ellipse:
    			size: (dp(5),dp(5))
                pos: 
                    self.pos[0]-dp(5/2), \
                    self.pos[1]+self.height/2-dp(5/2)
            Ellipse:
    			size: (dp(5),dp(5))
    			pos: 
        			(self.pos[0]+self.width*0.5-dp(5/2), \
        			self.pos[1]+self.height/2-dp(5/2))

            Ellipse:
    			size: (dp(5),dp(5))
				pos: 
    				self.pos[0]+self.width-dp(5/2), \
    				self.pos[1]+self.height/2-dp(5/2)    

    Widget:
		size_hint_x:None
		width:dp(18)                    

    BoxLayout:  
		size_hint_x:None
		width:line_label.texture_size[0]
        Label:
            id:line_label
            text:root.text
            halign:'left'
            valign:'center'
            color:root.text_color
            font_size: dp(18.5)
        
    Widget:
		size_hint_x:None
		width:dp(4)
        
<CellLegend>   
    mycolor: [1,0,0]
    line_type:'-'
    opacity: 0.5 if self.selected else 1
    size_hint_y: None
    height: dp(48) 
            
    Widget:
		size_hint_x:None
		width:dp(4) 

    BoxLayout:
		size_hint_x:None
		width:dp(38)
		canvas:
			Color:
				rgb:root.mycolor
				a:
                    self.opacity if root.line_type=='-' or \
                    root.line_type!='--' or \
                    root.line_type!='-.' or \
                    root.line_type!=':' else 0
            Line:
                width: dp(2.5)
                cap:'square'
                points: 
                    self.pos[0], \
                    self.pos[1]+self.height/2, \
                    self.pos[0]+self. \
                    width,self.pos[1]+self.height/2

			Color:
    			rgb:root.mycolor
				a:self.opacity if root.line_type=='--' else 0
            Line:
                width: dp(2.5)
            	cap:'square'
				points: 
    				self.pos[0], \
    				self.pos[1]+self.height/2, \
    				self.pos[0]+self.width*0.4, \
    				self.pos[1]+self.height/2
			Line:
				width: dp(2.5)
				cap:'square'
                points:
                    self.pos[0]+self.width*0.6, \
                    self.pos[1]+self.height/2, \
                    self.pos[0]+self.width, \
                    self.pos[1]+self.height/2 

            Color:
                rgb:root.mycolor
                a:self.opacity if root.line_type=='-.' else 0
            Line:
                width: dp(2.5)
                cap:'square'
                points: 
                    self.pos[0], \
                    self.pos[1]+self.height/2, \
                    self.pos[0]+self.width*0.3, \
                    self.pos[1]+self.height/2
            Ellipse:
                size: (dp(5),dp(5))
                pos: 
                    (self.pos[0]+self.width*0.5-dp(5/2), \
                    self.pos[1]+self.height/2-dp(5/2))

            Line:
                width: dp(2.5)
                cap:'square'
                points: 
                    self.pos[0]+self.width*0.7, \
                    self.pos[1]+self.height/2, \
                    self.pos[0]+self.width, \
                    self.pos[1]+self.height/2               

            Color:
                rgb:root.mycolor            
                a:self.opacity if root.line_type==':' else 0
            Ellipse:
    			size: (dp(5),dp(5))
                pos: 
                    self.pos[0]-dp(5/2), \
                    self.pos[1]+self.height/2-dp(5/2)
            Ellipse:
    			size: (dp(5),dp(5))
    			pos: 
        			(self.pos[0]+self.width*0.5-dp(5/2), \
        			self.pos[1]+self.height/2-dp(5/2))

            Ellipse:
    			size: (dp(5),dp(5))
				pos: 
    				self.pos[0]+self.width-dp(5/2), \
    				self.pos[1]+self.height/2-dp(5/2)    

    Widget:
		size_hint_x:None
		width:dp(18)                    
                   
    Label:
        text:root.text
        text_size:self.size
        halign:'left'
        valign:'center'
        color:root.text_color
        font_size: dp(18.5)
        shorten: True
        shorten_from: 'center'
        ''')
