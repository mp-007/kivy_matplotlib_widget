from kivy.utils import platform

#avoid conflict between mouse provider and touch (very important with touch device)
#no need for android platform
if platform != 'android':
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.lang import Builder
from kivy.app import App

import matplotlib.pyplot as plt

from kivy_matplotlib_widget.uix.legend_widget import MatplotlibInteractiveLegend  #also register all widgets to kivy register


KV = '''
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
            text: 'ZoomBox'
            on_press: 
                app.set_touch_mode('zoombox')
                self.state='down'
        ToggleButton:
            group:'touch_mode'
            text:"drag legend"  
            on_release:
                app.set_touch_mode('drag_legend')
                self.state='down'                  
                    
    BoxLayout: 
        ScreenManager:
            id:sm
            Screen1:
            Screen2:
            Screen3:

    BoxLayout:
        size_hint_y:0.1
        Button:
            text:"previous screen"
            on_release:app.previous_screen()
        Button:
            text:"next screen"
            on_release:app.next_screen()
                
<Screen1@Screen>
    name:'screen1'  
    figure_wgt:figure_wgt                  
    MatplotFigureSubplot:
        id:figure_wgt
        fast_draw:True
        interactive_axis:True
        
<Screen2@Screen> 
    name:'screen2'  
    figure_wgt:figure_wgt                  
    MatplotFigureSubplot:
        id:figure_wgt
        fast_draw:True
        interactive_axis:True
        draw_all_axes:True
        
<Screen3@Screen> 
    name:'screen3'  
    figure_wgt:figure_wgt                  
    MatplotFigureSubplot:
        id:figure_wgt
        fast_draw:True
        interactive_axis:True
        draw_all_axes:True
        
'''

class Test(App):
    def build(self):
        self.graph_app = Builder.load_string(KV)
        return self.graph_app

    def on_start(self, *args):

# =============================================================================
#         figure 1 - screen1 - example with twin axis
# =============================================================================
        fig, ax1 = plt.subplots(1, 1)
        
        plt.title('Twin axis legend')

        ax1.plot([0,1,2,3,4], [1,2,8,9,4],label='line1')
        ax1.scatter([2,8,10,15], [15,0,2,4],label='line2')
        ax2=ax1.twinx()
        ax2.plot([2,8,10,15], [15,0,2,4],c='r',label='line3')
        
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        leg=ax2.legend(lines + lines2, labels + labels2, loc=4)
        
        screen1=self.graph_app.ids.sm.get_screen('screen1')
        screen1.figure_wgt.figure = fig
        
        MatplotlibInteractiveLegend(screen1.figure_wgt,
                                    legend_instance=leg)
# =============================================================================
#         figure 2 - screen2 - example with 2 legends in same axis
# =============================================================================
        fig2, ax3 = plt.subplots()
        plt.title('2 legends in same axis')
        
        line1, = ax3.plot([1, 2, 3], label="Line 1", linestyle='--')
        line2, = ax3.plot([3, 2, 1], label="Line 2", linewidth=4)
        
        # Create a legend for the first line.
        first_legend = ax3.legend(handles=[line1], loc='upper right')
        
        # Add the legend manually to the Axes.
        ax3.add_artist(first_legend)
        
        # Create another legend for the second line.
        second_legend = ax3.legend(handles=[line2], loc='lower right')
        
        screen2=self.graph_app.ids.sm.get_screen('screen2')
        screen2.figure_wgt.figure = fig2
                 
        MatplotlibInteractiveLegend(screen2.figure_wgt,
                                    legend_instance=first_legend,
                                    custom_handlers=[line1])

        MatplotlibInteractiveLegend(screen2.figure_wgt,
                                    legend_instance=second_legend,
                                    custom_handlers=[line2],multi_legend=True)  
                
# =============================================================================
#         figure 3 - screen3 - group legend
# =============================================================================

        # create all axes we need
        fig3, ax4 = plt.subplots()
        plt.title('Group legend')
        
        line1, = ax4.plot([1, 2, 3], c='b', label="Line 1", linestyle='--')
        line2, = ax4.plot([3, 2, 1], c='b', label="Line 2", linewidth=4)
        line3, = ax4.plot([2, 3, 4], c='b', label="Line 3", linestyle='--')
        
        line4, = ax4.plot([0.5,1, 6], c='r', label="Line 4", linestyle='--')
        line5, = ax4.plot([2, 4.5, 5.5], c='r',label="Line 5", linewidth=4)
        
        import matplotlib.patches as mpatches
        blue_patch = mpatches.Patch(color='blue', label='The bue data')
        red_patch = mpatches.Patch(color='red', label='The red data')
        
        # Create a legend 
        leg3 = ax4.legend(handles=[blue_patch,red_patch],labels=['blue','red'], loc='upper right')
        
        screen3=self.graph_app.ids.sm.get_screen('screen3')
        screen3.figure_wgt.figure = fig3
                 
        MatplotlibInteractiveLegend(screen3.figure_wgt,
                                    legend_instance=leg3,
                                    custom_handlers=[[line1,line2,line3],[line4,line5]])

    def set_touch_mode(self,mode):
        for screen in self.graph_app.ids.sm.screens:
            if hasattr(screen,'figure_wgt'):
                screen.figure_wgt.touch_mode=mode

    def home(self):
        screen=self.graph_app.ids.sm.current_screen
        screen.figure_wgt.main_home()
        
    def previous_screen(self):
        screen_name=self.graph_app.ids.sm.current
        screen_number = int(screen_name[-1])
        if screen_number<=1:
            screen_number=3
        else:
            screen_number-=1
            
        self.graph_app.ids.sm.current = 'screen' + str(screen_number)        
        
    def next_screen(self):
        screen_name=self.graph_app.ids.sm.current
        screen_number = int(screen_name[-1])
        if screen_number>=3:
            screen_number=1
        else:
            screen_number+=1
            
        self.graph_app.ids.sm.current = 'screen' + str(screen_number)


Test().run()