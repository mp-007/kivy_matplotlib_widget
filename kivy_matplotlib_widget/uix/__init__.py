# remove font_manager "debug" from matplotib
import logging

logging.getLogger("matplotlib.font_manager").disabled = True
