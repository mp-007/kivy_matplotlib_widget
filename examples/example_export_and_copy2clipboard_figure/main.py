from kivy.lang import Builder
from kivy.app import App
import matplotlib.pyplot as plt
from kivy.properties import ListProperty,ObjectProperty
from kivy.uix.button import Button

from plyer import filechooser #using plyer filechooser to be cross platform
from kivy_matplotlib_widget.tools.clipboard_tool import image2clipboard

"""
note: image2clipboard do not work on android
"""

class SaveFig(Button):
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
        MatplotFigure:
            id:figure_wgt
        SaveFig:
            figure_wgt:figure_wgt
            size_hint_y: 0.1
            on_release: self.choose()
            text: 'Save fig'  
        Button:
            size_hint_y: 0.1
            on_release: app.copy2clipboard()
            text: 'Copy to clipboard'              
            
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

    def set_touch_mode(self,mode):
        self.screen.figure_wgt.touch_mode=mode

    def home(self):
        self.screen.figure_wgt.home()
        
    def copy2clipboard(self):
        image2clipboard(self.screen.figure_wgt)
        
Test().run()