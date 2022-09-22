# kivy_matplotlib_widget
A fast matplotlib rendering for Kivy based on Kivy_matplotlib project (https://github.com/jeysonmc/kivy_matplotlib) and kivy scatter. Matplotlib used 'agg' backend

# How to use
Just copy graph_widget.py and graph_generator_template.py in your project. Modify graph_generator_template as your needed. See examples for more informations

New: install with pip install (just import module in your header: import kivy_matplotlib_widget)
```
pip install kivy-matplotlib-widget
```

# key features
 - zoom with 2 fingers or mouse scroll
 - pan with 1 finger or mouse left click
 - zoom box like plotly library
 - reset axis on double-click (home button)
 - fast rendering mode (axis not updated for faster draw)
 - use only 1 package (matplotlib) and no additional backend
 - cursor option
 - legend widget like plotly library

![image](https://user-images.githubusercontent.com/19823482/146577068-026a9608-a9df-4d59-a548-8b81f9b85574.png)

