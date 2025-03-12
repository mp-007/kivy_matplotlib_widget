from kivy.factory import Factory

r = Factory.register

r("MatplotFigure", module="kivy_matplotlib_widget.uix.graph_widget")
r("MatplotFigureScatter", module="kivy_matplotlib_widget.uix.graph_widget_scatter")
r("MatplotFigure3D", module="kivy_matplotlib_widget.uix.graph_widget_3d")
r("MatplotFigure3DLayout", module="kivy_matplotlib_widget.uix.graph_widget_3d")
r("MatplotFigureGeneral", module="kivy_matplotlib_widget.uix.graph_widget_general")
r("MatplotFigureTwinx", module="kivy_matplotlib_widget.uix.graph_widget_twinx")
r("MatplotFigureSubplot", module="kivy_matplotlib_widget.uix.graph_subplot_widget")
r("MatplotFigureCropFactor", module="kivy_matplotlib_widget.uix.graph_widget_crop_factor")
r("MatplotNavToolbar", module="kivy_matplotlib_widget.uix.navigation_bar_widget")
r("KivyMatplotNavToolbar", module="kivy_matplotlib_widget.uix.navigation_bar_widget")
r("LegendRv", module="kivy_matplotlib_widget.uix.legend_widget")
r("LegendRvHorizontal", module="kivy_matplotlib_widget.uix.legend_widget")
