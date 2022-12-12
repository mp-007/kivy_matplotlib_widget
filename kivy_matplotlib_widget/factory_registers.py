from kivy.factory import Factory

r = Factory.register

r("MatplotFigure", module="kivy_matplotlib_widget.uix.graph_widget")
r("MatplotFigureScatter", module="kivy_matplotlib_widget.uix.graph_widget_scatter")
r("MatplotFigure3D", module="kivy_matplotlib_widget.uix.graph_widget_3d")
r("LegendRv", module="kivy_matplotlib_widget.uix.legend_widget")