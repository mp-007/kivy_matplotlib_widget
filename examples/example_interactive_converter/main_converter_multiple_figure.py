"""
important note: interactive_graph function use python mutiprocessing method, so 
it's a not blocking method and several figure can be generated. Becauce it use
mutiprocessing method, it need to be call with if __name__ == "__main__": .

if you need to generate kivy interactive graph in ipython. Please see 
interactive_graph_ipython function.

"""

# =============================================================================
# 
# example from https://matplotlib.org/stable/gallery/subplots_axes_and_figures/multiple_figs_demo.html
#
# =============================================================================


from kivy_matplotlib_widget.tools.interactive_converter import interactive_graph

import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":
    t = np.arange(0.0, 2.0, 0.01)
    s1 = np.sin(2*np.pi*t)
    s2 = np.sin(4*np.pi*t)
    
    # =============================================================================
    # figure 1
    # =============================================================================
    
    plt.figure(1)
    plt.subplot(211)
    plt.plot(t, s1)
    plt.subplot(212)
    plt.plot(t, 2*s1)
    
    interactive_graph(plt.figure(1))
    
    # =============================================================================
    # figure 2
    # =============================================================================
    
    
    plt.figure(2)
    plt.plot(t, s2)
    
    interactive_graph(plt.figure(2))
