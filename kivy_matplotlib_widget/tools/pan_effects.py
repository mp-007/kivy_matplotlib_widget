from time import time
from kivy.effects.kinetic import KineticEffect
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty


class PanEffect(KineticEffect):
    '''PanEffect class for velocity pan
    '''

    drag_threshold = NumericProperty('20sp')
    '''Minimum distance to travel before the movement is considered as a drag.

    :attr:`drag_threshold` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 20sp.
    '''

    pan = NumericProperty(0)
    '''Computed value for panning. This value is different from
    :py:attr:`kivy.effects.kinetic.KineticEffect.value`
    in that it will return to one of the min/max bounds.

    :attr:`pan` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0.
    '''

    target_widget = ObjectProperty(None, allownone=True, baseclass=Widget)
    '''Widget to attach to this effect. Even if this class doesn't make changes
    to the `target_widget` by default, subclasses can use it to change the
    graphics or apply custom transformations.

    :attr:`target_widget` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    displacement = NumericProperty(0)
    '''Cumulative distance of the movement during the interaction. This is used
    to determine if the movement is a drag (more than :attr:`drag_threshold`)
    or not.

    :attr:`displacement` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    def reset(self, pos):
        '''(internal) Reset the value and the velocity to the `pos`.
        Mostly used when the bounds are checked.
        '''
        self.value = pos
        self.velocity = 0
        self.is_manual = True
        self.displacement = 0
        
        if (history := self.history):
            val = history[-1][1]
            history.clear()
            history.append((time(), val))

    def on_value(self, *args):
        
        if not self.is_manual:
            self.target_widget.apply_pan_w_vel(self.value)

    def start(self, val, t=None):
        self.is_manual = True
        self.displacement = 0
        return super(PanEffect, self).start(val, t)

    def update(self, val, t=None):
        self.displacement += abs(val - self.history[-1][1])
        # print('allo')
        return super(PanEffect, self).update(val, t)

    def stop(self, val, t=None):
        # print('allo')
        self.is_manual = False
        self.displacement += abs(val - self.history[-1][1])
        if self.displacement <= self.drag_threshold:
            self.velocity = 0
            return
        return super(PanEffect, self).stop(val, t)