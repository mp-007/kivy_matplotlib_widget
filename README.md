# kivy_matplotlib_widget
A fast matplotlib rendering for Kivy based on Kivy_matplotlib project (https://github.com/jeysonmc/kivy_matplotlib) and kivy scatter. Hover option is also based on the algorithm from mplcursors project (https://github.com/anntzer/mplcursors). Matplotlib used 'agg' backend

# How to use
install with pip install (just import module in your header to register all the widgets in your kivy Factory: import kivy_matplotlib_widget)
```
pip install kivy-matplotlib-widget
```
You can also copy the needed widget in project

See examples for more informations

# Available tool
convert any matplotlib figure into kivy interactive graph with only 2 lines in your ipython console
```
from kivy_matplotlib_widget.tools.interactive_converter import interactive_graph_ipython

interactive_graph_ipython(fig) #fig is your matplotlib figure instance
```
See interactive_converter folder in the examples for more details.

# key features
 - zoom with 2 fingers or mouse scroll
 - pan with 1 finger or mouse left click
 - zoom box like plotly library
 - reset axis on double-click (home button)
 - fast rendering mode (axis not updated for faster draw)
 - use only 2 packages (kivy + matplotlib) and no additional backend
 - matplotlib cursor and kivy hover option (touch or desktop mode)
 - legend widget like plotly library
 - interactive axis like plotly library
 - min/max touch option to easily change axis limit
 - autoscale option

![image](https://github.com/mp-007/kivy_matplotlib_widget/assets/19823482/7709886e-0891-4fb7-a95d-eee790a6c57c)
