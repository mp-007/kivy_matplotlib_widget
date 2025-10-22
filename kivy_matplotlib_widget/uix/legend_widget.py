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
from kivy.metrics import dp
from matplotlib.colors import to_hex
import matplotlib as mpl
from math import ceil
import numpy as np
import copy
import re


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
    text_font=StringProperty("Roboto")
    text_font_size=NumericProperty(dp(18.5))
    background_color=ColorProperty([1,1,1,1])
    box_height = NumericProperty(dp(48))
    autoscale=BooleanProperty(False)

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
            r_data["text_font"] = self.text_font
            r_data["text_font_size"] = self.text_font_size
            r_data["box_height"] = self.box_height

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
        r_data["text_font"] = self.text_font
        r_data["text_font_size"] = self.text_font_size
        r_data["box_height"] = self.box_height

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
        remove_idx=None
        for idx,current_data in enumerate(self.data):
            if current_data["matplotlib_line"] == remove_line:
                remove_idx=idx
                break
        if remove_idx:
            del self.data[remove_idx]
            remove_line.remove()
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()

    def show_hide_wgt(self,row_index) -> None:
        if self.data[row_index]["selected"]:
            #show line
            self.data[row_index]["selected"] = False
            self.data[row_index]["matplotlib_line"].set_visible(True)
            if self.autoscale and hasattr(self.figure_wgt,'autoscale_axis'):
                self.figure_wgt.autoscale()
            else:
                self.figure_wgt.figure.canvas.draw_idle()
                self.figure_wgt.figure.canvas.flush_events()
        else:
            #hide line
            self.data[row_index]["selected"] = True
            self.data[row_index]["matplotlib_line"].set_visible(False)
            if self.autoscale and hasattr(self.figure_wgt,'autoscale_axis'):
                self.figure_wgt.autoscale()
            else:
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
                if len(self.figure_wgt.figure.axes)>1:
                    figure_lines = self.figure_wgt.figure.axes[0].get_lines() + \
                                    self.figure_wgt.figure.axes[1].get_lines()
                else:
                    figure_lines = list(self.figure_wgt.figure.axes[0].get_lines())
                for line in figure_lines:
                    if line != current_line and line.get_visible():
                        need_isolate=True
                        break

                if need_isolate:
                   #isolate line'
                   for idx,line in enumerate(figure_lines):
                       if line != current_line:
                           line.set_visible(False)
                           self.data[idx]["selected"] = True
                       else:
                           self.data[idx]["selected"] = False
                else:
                    #show all lines'
                    for idx,line in enumerate(figure_lines):
                        line.set_visible(True)
                        self.data[idx]["selected"] = False
        else:
            #show all lines
            if len(self.figure_wgt.figure.axes)>1:
                figure_lines = self.figure_wgt.figure.axes[0].get_lines() + \
                                self.figure_wgt.figure.axes[1].get_lines()
            else:
                figure_lines = list(self.figure_wgt.figure.axes[0].get_lines())
            for idx,line in enumerate(figure_lines):
                line.set_visible(True)
                self.data[idx]["selected"] = False

        self.ids.view.refresh_from_layout()
        if self.autoscale and hasattr(self.figure_wgt,'autoscale_axis'):
            self.figure_wgt.autoscale()
        else:
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()

class LegendRvHorizontal(BoxLayout):
    """Legend Horizontal class

    """
    figure_wgt = ObjectProperty(None)
    data = ListProperty()
    text_color = ColorProperty([0,0,0,1])
    text_font = StringProperty("Roboto")
    text_font_size = NumericProperty(dp(18.5))
    background_color = ColorProperty([1,1,1,1])
    box_height = NumericProperty(dp(48))
    autoscale=BooleanProperty(False)

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
            r_data["text_font"] = self.text_font
            r_data["text_font_size"] = self.text_font_size
            r_data['box_height'] = self.box_height

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
        r_data["text_font"] = self.text_font
        r_data["text_font_size"] = self.text_font_size
        r_data['box_height'] = self.box_height

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
        remove_idx=None
        for idx,current_data in enumerate(self.data):
            if current_data["matplotlib_line"] == remove_line:
                remove_idx=idx
                break
        if remove_idx:
            del self.data[remove_idx]
            remove_line.remove()
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()

    def show_hide_wgt(self,row_index) -> None:
        if self.data[row_index]["selected"]:
            #show line
            self.data[row_index]["selected"] = False
            self.data[row_index]["matplotlib_line"].set_visible(True)
            if self.autoscale and hasattr(self.figure_wgt,'autoscale_axis'):
                self.figure_wgt.autoscale()
            else:
                self.figure_wgt.figure.canvas.draw_idle()
                self.figure_wgt.figure.canvas.flush_events()
        else:
            #hide line
            self.data[row_index]["selected"] = True
            self.data[row_index]["matplotlib_line"].set_visible(False)
            if self.autoscale and hasattr(self.figure_wgt,'autoscale_axis'):
                self.figure_wgt.autoscale()
            else:
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
                if len(self.figure_wgt.figure.axes)>1:
                    figure_lines = self.figure_wgt.figure.axes[0].get_lines() + \
                                    self.figure_wgt.figure.axes[1].get_lines()
                else:
                    figure_lines = list(self.figure_wgt.figure.axes[0].get_lines())
                for line in figure_lines:
                    if line != current_line and line.get_visible():
                        need_isolate=True
                        break

                if need_isolate:
                   #isolate line'
                   for idx,line in enumerate(figure_lines):
                       if line != current_line:
                           line.set_visible(False)
                           self.data[idx]["selected"] = True
                       else:
                           self.data[idx]["selected"] = False
                else:
                    #show all lines'
                    for idx,line in enumerate(figure_lines):
                        line.set_visible(True)
                        self.data[idx]["selected"] = False
        else:
            #show all lines
            if len(self.figure_wgt.figure.axes)>1:
                figure_lines = self.figure_wgt.figure.axes[0].get_lines() + \
                                self.figure_wgt.figure.axes[1].get_lines()
            else:
                figure_lines = list(self.figure_wgt.figure.axes[0].get_lines())
            for idx,line in enumerate(figure_lines):
                line.set_visible(True)
                self.data[idx]["selected"] = False

        self.ids.view.refresh_from_layout()
        if self.autoscale and hasattr(self.figure_wgt,'autoscale_axis'):
            self.figure_wgt.autoscale()
        else:
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
    text_font=StringProperty("Roboto")
    text_font_size=NumericProperty(dp(18.5))
    box_height = NumericProperty(dp(48))

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
    mycolor = ListProperty([0,0,1])
    text_color = ColorProperty([0,0,0,1])
    text_font = StringProperty("Roboto")
    text_font_size = NumericProperty(dp(18.5))
    box_height = NumericProperty(dp(48))

    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)

    def cg_tap(self, touch, x, y):
        #single tap
        self.legend_rv.show_hide_wgt(self.row_index)

    def cg_double_tap(self, touch, x, y):
        #double tap
        self.legend_rv.doubletap(self.row_index)

def MatplotlibInteractiveLegend(figure_wgt,
                                legend_handles='auto',
                                delay=None,
                                legend_instance=None,
                                custom_handlers=None,
                                multi_legend=False,
                                prop=None,
                                current_handles_text=None,
                                scatter=None,
                                autoscale=False):
    """ transform matplotlib legend to interactive legend

    Args:
        figure_wgt: figure widget from kivy_matplotlib_widget package
        legend_handles : 'auto' (general purpose) or variante (ex: for seaborn legend)
        delay: create legend touch after a delay (None or int)
        legend_instance (object): matplotlib legend instance (optional)
        custom_handlers (list): list of matplotlib plot instances (line,scatter,bar...)
                                    linked to the legend labels (optional)
        multi_legend (bool): Set it True if you have multiple legend in graph

    """

    #check if the figure has a legend
    if legend_instance is None:
        leg = figure_wgt.figure.axes[0].get_legend()
        if leg is None:
            #create a defaut legend if no figure exist
            ax=figure_wgt.figure.axes[0]
            ax.legend()
            leg = figure_wgt.figure.axes[0].get_legend()
    else:
        leg = legend_instance

    #put the legend on top (useful for drag behavior)
    leg.set_zorder(20)
    figure_wgt.figcanvas.draw()

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

    # create_touch_legend(figure_wgt,leg,ncol,legend_handles,0)
    if delay is None:
        #no delay case
        create_touch_legend(figure_wgt,
                            leg,ncol,
                            legend_handles,
                            legend_instance,
                            custom_handlers,
                            multi_legend,
                            prop,
                            current_handles_text,
                            scatter,
                            autoscale,
                            0)
    else:
        #get legend bbox position atfer delay (sometime needed if 'best position' was used)
        Clock.schedule_once(partial(create_touch_legend,
                                    figure_wgt,leg,ncol,
                                    legend_handles,
                                    legend_instance,
                                    custom_handlers,
                                    multi_legend,
                                    prop,
                                    current_handles_text,
                                    scatter,
                                    autoscale),
                            delay)


def create_touch_legend(figure_wgt,
                        leg,ncol,
                        legend_handles,
                        legend_instance,
                        custom_handlers,
                        multi_legend,
                        prop,
                        current_handles_text,
                        scatter,
                        autoscale,
                        _):
    """ create touch legend """

    bbox = leg.get_window_extent()

    if legend_instance is None:
        ax=figure_wgt.figure.axes[0]
    else:
        ax=figure_wgt.figure.axes
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

    if custom_handlers:
        current_handles=custom_handlers
    else:
        #get legend handles and labels
        if legend_instance is None:
            current_handles, current_labels = ax.get_legend_handles_labels()
        else:
            current_handles=[]
            current_labels=[]
            for current_ax in ax:
                current_handles0, current_labels0 = current_ax.get_legend_handles_labels()
                current_handles+=current_handles0
                current_labels+=current_labels0

    nb_group=len(current_handles)

    if nb_group==0:
        print('no legend available')
        return

    #check if a title exist
    have_title=False
    if leg.get_title().get_text():
        have_title=True

    figure_wgt_as_legend=False
    if figure_wgt.legend_instance and not multi_legend:
        for current_legend in figure_wgt.legend_instance:
            current_legend.reset_legend()
        matplotlib_legend_box = current_legend
        figure_wgt_as_legend=True
    else:
        matplotlib_legend_box = MatplotlibLegendGrid()

    matplotlib_legend_box.prop=prop
    matplotlib_legend_box.autoscale=autoscale

    if prop:
        matplotlib_legend_box.facecolor = scatter.get_facecolor()
        matplotlib_legend_box.mysize=float(scatter.get_sizes()[0])
        matplotlib_legend_box.scatter = scatter
        matplotlib_legend_box.current_handles_text=current_handles_text
        matplotlib_legend_box.original_size=scatter.get_sizes()

    if ncol:
        #reorder legend handles to fit with grid layout orientation
        #note: all kivy grid layout orientation don't fit with matpotlib grid position

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
        matplotlib_legend_box.ids.box.cols=1

    #update kivy widget attributes
    matplotlib_legend_box.x_pos = x0_pos
    matplotlib_legend_box.y_pos = y0_pos
    matplotlib_legend_box.legend_height = y1_pos-y0_pos
    if legend_instance:
        matplotlib_legend_box.legend_instance = legend_instance

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
        if hasattr(leg,'legend_handles'):
            #matplotlib>3.7
            legeng_marker = leg.legend_handles
        else:
            legeng_marker = leg.legendHandles

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
                current_legend_cell.height=int(matplotlib_legend_box.legend_height/max(nb_group,1))
                current_legend_cell.width=matplotlib_legend_box.legend_width

            if isinstance(current_handles[i],list):
                instance_dict[legeng_marker[i]] = current_handles[i]
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

    #add kivy legend widget in figure if needed
    if not figure_wgt_as_legend:
        figure_wgt.parent.add_widget(matplotlib_legend_box)
        figure_wgt.legend_instance.append(matplotlib_legend_box)


class MatplotlibLegendGrid(FloatLayout):
    """ Touch egend kivy class"""
    figure_wgt= ObjectProperty(None)
    x_pos = NumericProperty(1)
    y_pos = NumericProperty(1)
    legend_height = NumericProperty(1)
    legend_width = NumericProperty(1)
    title_padding = NumericProperty(0)
    legend_instance = ObjectProperty(None,allow_none=True)
    prop = StringProperty(None,allow_none=True)
    autoscale=BooleanProperty(False)

    instance_dict=dict()

    def __init__(self, **kwargs):
        """ init class """
        self.facecolor=[]
        self.mysize=None
        self.scatter=None
        self.mysize_list=[]
        self.original_size=None
        self.current_handles_text=None

        super().__init__(**kwargs)

    def update_size(self):
        """ update size """
        if self.figure_wgt:
            if self.legend_instance:
                leg = self.legend_instance
            else:
                leg = self.figure_wgt.figure.axes[0].get_legend()
            if leg:
                bbox = leg.get_window_extent()

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
                    if hasattr(leg,'legend_handles'):
                        #matplotlib>3.7
                        current_handles = leg.legend_handles
                    else:
                        current_handles = leg.legendHandles

                    nb_group=len(current_handles)

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

    def reset_legend(self):
        """ reset_legend and clear all children """
        self.x_pos = 1
        self.y_pos = 1
        self.legend_height = 1
        self.legend_width = 1
        self.title_padding = 0
        self.box.clear_widgets()

    def show_hide_wgt(self,row_index) -> None:
        if self.box.children[::-1][row_index].selected:
            #show line
            self.box.children[::-1][row_index].selected = False
            self.box.children[::-1][row_index].matplotlib_line.set_alpha(1)
            self.box.children[::-1][row_index].matplotlib_text.set_alpha(1)

            hist = self.instance_dict[self.box.children[::-1][row_index].matplotlib_line]
            for current_hist in hist:
                self.set_visible(current_hist,True,row_index)
            if self.autoscale and hasattr(self.figure_wgt,'autoscale_axis'):
                if self.prop:
                    self.prop_autoscale()
                else:
                    self.figure_wgt.autoscale()
            else:
                self.figure_wgt.figure.canvas.draw_idle()
                self.figure_wgt.figure.canvas.flush_events()
        else:
            #hide line
            self.box.children[::-1][row_index].selected = True
            self.box.children[::-1][row_index].matplotlib_line.set_alpha(0.5)
            self.box.children[::-1][row_index].matplotlib_text.set_alpha(0.5)

            hist = self.instance_dict[self.box.children[::-1][row_index].matplotlib_line]
            for current_hist in hist:
                self.set_visible(current_hist,False,row_index)
            if self.autoscale and hasattr(self.figure_wgt,'autoscale_axis'):
                if self.prop:
                    self.prop_autoscale()
                else:
                    self.figure_wgt.autoscale()
            else:
                self.figure_wgt.figure.canvas.draw_idle()
                self.figure_wgt.figure.canvas.flush_events()

    def doubletap(self,row_index) -> None:
        """ double tap behavior is based on plotly behavior """
        if not self.box.children[::-1][row_index].selected:
            hist = self.instance_dict
            current_line = hist[self.box.children[::-1][row_index].matplotlib_line][0]
            hist_keys= list(self.instance_dict.keys())

            #check if we isolate line or show all lines
            need_isolate = False
            # for line in hist_keys:
            for idx,line in enumerate(hist_keys):
                if hist[line][0] != current_line:
                    if not self.box.children[::-1][idx].selected:
                        need_isolate=True
                        break

            if need_isolate:
                #isolate line'
                for idx,line in enumerate(hist_keys):
                    if hist[line][0] != current_line:
                        for current_hist in hist[line]:
                            self.set_visible(current_hist,False,idx)
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
                        self.set_visible(current_hist,True,idx)
                    self.box.children[::-1][idx].selected = False
                    self.box.children[::-1][idx].matplotlib_line.set_alpha(1)
                    self.box.children[::-1][idx].matplotlib_text.set_alpha(1)
        else:
            hist = self.instance_dict
            #show all lines
            for idx,line in enumerate(hist):
                for current_hist in hist[line]:
                    self.set_visible(current_hist,True,idx)
                self.box.children[::-1][idx].selected = False
                self.box.children[::-1][idx].matplotlib_line.set_alpha(1)
                self.box.children[::-1][idx].matplotlib_text.set_alpha(1)

        if self.autoscale and hasattr(self.figure_wgt,'autoscale_axis'):
            if self.prop:
                self.prop_autoscale()
                self.figure_wgt.autoscale()
            else:
                self.figure_wgt.autoscale()
        else:
            self.figure_wgt.figure.canvas.draw_idle()
            self.figure_wgt.figure.canvas.flush_events()

    def prop_autoscale(self) -> None:
        """set autoscale hen use prop

        Args:
            None

        Returns:
            None
        """
        ax=self.scatter.axes
        if self.prop=='colors':
            if not self.facecolor.any():
                ax.figure.canvas.draw_idle()
                ax.figure.canvas.flush_events()
                return

        if isinstance(self.mysize_list,list):
            mysize_list = self.mysize_list
        else:
            mysize_list = self.mysize_list.tolist()

        if mysize_list and not all(x == 0.0 for x in mysize_list):


            x,y = self.scatter.get_offsets().T
            indices_nozero = [i for i, v in enumerate(mysize_list) if v != 0.0]
            if len(indices_nozero)==0:
                ax.set_autoscale_on(False)

                ax.figure.canvas.draw_idle()
                ax.figure.canvas.flush_events()
                return
            else:
                xmin = np.min(x[indices_nozero])
                xmax = np.max(x[indices_nozero])
                ymin = np.min(y[indices_nozero])
                ymax = np.max(y[indices_nozero])

            autoscale_axis = self.figure_wgt.autoscale_axis

            no_visible = self.figure_wgt.myrelim(ax,visible_only=self.figure_wgt.autoscale_visible_only)
            ax.autoscale_view(tight=self.figure_wgt.autoscale_tight,
                              scalex=True if autoscale_axis!="y" else False,
                              scaley=True if autoscale_axis!="x" else False)
            ax.autoscale(axis=autoscale_axis,tight=self.figure_wgt.autoscale_tight)

            current_xlim = ax.get_xlim()
            current_ylim = ax.get_ylim()

            invert_xaxis = False
            invert_yaxis = False
            if ax.xaxis_inverted():
                invert_xaxis=True
                xleft = xmax
                xright = xmin
            else:
                xleft = xmin
                xright = xmax

            if ax.yaxis_inverted():
                invert_yaxis=True
                ybottom = ymax
                ytop = ymin
            else:
                ybottom = ymin
                ytop = ymax

            lim_collection = [xleft,ybottom,xright,ytop]

            if lim_collection:
                xchanged=False
                if self.figure_wgt.autoscale_tight:
                    current_margins = (0,0)
                else:
                    current_margins = ax.margins()

                if self.figure_wgt.autoscale_axis!="y":
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

                if self.figure_wgt.autoscale_axis!="x":
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

            index = self.figure_wgt.figure.axes.index(ax)
            self.figure_wgt.xmin[index],self.figure_wgt.xmax[index] = ax.get_xlim()
            self.figure_wgt.ymin[index],self.figure_wgt.ymax[index] = ax.get_ylim()
            ax.set_autoscale_on(False)

        ax.figure.canvas.draw_idle()
        ax.figure.canvas.flush_events()

    def set_visible(self,instance,value,row_index=None) -> None:
        """set visible method

        Args:
            instance: matplotlib instance
            value: True or False

        Returns:
            None
        """
        if self.prop:
            if self.prop=='colors':
                if self.facecolor.any():
                    unique_color = np.unique(self.facecolor,axis=0)
                    ncol = np.shape(unique_color)[0]

                    if not self.mysize_list:

                        self.mysize_list =[self.mysize] * np.shape(self.facecolor)[0]
                    for i in range(np.shape(self.facecolor)[0]):
                        if (self.facecolor[i,:] == unique_color[row_index,:]).all():
                            if value:
                                self.mysize_list[i] = self.mysize
                            else:
                                self.mysize_list[i] = 0.0
                        # else:
                        #     if value:
                        #         mysize_list.append(0.0)
                        #     else:
                        #         mysize_list.append(self.mysize)

                    # self.figure_wgt.figure.axes[0].get_children()[0].set_facecolor(newfacecolor)
                    self.scatter.set_sizes(self.mysize_list)
            if self.prop=='sizes':
                if self.mysize:
                    legend_size = len(self.current_handles_text)
                    legend_value = self.current_handles_text[row_index]

                    float_legend_value_before=None
                    if row_index!=0:
                        legend_value_before = self.current_handles_text[row_index-1]
                        match_legend_value_before = re.search(r"\{(.+?)\}", legend_value_before)
                        if match_legend_value_before:
                            float_legend_value_before = float(match_legend_value_before.group(1))
                        else:
                            return

                    match_legend_value = re.search(r"\{(.+?)\}", legend_value)
                    if match_legend_value:
                        float_legend_value = float(match_legend_value.group(1))
                    else:
                        return

                    if isinstance(self.mysize_list,list) and len(self.mysize_list)==0:

                        self.mysize_list = copy.copy(self.original_size)

                    if row_index==0:
                        index_match=np.where(float_legend_value>=self.original_size)[0]
                    elif row_index==legend_size-1:
                        index_match=np.where(float_legend_value_before<=self.original_size)[0]
                    else:
                        index_match=np.where((float_legend_value>=self.original_size) &
                                             (float_legend_value_before<=self.original_size))[0]
                    if value:
                        self.mysize_list[index_match] = self.original_size[index_match]
                    else:
                        self.mysize_list[index_match] = 0.0

                    self.scatter.set_sizes(self.mysize_list)

        else:
            if hasattr(instance,'set_visible'):
                instance.set_visible(value)
            elif hasattr(instance,'get_children'):
                all_child = instance.get_children()
                for child in all_child:
                    child.set_visible(value)

    def get_visible(self,instance) -> bool:
        """get visible method

        Args:
            instance: matplotlib instance

        Returns:
            bool
        """
        if hasattr(instance,'get_visible'):
            return instance.get_visible()
        elif hasattr(instance,'get_children'):
            return_value=False
            all_child = instance.get_children()
            for child in all_child[:1]:
                return_value = child.get_visible()
            return return_value
        else:
            return False

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
    height: root.box_height
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
            font_size: root.text_font_size
            font_name:root.text_font

    Widget:
		size_hint_x:None
		width:dp(4)

<CellLegend>
    mycolor: [1,0,0]
    line_type:'-'
    opacity: 0.5 if self.selected else 1
    size_hint_y: None
    height: root.box_height

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
        font_size: root.text_font_size
        font_name:root.text_font
        shorten: True
        shorten_from: 'center'
        ''')
