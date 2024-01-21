from kivy.utils import platform

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App
from graph_generator import GraphGenerator
from minmax_widget import add_minmax

KV = '''
#:import MatplotFigure graph_widget

Screen
    figure_wgt:figure_wgt
    BoxLayout:
        orientation:'vertical'
        BoxLayout:
            size_hint_y:0.2
            Button:
                text:"home"
                on_release:app.home()
            Button:
                text:"back"
                on_release:app.back()  
            Button:
                text:"forward"
                on_release:app.forward()                
            ToggleButton:
                group:'touch_mode'
                state:'down'
                text:"pan" 
                on_press:
                    app.set_touch_mode('pan')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"zoom box"  
                on_release:
                    app.set_touch_mode('zoombox')
                    self.state='down' 
            ToggleButton:
                group:'touch_mode'
                text:"cursor"  
                on_release:
                    app.set_touch_mode('cursor')
                    self.state='down'  
            ToggleButton:
                group:'touch_mode'
                text:"min/max" 
                on_release:
                    app.set_touch_mode('minmax')
                    self.state='down'                      
        BoxLayout:
            size_hint_y:0.2                    
            ToggleButton:
                group:'touch_mode'
                text:"pan_x" 
                on_press:
                    app.set_touch_mode('pan_x')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"pan_y" 
                on_press:
                    app.set_touch_mode('pan_y')
                    self.state='down'                    
            ToggleButton:
                group:'touch_mode'
                text:"adjust_x"  
                on_press:
                    app.set_touch_mode('adjust_x')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"adjust_y"  
                on_press:
                    app.set_touch_mode('adjust_y')
                    self.state='down' 

            ToggleButton:
                text:"zoom_x"  
                on_press:
                    app.set_zoom_behavior('zoom_x',self.state)                     
            ToggleButton:
                text:"zoom_y"  
                on_press:
                    app.set_zoom_behavior('zoom_y',self.state)                      
        MatplotFigure:
            id:figure_wgt
            #update axis during pan/zoom
            fast_draw:False
'''


class Test(App):
    lines = []

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        mygraph = GraphGenerator()
        
        self.screen.figure_wgt.figure = mygraph.fig
        
        #register lines instance if need to be update
        self.lines.append(mygraph.line1)
        self.lines.append(mygraph.line2)
        
        #register line for cursor
        self.screen.figure_wgt.register_lines(self.lines)
        
        #add min max option
        add_minmax(self.screen.figure_wgt)

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def set_zoom_behavior(self,mode,state):
        boolean_val=True
        if state=='down':
            boolean_val=False
        if mode=='zoom_x':
            self.screen.figure_wgt.do_zoom_y=boolean_val
        elif mode=='zoom_y':
            self.screen.figure_wgt.do_zoom_x=boolean_val        
    def home(self):
        self.screen.figure_wgt.home()
    def back(self):
        self.screen.figure_wgt.back()   
    def forward(self):
        self.screen.figure_wgt.forward()        
        
Test().run()