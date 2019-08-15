from random import random, choice, randint
from enum import Enum
from typing import Tuple, List, Dict, Optional, Iterator
from dataclasses import dataclass
from .widgets import GamePiece
from .boardstate import BoardState, GamePiece as GamePieceState

class PlayerState(Enum):
    PLAYER_1 = 'player 1'
    PLAYER_2 = 'player 2'
            

def gp_into_widget(self: GamePieceState, x: float, y: float, is_highlighted: bool = False, size: float = 100) -> GamePiece:
    return GamePiece(
        x=x,y=y, size=size,
        is_highlighted=is_highlighted,
        is_hole=self.is_hole,
        is_circle=self.is_circle,
        is_white=self.is_white,
        is_tall=self.is_tall,
    )

GamePieceState.into_widget = gp_into_widget

class GameState:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.board = BoardState()
        self.cplayer: PlayerState = PlayerState.PLAYER_1 if random() < 0.5 else PlayerState.PLAYER_2
        self.cpiece_id: Optional[int] = None
        self.cboard_id: Optional[Tuple[int, int]] = None
        self.current_highlight = choice(list(self.unused_game_pieces))[0]

    def switch_plauers(self):
        if self.cplayer == PlayerState.PLAYER_1:
            self.cplayer = PlayerState.PLAYER_2
        else:
            self.cplayer = PlayerState.PLAYER_1

    def match_board_id(self, r: int, c: int) -> bool:
        if self.cboard_id is not None:
            return (self.cboard_id[0] == r) & (self.cboard_id[1] == c)
        return False
    
    def set_highlight_randomly(self):
        if not self.board.is_full:
            self.current_highlight = choice(list(self.unused_game_pieces))[0] 

    def set_cboard_id_randomly(self):
        if not self.board.is_full:
            self.cboard_id = choice(list(self.board.open_spots))

    def next_highlight_v(self, up: bool, iter_safety= 0):
        last_ch = self.current_highlight
        if up:
            if (self.current_highlight+1) % 8 == 0:
                self.current_highlight -= 7
            elif self.current_highlight < 15:
                self.current_highlight += 1
        else: # down
            if (self.current_highlight+8) % 8 == 0:
                self.current_highlight += 8
            if self.current_highlight > 0:
                self.current_highlight -= 1
        if self.board.is_piece_id_in_board(self.current_highlight):
            if not self.board.is_full:
                if iter_safety < 8:
                    return self.next_highlight_v(up, iter_safety+1)
                else:
                    self.set_highlight_randomly()

    
    def next_highlight_h(self):
        last_ch = int(self.current_highlight)
        if self.current_highlight > 7:
            self.current_highlight -= 8
        else:
            self.current_highlight += 8

        if self.board.is_piece_id_in_board(self.current_highlight):
            self.current_highlight = last_ch

    @property
    def board_is_full(self) -> bool:
        for v in self.board.values():
            if v is None:
                return False
        return True

    @property
    def cpiece(self) -> Optional[GamePieceState]:
        if self.cpiece_id is not None:
            return self.board.get_piece(self.cpiece_id)
        return None

    @property
    def unused_game_pieces(self) -> Iterator[Tuple[int, GamePieceState]]:
        for i, gp in enumerate(self.board.iter_gamepieces()):
            if not self.board.is_piece_id_in_board(i):
                if i != self.cpiece_id:
                    yield i, gp
    
    def __iter__(self):
        for (r,c), v in self.board.iter_iddata():
            if v is not None:
                yield (r,c, self.board.get_piece(v))
            else:
                yield (r, c, None)
            