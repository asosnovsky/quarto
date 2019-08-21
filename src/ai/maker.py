from random import choice
from typing import Optional, Callable
from abc import abstractmethod
from ..boardstate import BoardState, GamePiece
from .helpers import AIPlayer, find_win_spot

PiecePlacement = Callable[[BoardState, GamePiece], Optional[BoardState.ID]]
PieceSelect = Callable[[BoardState, Optional[GamePiece]], Optional[BoardState.ID]]

class AIPlayerMaker:
    def __init__(self):
        self.__name__ = self.__class__.__name__
    @abstractmethod
    def select_piece_placement(self, board: BoardState, cur_piece: GamePiece) -> Optional[BoardState.ID]:
        pass
    @abstractmethod
    def select_giving_piece(self, board: BoardState, cur_piece: Optional[GamePiece]) -> BoardState.DATA:
        pass
    def __call__(self, board: BoardState) -> BoardState:
        cur_piece = board.cpiece
        if cur_piece is not None:
            moved = False
            for (x,y) in board.open_spots:
                move = find_win_spot(cur_piece, board)
                if move is not None:
                    board[move] = board.cpiece_id
                    moved = True
                    break
            if not moved:
                move = self.select_piece_placement(board, cur_piece)
                if move is not None:
                    board[move] = board.cpiece_id
                else:
                    board[choice(list(board.open_spots))] = board.cpiece_id
            board.cpiece_id = self.select_giving_piece(board, cur_piece)
        else:
            board.cpiece_id = self.select_giving_piece(board, None)

        if (board.cpiece_id is None) and not board.is_full:
            board.cpiece_id, _ = choice(list(board.unused_game_pieces))
        return board

def into_aiplayer(cls) -> AIPlayer:
    return cls()