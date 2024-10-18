from kivy.app import App
from kivy.lang import Builder
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ColorProperty,ObjectProperty,BooleanProperty,NumericProperty
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform

import numpy as np
from matplotlib.path import Path
import matplotlib.colors as mcolors

class MatplotlibEvent:
    x:None
    y:None
    pickradius:None
    inaxes:None
    projection:False
    compare_xdata:False

kv = """
<ResizeSelect>:
    #size_hint: None,None
    #height: dp(0.001)
    #width:dp(0.001)       
    canvas.before:
        # TOP LINE
        Color:
            rgba: root.top_color
        Line:
            width: dp(1)
            points: 
                (self.x + dp(7), self.top, self.right - dp(7), self.top) if root.alpha \
                else (self.x, self.top, self.right, self.top)# Top line
            cap: 'round'
            joint: 'round'
            dash_offset: 2
            dash_length: 10
            close: False

        # BOTTOM LINE
        Color:
            rgba: root.bottom_color
        Line:
            width: dp(1)
            points: 
                (self.x + dp(7), self.y, self.right - dp(7), self.y)  if root.alpha \
                else (self.x, self.y, self.right, self.y)# Bottom
            cap: 'round'
            joint: 'round'
            dash_offset: 2
            dash_length: 10
            close: False

        # LEFT LINE
        Color:
            rgba: root.left_color
        Line:
            width: dp(1)
            points: 
                (self.x, self.y+dp(7), self.x, self.top - dp(7)) if root.alpha \ 
                else (self.x, self.y, self.x, self.top)# Left
            cap: 'round'
            joint: 'round'
            dash_offset: 2
            dash_length: 10
            close: False

        # RIGHT LINE
        Color:
            rgba: root.right_color
        Line:
            width: dp(1)
            points: 
                (self.right, self.y + dp(7), self.right, self.top - dp(7)) if root.alpha \
                else (self.right, self.y, self.right, self.top)# Right
            cap: 'round'
            joint: 'round'
            dash_offset: 2
            dash_length: 10
            close: False

        # Upper left rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.x, self.top - dp(7)
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]                
        Line:
            width: dp(1)
            points: ( \
                self.x, self.top - dp(7), \
                self.x + dp(7), self.top - dp(7),  self.x + dp(7), self.top, \
                self.x, self.top, \
                self.x, self.top - dp(7))  # Horizontal
            cap: 'round'
            joint: 'round'
            close: False

        # Bottom left rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.x, self.y
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.x, self.y, \
                self.x + dp(7), self.y,  self.x + dp(7), self.y + dp(7), \
                self.x, self.y + dp(7), \
                self.x, self.y)  # Vertical
            cap: 'round'
            joint: 'round'
            close: True

        # Bottom right rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.right - dp(7), self.y
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.right - dp(7), self.y, \
                self.right - dp(7), self.y + dp(7),  self.right, self.y + dp(7), \
                self.right, self.y, \
                self.right - dp(7), self.y)  # Vertical
            cap: 'round'
            joint: 'round'
            close: True
            
        # Upper right rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.right - dp(7), self.top - dp(7)
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.right - dp(7), self.top - dp(7), \
                self.right - dp(7), self.top,  self.right, self.top, \
                self.right, self.top - dp(7), \
                self.right - dp(7), self.top - dp(7))  # Horizontal
            cap: 'round'
            joint: 'round'
            close: True

        # Upper edge rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.x + self.width/2 - dp(3.5), self.top - dp(7)
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.x + self.width/2 - dp(3.5), self.top - dp(7), \
                self.x + self.width/2 + dp(3.5), self.top - dp(7),  self.x + self.width/2 + dp(3.5), self.top, \
                self.x + self.width/2 - dp(3.5), self.top, \
                self.x + self.width/2 - dp(3.5), self.top - dp(7))  # Horizontal
            cap: 'round'
            joint: 'round'
            close: True

        # Left edge rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.x, self.y + self.height/2 - dp(3.5)
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.x, self.y + self.height/2 - dp(3.5), \
                self.x + dp(7), self.y + self.height/2 - dp(3.5), \
                self.x + dp(7), self.y + self.height/2 + dp(3.5), \
                self.x, self.y + self.height/2 + dp(3.5), \
                self.x, self.y + self.height/2 - dp(3.5))  # Vertical
            cap: 'round'
            joint: 'round'
            close: True

        # Right edge rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.right - dp(7), self.y + self.height/2 - dp(3.5)
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.right - dp(7), self.y + self.height/2 - dp(3.5), \
                self.right, self.y + self.height/2 - dp(3.5), \
                self.right, self.y + self.height/2 + dp(3.5), \
                self.right - dp(7), self.y + self.height/2 + dp(3.5), \
                self.right - dp(7), self.y + self.height/2 - dp(3.5))  # Vertical
            cap: 'round'
            joint: 'round'
            close: True

        # Bottom edge rectangle
        Color:
            rgba: 62/255, 254/255, 1, root.alpha
        Rectangle:
            pos: self.x + self.width/2 - dp(3.5), self.y
            size: dp(7), dp(7)
        Color:
            rgba:
                [0,0,0,root.alpha] if (root.bg_color[0]*0.299 + \
                root.bg_color[1]*0.587 + root.bg_color[2]*0.114) > 186/255 \
                else [1,1,1,root.alpha]  
        Line:
            width: dp(1)
            points: ( \
                self.x + self.width/2 - dp(3.5), self.y, \
                self.x + self.width/2 + dp(3.5), self.y, \
                self.x + self.width/2 + dp(3.5), self.y + dp(7), \
                self.x + self.width/2 - dp(3.5), self.y + dp(7), \
                self.x + self.width/2 - dp(3.5), self.y)  # Horizontal
            cap: 'round'
            joint: 'round'
            close: True
        
<ResizeRelativeLayout>  
    resize_wgt:resize_wgt
    size_hint: None,None
    height: dp(0.001)
    width:dp(0.001)         
    ResizeSelect:
        id:resize_wgt
        desktop_mode:root.desktop_mode
        figure_wgt:root.figure_wgt
        size_hint: None, None
        size: dp(0.001),dp(0.001)
        pos: 0, 0
        opacity:0

"""

MINIMUM_HEIGHT = 20.0
MINIMUM_WIDTH = 20.0

class ResizeRelativeLayout(RelativeLayout):
    figure_wgt = ObjectProperty()
    resize_wgt = ObjectProperty()
    desktop_mode = BooleanProperty(True)
    def __init__(self,figure_wgt=None,desktop_mode=True, **kwargs):
        self.figure_wgt=figure_wgt
        self.desktop_mode=desktop_mode
        super().__init__(**kwargs)

class ResizeSelect(FloatLayout):
    top_color = ColorProperty("black")
    bottom_color = ColorProperty("black")
    left_color = ColorProperty("black")
    right_color = ColorProperty("black")
    highlight_color = ColorProperty("red")
    bg_color = ColorProperty([1,1,1,1])
    figure_wgt = ObjectProperty()
    desktop_mode = BooleanProperty(True)
    alpha = NumericProperty(1)

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.selected_side = None
        self.verts = []
        self.myevent = MatplotlibEvent()
        self.ax = None
        self.callback = None
        
        self.alpha_other = 0.3
        self.ind = []

        self.collection = None
        self.xys = None
        self.Npts = None
        self.fc = None
        
        self.line = None  
        self.ind_line=[]
        
        self.first_touch=None

    def on_kv_post(self,_):     
        if platform != 'android' and self.desktop_mode: #only bind mouse position if not android or if the user set desktop mode to false
            Window.bind(mouse_pos=self.on_mouse_pos)
            
    def update_bg_color(self):
        fig_bg_color = self.figure_wgt.figure.get_facecolor()
        rgb_fig_bg_color = mcolors.to_rgb(fig_bg_color)
        if (rgb_fig_bg_color[0]*0.299 + rgb_fig_bg_color[1]*0.587 + rgb_fig_bg_color[2]*0.114) > 186/255:
            self.bg_color = [1,1,1,1]
            self.bottom_color = (
                self.top_colors
            ) = self.left_color = self.right_color = [1,1,1,1]
            
        else:
            self.bg_color = [0,0,0,1]
            self.bottom_color = (
                self.top_colors
            ) = self.left_color = self.right_color = [0,0,0,1]
        
    def set_collection(self,collection):
        self.collection = collection
        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object
        self.fc = collection.get_facecolors()
        if len(self.fc) == 0:
            raise ValueError('Collection must have a facecolor')
        elif len(self.fc) == 1:
            self.fc = np.tile(self.fc, (self.Npts, 1))
            
    def set_line(self,line):
        self.line = line          

    def on_mouse_pos(self, something, touch):
        """
        When the mouse moves, we check the position of the mouse
        and update the cursor accordingly.
        """
        if self.opacity and self.figure_wgt.touch_mode=='selector' and self.collide_point(*self.to_widget(*touch)):
            
            collision = self.collides_with_control_points(something, self.to_widget(*touch))
            if collision in ["top left", "bottom right"]:
                Window.set_system_cursor("size_nwse")
            elif collision in ["top right", "bottom left"]:
                Window.set_system_cursor("size_nesw")
            elif collision in ["top", "bottom"]:
                Window.set_system_cursor("size_ns")
            elif collision in ["left", "right"]:
                Window.set_system_cursor("size_we")
            else:
                Window.set_system_cursor("size_all")
                
        elif self.figure_wgt.collide_point(*touch):
        # else:
            Window.set_system_cursor("arrow")

    def collides_with_control_points(self, _, touch):
        """
        Returns True if the mouse is over a control point.
        """
        x, y = touch[0], touch[1]

        # Checking mouse is on left edge
        if self.x <= x <= self.x + dp(7):
            if self.y <= y <= self.y + dp(7):
                return "bottom left"
            elif self.y + dp(7) <= y <= self.y + self.height - dp(7):
                return "left"
            else:
                return "top left"

        # Checking mouse is on top edge
        elif self.x + dp(7) <= x <= self.x + self.width - dp(7):
            if self.y <= y <= self.y + dp(7):
                return "bottom"
            elif self.y + self.height - dp(7) <= y <= self.y + self.height:
                return "top"
            else:
                return False

        # Checking mouse is on right edge
        elif self.x + self.width - dp(7) <= x <= self.x + self.width:
            if self.y <= y <= self.y + dp(7):
                return "bottom right"
            elif self.y + dp(7) <= y <= self.y + self.height - dp(7):
                return "right"
            else:
                return "top right"

    def on_touch_down(self, touch):
        if self.figure_wgt.touch_mode != 'selector':
            return
        
        if self.collide_point(*touch.pos) and self.opacity:
            touch.grab(self)
            x, y = touch.pos[0], touch.pos[1]

            collision = self.collides_with_control_points("", touch.pos)
            # collision = self.collides_with_control_points("", self.to_widget(*touch.pos))

            if collision == "top":
                self.top_color = self.highlight_color
                self.selected_side = "top"
            elif collision == "bottom":
                self.bottom_color = self.highlight_color
                self.selected_side = "bottom"
            elif collision == "left":
                self.left_color = self.highlight_color
                self.selected_side = "left"
            elif collision == "right":
                self.right_color = self.highlight_color
                self.selected_side = "right"
            else:
                if collision == "top left":
                    self.selected_side = "top left"
                    self.top_color = self.highlight_color
                    self.left_color = self.highlight_color
                elif collision == "bottom right":
                    self.selected_side = "bottom right"
                    self.bottom_color = self.highlight_color
                    self.right_color = self.highlight_color
                elif collision == "top right":
                    self.selected_side = "top right"
                    self.top_color = self.highlight_color
                    self.right_color = self.highlight_color
                elif collision == "bottom left":
                    self.selected_side = "bottom left"
                    self.bottom_color = self.highlight_color
                    self.left_color = self.highlight_color
                else:
                    self.selected_side = None
                    self.top_color = self.highlight_color
                    self.bottom_color = self.highlight_color
                    self.left_color = self.highlight_color
                    self.right_color = self.highlight_color
        elif self.figure_wgt.collide_point(*self.to_window(*touch.pos)):
            if self.figure_wgt.touch_mode=='selector':
                touch.grab(self)
                x, y = touch.pos[0], touch.pos[1]
                self.pos = (x,y-5)
                self.size = (5,5)
                self.opacity=1
                self.first_touch = (x,y-5)
                self.selected_side = "new select"
            
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.figure_wgt.touch_mode != 'selector':
            return
        
        if touch.grab_current is self:
            x, y = self.to_window(*self.pos)

            top = y + self.height  # top of our widget
            right = x + self.width  # right of our widget
            
            if self.selected_side == "top":
                if self.height + touch.dy <= MINIMUM_HEIGHT:
                    return False
                self.height += touch.dy

            elif self.selected_side == "bottom":
                if self.height - touch.dy <= MINIMUM_HEIGHT:
                    return False
                self.height -= touch.dy
                self.y += touch.dy

            elif self.selected_side == "left":
                if self.width - touch.dx <= MINIMUM_WIDTH:
                    return False
                self.width -= touch.dx
                self.x += touch.dx

            elif self.selected_side == "right":
                if self.width + touch.dx <= MINIMUM_WIDTH:
                    return False
                self.width += touch.dx

            elif self.selected_side == "top left":
                if touch.dx > 0:
                    if self.width - touch.dx <= MINIMUM_WIDTH:
                        return False
                if touch.dy < 0:
                    if self.height + touch.dy <= MINIMUM_HEIGHT:
                        return False

                self.width -= touch.dx
                self.x += touch.dx  # OK
                self.height += touch.dy

            elif self.selected_side == "top right":
                if touch.dx < 0:
                    if self.width + touch.dx <= MINIMUM_WIDTH:
                        return False
                if touch.dy < 0:
                    if self.height + touch.dy <= MINIMUM_HEIGHT:
                        return False

                self.width += touch.dx
                self.height += touch.dy

            elif self.selected_side == "bottom left":
                if touch.dx > 0:
                    if self.width - touch.dx <= MINIMUM_WIDTH:
                        return False
                if touch.dy > 0:
                    if self.height - touch.dy <= MINIMUM_HEIGHT:
                        return False

                self.width -= touch.dx  # OK
                self.x += touch.dx
                self.height -= touch.dy
                self.y += touch.dy

            elif self.selected_side == "bottom right":
                if touch.dx < 0:
                    if self.width + touch.dx <= MINIMUM_WIDTH:
                        return False
                if touch.dy > 0:
                    if self.height - touch.dy <= MINIMUM_HEIGHT:
                        return False

                self.width += touch.dx
                self.height -= touch.dy
                self.y += touch.dy
                
            elif self.selected_side == "new select":
                self.width += touch.dx
                self.height -= touch.dy
                self.y += touch.dy  

            elif not self.selected_side:
                if self.figure_wgt.collide_point(*self.to_window(self.pos[0]+touch.dx,self.pos[1]+touch.dy )) and \
                    self.figure_wgt.collide_point(*self.to_window(self.pos[0] + self.size[0]+touch.dx,self.pos[1]+ self.size[1]+touch.dy )):
                # if self.x<self.figure_wgt.x : #and self.x + self.width <self.figure_wgt.x + self.figure_wgt.width:
                    self.x += touch.dx
                # if self.y<self.figure_wgt.y and self.y + self.height <self.figure_wgt.y + self.figure_wgt.height:
                    self.y += touch.dy
                # else:
                #     return
                
            if self.selected_side == "new select":
                self.alpha = 0
            else:
                self.alpha = 1

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.figure_wgt.touch_mode != 'selector':
            return
        
        if touch.grab_current is self:
            touch.ungrab(self)
            self.alpha = 1
            if (self.bg_color[0]*0.299 + \
            self.bg_color[1]*0.587 + self.bg_color[2]*0.114) > 186/255:
                self.bottom_color = (
                    self.top_colors
                ) = self.left_color = self.right_color = [0,0,0,1]
            else:
                self.bottom_color = (
                    self.top_colors
                ) = self.left_color = self.right_color = [1,1,1,1]                
            
            if self.first_touch and self.selected_side == "new select":
                self.check_if_reverse_selection(touch)
            
            if abs(self.size[0])<MINIMUM_WIDTH or abs(self.size[1])<MINIMUM_HEIGHT:
                self.reset_selection()
            else:
                if self.verts is not None:
                    # self.verts.append(self._get_data(touch))
                    self.verts = self._get_box_data()
                    self.onselect(self.verts)

            return True
        return super().on_touch_up(touch)
    
    def check_if_reverse_selection(self,last_touch):  

        if last_touch.x > self.first_touch[0] and \
            last_touch.y < self.first_touch[1]:

                return
            
        else:
            #reverse selection'
            if last_touch.x < self.first_touch[0]:
                self.pos[0] = last_touch.x
                self.size[0] = self.first_touch[0] - last_touch.x + 5
                
            if last_touch.y > self.first_touch[1]:
                self.size[1] = last_touch.y - self.first_touch[1] 
                self.pos[1] = last_touch.y - self.size[1]
                
            return


    def reset_selection(self):
        self.pos = (0,0)
        self.size = (dp(0.01),dp(0.01))
        self.opacity=0

        
    def _get_box_data(self):
        trans = self.ax.transData.inverted() 
        #get box 4points xis data
        x0 = self.to_window(*self.pos)[0]-self.figure_wgt.pos[0]
        y0 = self.to_window(*self.pos)[1]-self.figure_wgt.pos[1]
        x1 = self.to_window(*self.pos)[0]-self.figure_wgt.pos[0]
        y1 = self.to_window(*self.pos)[1] + self.height-self.figure_wgt.pos[1]
        x3 = self.to_window(*self.pos)[0] + self.width-self.figure_wgt.pos[0]
        y3 = self.to_window(*self.pos)[1]-self.figure_wgt.pos[1]
        x2 = self.to_window(*self.pos)[0] + self.width -self.figure_wgt.pos[0]
        y2 = self.to_window(*self.pos)[1] + self.height  -self.figure_wgt.pos[1]
        
        
        x0_box, y0_box = trans.transform_point((x0, y0)) 
        x1_box, y1_box = trans.transform_point((x1, y1))
        x2_box, y2_box = trans.transform_point((x2, y2))
        x3_box, y3_box = trans.transform_point((x3, y3))
        verts=[]
        verts.append((x0_box, y0_box))
        verts.append((x1_box, y1_box))
        verts.append((x2_box, y2_box))
        verts.append((x3_box, y3_box))

        return verts

    def onselect(self, verts):
        path = Path(verts)
        if self.collection:
            self.ind = np.nonzero(path.contains_points(self.xys))[0] #xys collection.get_offsets()
            self.fc[:, -1] = self.alpha_other
            self.fc[self.ind, -1] = 1
            self.collection.set_facecolors(self.fc)
        if self.line:
            xdata,ydata = self.line.get_data()
            self.ind_line = np.nonzero(path.contains_points(np.array([xdata,ydata]).T))[0]                  

        self.figure_wgt.figure.canvas.draw_idle()
        if self.callback:
            self.callback(self)
            
    def set_callback(self,callback):
        self.callback=callback
        
    def clear_selection(self):

        if self.collection:
            self.ind = []
            self.fc[:, -1] = 1
            self.collection.set_facecolors(self.fc)
        if self.line:
            self.ind_line=[]
            
        self.reset_selection()
        self.figure_wgt.figure.canvas.draw_idle()  
              

Builder.load_string(kv)
