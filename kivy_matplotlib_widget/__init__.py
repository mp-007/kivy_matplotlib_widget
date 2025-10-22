import os

import kivy

kivy.require("2.3.0")

path = os.path.dirname(__file__)
"""Path to kivy_matplotlib_widget package directory."""

fonts_path = os.path.join(path, f"fonts{os.sep}")
"""Path to fonts directory."""
from kivy.core.text import LabelBase

LabelBase.register(name="NavigationIcons",fn_regular= fonts_path + "NavigationIcons.ttf")

import kivy_matplotlib_widget.factory_registers  # NOQA

__version__ = "0.16.0"
__description__ = "A Matplotlib interactive widget for kivy"
__author__ = "mp-007"
