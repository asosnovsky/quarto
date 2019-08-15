from typing import Tuple
from kivy.uix.widget import Widget
from kivy.properties import (
    NumericProperty, BooleanProperty,
    StringProperty
)

class WinBanner(Widget):
    pname = StringProperty()

class BorderedRect(Widget):
    x = NumericProperty(0) 
    y = NumericProperty(0) 
    size = NumericProperty(50) 

    is_highlighted = BooleanProperty(False)

class GamePiece(Widget):
    x = NumericProperty(0) 
    y = NumericProperty(0) 
    inner_pad = NumericProperty(0.5) 
    outer_pad = NumericProperty(0.35) 
    size = NumericProperty(50) 

    is_hole = BooleanProperty(True)
    is_circle = BooleanProperty(True)
    is_white = BooleanProperty(True)
    is_tall = BooleanProperty(True)

    is_highlighted = BooleanProperty(False)

    @property
    def high_pad(self) -> float:
        return self.outer_pad*0.7

    @property
    def inner_color(self) -> Tuple[float, float, float, float]:
        if self.is_white:
            if self.is_hole:
                return (0.5, 0.5, 0.5, 1.)
            else:
                return (0.5, 0.5, 0.5, 0.)
        else:
            if self.is_hole:
                return (0.25, 0.25, 0.25, 1.)
            else:
                return (0.5, 0.5, 0.5, 0.)

  