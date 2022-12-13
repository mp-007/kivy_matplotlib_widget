from kivy.uix.boxlayout import BoxLayout
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
    BooleanProperty
    )

from kivy.lang import Builder
from kivy.uix.widget import Widget
from matplotlib.colors import to_hex


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
       
class CellLegend(LegendGestures, BoxLayout):
    """ Touch egend kivy class"""  
    selected = BooleanProperty(False)
    text = StringProperty("")
    row_index = NumericProperty(0)
    legend_rv = ObjectProperty(None)
    matplotlib_line = ObjectProperty(None)
    line_type = StringProperty('-')	
    mycolor= ListProperty([0,0,1])
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)    

    def cg_tap(self, touch, x, y):
        #single tap
        self.legend_rv.show_hide_wgt(self.row_index)

    def cg_double_tap(self, touch, x, y):
        #double tap
        self.legend_rv.doubletap(self.row_index)
         
from kivy.factory import Factory

Factory.register('LegendRv', LegendRv)

Builder.load_string('''
<LegendRv>
    canvas.before:
        Color:
            rgba: (1, 1, 1, 1)    
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
            orientation: 'vertical'
        
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
        color:0,0,0,1
        font_size: dp(18.5)
        shorten: True
        shorten_from: 'center'
        ''')
