from kivy.utils import platform
from kivy.config import Config

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    Config.set('input', 'mouse', 'mouse,disable_on_activity')
else:
    #for android, we remove mouse input to not get extra touch 
    Config.remove_option('input', 'mouse')

from kivy.lang import Builder
from kivy.app import App

import matplotlib.pyplot as plt

from kivy_matplotlib_widget.uix.hover_widget import add_hover,HightChartHover
from kivy.properties import StringProperty

#remove font_manager "debug" from matplotib
# import logging
# logging.getLogger('matplotlib.font_manager').disabled = True

KV = '''
Screen
    figure_wgt:figure_wgt
    BoxLayout:
        orientation:'vertical'
        BoxLayout:
            size_hint_y:0.2
            Button:
                text:"home"
                on_release:app.home()
            ToggleButton:
                group:'touch_mode'
                state:'down'
                text:"pan" 
                on_release:
                    app.set_touch_mode('pan')
                    self.state='down'
            ToggleButton:
                group:'touch_mode'
                text:"zoom box"  
                on_release:
                    app.set_touch_mode('zoombox')
                    self.state='down'  
                                 
        MatplotFigureSubplot:
            id:figure_wgt
            fast_draw:True
            interactive_axis:True
            auto_cursor:True

        BoxLayout:
            size_hint_y:0.2
            Button:
                text:'top'
                on_press: app.set_placement('top')
            Button:
                text:'bottom'
                on_press: app.set_placement('bottom')                
            Button:
                text:'left'
                on_press: app.set_placement('left')  
            Button:
                text:'right'
                on_press: app.set_placement('right')  

        BoxLayout:
            size_hint_y:0.2
            Button:
                text:'middle'
                on_press: app.set_additionnal_placement('middle')            
            Button:
                text:'start'
                on_press: app.set_additionnal_placement('start')
            Button:
                text:'end'
                on_press: app.set_additionnal_placement('end')         

<HightChartHoverVariante>
    text_1row:root.label_x_value
    text_2row:
        '[size={}]'.format(int(root.text_size + dp(6))) + \
        '[color={}]'.format(get_hex_from_color(root.custom_color)) + \
        '[font=NavigationIcons]' + u"{}".format("\U00000EB1") + \
        '[/font][/color][/size]' +  root.extra_text + ': ' + \
        '[b]' + root.label_y_value + '[/b]'
                    
    label_format : root.text_1row + "\\n" + root.text_2row
    position:'left_start'  
'''
    
class HightChartHoverVariante(HightChartHover):
    """ variante of HightChartHover with a differente text configuration"""
    text_1row=StringProperty("")
    text_2row=StringProperty("")
    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs) 

class Test(App):
    lines = []
    current_position = "top"

    def build(self):
        self.screen=Builder.load_string(KV)
        return self.screen


    def on_start(self, *args):

        fig, ax1 = plt.subplots(1, 1)

        ax1.plot([0,1,2,3,4], [1,2,8,9,4],label='line1', marker='o', mec='white', mew=3, markersize=10)
        ax1.plot([2,8,10,15], [15,0,2,4],label='line2', marker='o', mec='white', mew=3, markersize=10)
        
        # Remove the top and right spines
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        add_hover(self.screen.figure_wgt,mode='desktop',hover_widget=HightChartHover())
        
        #variante of HightChartHover with a differente text configuration
        # add_hover(self.screen.figure_wgt,mode='desktop',hover_widget=HightChartHoverVariante())
        
        self.current_position = self.root.ids.figure_wgt.hover_instance.position

        self.screen.figure_wgt.figure = fig

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()

    def set_placement(self,value):
        self.root.ids.figure_wgt.hover_instance.position = value
        self.current_position = value
        
    def set_additionnal_placement(self,value):
        if value == 'middle':
            self.root.ids.figure_wgt.hover_instance.position = self.current_position
        else:
            self.root.ids.figure_wgt.hover_instance.position = self.current_position   + '_' + value  

Test().run()