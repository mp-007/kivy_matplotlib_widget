# kivy_matplotlib_widget
A fast matplotlib rendering for Kivy based on Kivy_matplotlib project (https://github.com/jeysonmc/kivy_matplotlib) and kivy scatter. Matplotlib used 'agg' backend

# How to use
install with pip install (just import module in your header to register all the widgets in your kivy Factory: import kivy_matplotlib_widget)
```
pip install kivy-matplotlib-widget
```
You can also copy the needed widget in project

See examples for more informations

# key features
 - zoom with 2 fingers or mouse scroll
 - pan with 1 finger or mouse left click
 - zoom box like plotly library
 - reset axis on double-click (home button)
 - fast rendering mode (axis not updated for faster draw)
 - use only 1 package (matplotlib) and no additional backend
 - cursor and hover option (touch or desktop mode)
 - legend widget like plotly library
 - interactive axis like plotly library
 - min/max touch option to easily change axis limit

![image](https://user-images.githubusercontent.com/19823482/146577068-026a9608-a9df-4d59-a548-8b81f9b85574.png)

