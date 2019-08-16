import random
from typing import Tuple
import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window, Keyboard
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import ObservableList
from kivy.clock import Clock

kivy.require('1.11.1')

from .widgets import BorderedRect, Banner
from .state import GameState


class QuartoGame(Widget):
    def __init__(self, **kwargs):
        from kivy.core.window import Window, Keyboard
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
        elif self.game_state.board.cpiece_id is None:
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
            self.on_piece_play()

    def _on_keyboard_during_pselect(self, keycode: Tuple[int, str]):
        if keycode[1] == "up":
            self.game_state.next_highlight_v(True)
        elif keycode[1] == "down":
            self.game_state.next_highlight_v(False)
        elif keycode[1] in ["left", "right"]:
            self.game_state.next_highlight_h()
        elif keycode[1] == "enter":
            self.on_piece_select()
    
    def on_piece_play(self):
        if self.game_state.board[self.game_state.cboard_id] == None:
            self.game_state.board[self.game_state.cboard_id] = self.game_state.board.cpiece_id
            self.game_state.cboard_id = None
            self.game_state.board.cpiece_id = None
            self.game_state.set_highlight_randomly()
    
    def on_piece_select(self):
        self.game_state.board.cpiece_id = self.game_state.current_highlight
        self.game_state.set_cboard_id_randomly()
        self.game_state.switch_plauers()

    def draw_current_things(self):
        self.add_widget(Label(
            text = "Current Player: " + self.game_state.cplayer.value,
            center_x = self.center_x, 
            center_y = self.center_y - 300,
            font_size = 24
        ))
        self.add_widget(Label(
            text = f"{self.game_state.game_type}",
            x = 48, 
            top = self.top,
            font_size = 24
        ))
        cpiece = self.game_state.board.cpiece
        if cpiece is not None:
            self.add_widget(cpiece.into_widget(
                x=self.center_x - 25,
                y = self.center_y - 275,
                size = 50,
                is_highlighted = True
            ))
    
    def draw_board(self, size = 100):
        (x,y) = (self.center_x, self.center_y)
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
    
    def draw_unused_pieces(self, size = 100):
        (x,y,size) = (self.center_x + 2.5*size, self.center_y - 2*size, size/2)
        for i, gp in self.game_state.board.unused_game_pieces:
            self.add_widget(gp.into_widget(
                x=( 1*(i>7) )*size + x,
                y=( i - 8*(i>7) )*size + y,
                size = size,
                is_highlighted = False if self.game_state.board.cpiece_id is not None else self.game_state.current_highlight == i
            ))

    def draw_usual_game_play(self):
        self.draw_current_things();
        self.draw_board();
        self.draw_unused_pieces();
        if self.game_state.board.win_state is not None:
            self.add_widget(Banner(
                text=f"{self.game_state.cplayer.value} has won the game!",
                size=[650, 300],
                center_x=self.center_x,
                center_y=self.center_y,
            ))
            self.add_widget(Button(
                text = "Play Again",
                size= (100, 50),
                center_x = self.center_x,
                center_y = self.center_y - 75,
                on_press = lambda _: self.game_state.reset(GameState.GameType.PvP, False)
            ))
            Clock.schedule_once(self.update, 1.0 / 60.0)
        elif self.game_state.game_type == GameState.GameType.AvA:
            self.game_state.board.ai_random_move()
            self.game_state.switch_plauers()
            Clock.schedule_once(self.update, 15.0 / 60.0)
        elif self.game_state.game_type == GameState.GameType.PvA:
            if self.game_state.cplayer == GameState.PlayerState.PLAYER_2:
                self.game_state.board.ai_random_move()
                self.game_state.switch_plauers()
                self.game_state.set_cboard_id_randomly()
                Clock.schedule_once(self.update, 10.0 / 60.0)
            else:
                Clock.schedule_once(self.update, 1.0 / 60.0)
        else:
            Clock.schedule_once(self.update, 1.0 / 60.0)


    def update(self, dt: float = 1.0 / 60.0):
        self.clear_widgets();
        if self.game_state.started:
            self.draw_usual_game_play()
        else:
            self.add_widget(Banner(
                text=f"Choose the gamepay style",
                size=[650, 300],
                center_x=self.center_x,
                center_y=self.center_y,
            ))
            self.add_widget(Button(
                text = "PvP",
                size= (100, 50),
                center_x = self.center_x - 100,
                center_y = self.center_y - 75,
                on_press = lambda _: self.game_state.reset(GameState.GameType.PvP, True)
            ))
            self.add_widget(Button(
                text = "PvA",
                size= (100, 50),
                center_x = self.center_x,
                center_y = self.center_y - 75,
                on_press = lambda _: self.game_state.reset(GameState.GameType.PvA, True)
            ))
            self.add_widget(Button(
                text = "AvA",
                size= (100, 50),
                center_x = self.center_x + 100,
                center_y = self.center_y - 75,
                on_press = lambda _: self.game_state.reset(GameState.GameType.AvA, True)
            ))
            Clock.schedule_once(self.update, 1.0 / 60.0)


class QuartoApp(App):
    def build(self):
        Window.size = [1000, 700]
        game = QuartoGame()
        Clock.schedule_once(game.update, 1.0 / 60.0)
        return game

def run_app():
    QuartoApp().run()