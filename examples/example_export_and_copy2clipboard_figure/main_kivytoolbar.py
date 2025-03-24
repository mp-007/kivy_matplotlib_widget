from kivy.lang import Builder
from kivy.app import App
import matplotlib.pyplot as plt
from kivy.properties import ListProperty,ObjectProperty
from kivy.uix.button import Button
from kivy.factory import Factory as F

from plyer import filechooser #using plyer filechooser to be cross platform
from kivy_matplotlib_widget.tools.clipboard_tool import image2clipboard
from kivy_matplotlib_widget.uix.navigation_bar_widget import KivyMatplotNavToolbar
from kivy_matplotlib_widget.uix.minmax_widget import add_minmax
from kivy_matplotlib_widget.uix.hover_widget import add_hover

"""
note: image2clipboard do not work on android
"""

class SaveFig(F.NavButton):
    '''
    Button that triggers 'filechooser.save_file()' and processes
    the data response from filechooser Activity.
    '''

    selection = ListProperty([])
    figure_wgt = ObjectProperty(None)

    def choose(self):
        '''
        Call plyer filechooser API to run a filechooser Activity.
        '''
        filechooser.save_file(on_selection=self.handle_selection,title='Save figure',filters=["*.png (defaul if no extension),*.jpg,*.svg,*.pdf,*.eps"])

    def handle_selection(self, selection):
        '''
        Callback function for handling the selection response from Activity.
        '''
        self.selection = selection

    def on_selection(self, *a, **k):
        '''
        Update TextInput.text after FileChoose.selection is changed
        via FileChoose.handle_selection.
        '''
        if self.selection:
            if str(self.selection[0])[-4:] != '.png' and \
                str(self.selection[0])[-4:] != '.jpg' and \
                str(self.selection[0])[-4:] != '.eps' and \
                    str(self.selection[0])[-4:] != '.svg' and \
                    str(self.selection[0])[-4:] != '.pdf':
                path = str(self.selection[0]) + '.png'
            else:
                path = str(self.selection[0]) 
            if path[-4:] == '.png':
                self.figure_wgt.export_to_png(path)
            else:
                myformat = path[-3:]
                self.figure_wgt.figure.savefig(path, format=myformat)
KV = '''

Screen
    figure_wgt:figure_wgt
    BoxLayout:
        orientation:'vertical'
        KivyMatplotNavToolbar:
            id:nav_bar
            nav_icon:'all'
            hover_mode:'desktop'
            show_cursor_data:True
            figure_wgt:figure_wgt
                  
        MatplotFigureSubplot:
            id:figure_wgt
            auto_cursor:True
            interactive_axis:True             
            
'''


class Test(App):
    lines = []

    def build(self):  
        self.screen=Builder.load_string(KV)
        return self.screen

    def on_start(self, *args):
        fig, ax1 = plt.subplots(1, 1)

        ax1.plot([0,1,2,3,4], [1,2,8,9,4],label='line1')
        ax1.plot([2,8,10,15], [15,0,2,4],label='line2')
        
        self.screen.figure_wgt.figure = fig
        
        add_hover(self.screen.figure_wgt,mode='desktop')
        add_minmax(self.screen.figure_wgt)
        
        #add custom button in navigation bar 
        export_fig = SaveFig()
        export_fig.figure_wgt = self.screen.figure_wgt
        export_fig.icon_font_size=self.screen.ids.nav_bar.icon_font_size
        export_fig.nav_btn_size=self.screen.ids.nav_bar.nav_btn_size
        export_fig.bind(on_release=lambda x:export_fig.choose())
        export_fig.text = u"{}".format("\U00000088")
        self.screen.ids.nav_bar.ids.container.add_widget(export_fig)

        clipboard_btn = F.NavButton()
        clipboard_btn.icon_font_size=self.screen.ids.nav_bar.icon_font_size
        clipboard_btn.nav_btn_size=self.screen.ids.nav_bar.nav_btn_size        
        clipboard_btn.bind(on_release=lambda x:self.copy2clipboard())
        clipboard_btn.text = u"{}".format("\U000005c5")
        self.screen.ids.nav_bar.ids.container.add_widget(clipboard_btn)
        
    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        
    def copy2clipboard(self):
        image2clipboard(self.screen.figure_wgt)
        
Test().run()