import os

import kivy


kivy.require("2.0.0")

path = os.path.dirname(__file__)
"""Path to kivy_matplotlib_widget package directory."""

fonts_path = os.path.join(path, f"fonts{os.sep}")
"""Path to fonts directory."""


import kivy_matplotlib_widget.factory_registers  # NOQA

__version__ = "0.14.0"
__description__ = "A Matplotlib interactive widget for kivy"
__author__ = "mp-007"
