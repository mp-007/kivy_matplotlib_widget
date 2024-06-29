"""
important note: interactive_graph_ipython is used to generate kivy interactive 
graph directly in python interactive console (ipython) oy directly in the code
if you have only 1 figure. You can generate only 1 figure at a time with this
function. You can close your kivy graph (or ctrl+c) if you wnt to resume your
code and then you can call interactive_graph_ipython again.

If you need to generate multiple figure with a no blocking method, please see
interactive_graph function.
"""

# =============================================================================
# 
# example from https://matplotlib.org/stable/gallery/text_labels_and_annotations/legend.html#sphx-glr-gallery-text-labels-and-annotations-legend-py
# 
# =============================================================================

import matplotlib.pyplot as plt
import numpy as np

# Make some fake data.
a = b = np.arange(0, 3, .02)
c = np.exp(a)
d = c[::-1]

# Create plots with pre-defined labels.
fig, ax = plt.subplots()
ax.plot(a, c, 'k--', label='Model length')
ax.plot(a, d, 'k:', label='Data length')
ax.plot(a, c + d, 'k', label='Total message length')

legend = ax.legend(loc='upper center', shadow=True, fontsize='x-large')

# Put a nicer background color on the legend.
legend.get_frame().set_facecolor('C0')


#these 2 lines can be call in your ipython console
from kivy_matplotlib_widget.tools.interactive_converter import interactive_graph_ipython

interactive_graph_ipython(fig,compare_hover=True)