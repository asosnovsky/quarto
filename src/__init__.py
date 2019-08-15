import kivy
from typing import Tuple
from kivy.config import Config
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.core.window import Window, Keyboard
from kivy.properties import (
    ObservableList, 
)
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color, Ellipse
from .widgets import BorderedRect, WinBanner
from .state import GameState

kivy.require('1.11.1')

class QuartoGame(Widget):
    def __init__(self, **kwargs):
        super(QuartoGame, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.game_state = GameState()
    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard: Keyboard, keycode: Tuple[int, str], text: str, modifiers: ObservableList):
        if self.game_state.board.win_state is not None:
            pass
        elif self.game_state.cpiece_id is None:
            self._on_keyboard_during_pselect(keycode)
        else:
            self._on_keyboard_during_pplace(keycode)

    def _on_keyboard_during_pplace(self, keycode: Tuple[int, str]):
        if keycode[1] == "up":
            if (self.game_state.cboard_id[1]+1) % 4 == 0:
                self.game_state.cboard_id = (self.game_state.cboard_id[0], self.game_state.cboard_id[1]-3)
            else:
                self.game_state.cboard_id = (self.game_state.cboard_id[0], self.game_state.cboard_id[1]+1)
        elif keycode[1] == "down":
            if (self.game_state.cboard_id[1]+4) % 4 == 0:
                self.game_state.cboard_id = (self.game_state.cboard_id[0], self.game_state.cboard_id[1]+3)
            else:
                self.game_state.cboard_id = (self.game_state.cboard_id[0], self.game_state.cboard_id[1]-1)
        elif keycode[1] == "left":
            if (self.game_state.cboard_id[0]+4) % 4 == 0:
                self.game_state.cboard_id = (self.game_state.cboard_id[0]+3, self.game_state.cboard_id[1])
            else:
                self.game_state.cboard_id = (self.game_state.cboard_id[0]-1, self.game_state.cboard_id[1])
        elif keycode[1] == "right":
            if (self.game_state.cboard_id[0]+1) % 4 == 0:
                self.game_state.cboard_id = (self.game_state.cboard_id[0]-3, self.game_state.cboard_id[1])
            else:
                self.game_state.cboard_id = (self.game_state.cboard_id[0]+1, self.game_state.cboard_id[1])
        elif keycode[1] == "enter":
            if self.game_state.board[self.game_state.cboard_id] == None:
                self.game_state.board[self.game_state.cboard_id] = self.game_state.cpiece_id
                self.game_state.cboard_id = None
                self.game_state.cpiece_id = None
                self.game_state.set_highlight_randomly()

    def _on_keyboard_during_pselect(self, keycode: Tuple[int, str]):
        if keycode[1] == "up":
            self.game_state.next_highlight_v(True)
        elif keycode[1] == "down":
            self.game_state.next_highlight_v(False)
        elif keycode[1] in ["left", "right"]:
            self.game_state.next_highlight_h()
        elif keycode[1] == "enter":
            self.game_state.cpiece_id = self.game_state.current_highlight
            self.game_state.set_cboard_id_randomly()
            self.game_state.switch_plauers()

    def update(self, dt: float = 1.0 / 60.0):
        self.clear_widgets();
        self.add_widget(Label(
            text = "Current Player: " + self.game_state.cplayer.value,
            center_x = self.center_x, 
            center_y = self.center_y - 300,
            font_size = 24
        ))
        cpiece = self.game_state.cpiece
        if cpiece is not None:
            self.add_widget(cpiece.into_widget(
                x=self.center_x - 25,
                y = self.center_y - 275,
                size = 50,
                is_highlighted = True
            ))

        (x,y,size) = (self.center_x, self.center_y, 100)
        for (r,c,v) in self.game_state:
            self.add_widget(BorderedRect(
                x=(r-2)*size + x, 
                y=(c-2)*size + y, 
                size=size,
                is_highlighted = self.game_state.match_board_id(r, c)
            ))
            if v is not None:
                self.add_widget(v.into_widget(
                    x=(r-2)*size + x, 
                    y=(c-2)*size + y, 
                    size=size
                ))
        
        (x,y,size) = (self.center_x + 2.5*size, self.center_y - 2*size, 50)
        for i, gp in self.game_state.unused_game_pieces:
            self.add_widget(gp.into_widget(
                x=( 1*(i>7) )*size + x,
                y=( i - 8*(i>7) )*size + y,
                size = size,
                is_highlighted = False if self.game_state.cpiece_id is not None else self.game_state.current_highlight == i
            ))
        
        if self.game_state.board.win_state is not None:
            self.add_widget(WinBanner(
                pname=self.game_state.cplayer.value,
                center_x=self.center_x,
                center_y=self.center_y,
            ))
            self.add_widget(Button(
                text = "Play Again",
                size= (100, 50),
                center_x = self.center_x,
                center_y = self.center_y - 75,
                on_press = lambda _: self.game_state.reset()
            ))


class QuartoApp(App):
    def build(self):
        Window.size = [1000, 700]
        game = QuartoGame()
        Clock.schedule_interval(game.update, 1.0 / 60.0)
        return game


