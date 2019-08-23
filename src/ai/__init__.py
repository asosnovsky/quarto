from tqdm import tqdm
from time import sleep
from typing import Iterator, Optional, Callable
from random import choice
from itertools import repeat
from functools import reduce, partial
from ..boardstate import BoardState, GamePieceTuple
from .helpers import *
from .maker import AIPlayerMaker, into_aiplayer

ai_dumb = lambda b: b.ai_random_move()
ai_dumb.__name__ = "ai_dumb"

def ai_1(board: BoardState) -> BoardState:
    """This AI will always choose the winning spot, if there is no winning spot it will place randomly
    """
    cur_piece = board.cpiece
    if cur_piece is not None:
        for (x,y) in board.open_spots:
            move = find_win_spot(cur_piece, board)
            if move:
                return update_board_then_give_random(board, move)
    board.ai_random_move()
    return board

def ai_2(board: BoardState) -> BoardState:
    """This AI will always give a none-winable piece (if there is one) and will place randomly
    """
    cur_piece = board.cpiece
    if cur_piece is None:
        board.cpiece_id = choose_none_winable_piece(board)
    else:
        board[choice(list(board.open_spots))] = board.cpiece_id
        board.cpiece_id = choose_none_winable_piece(board)

    if (board.cpiece_id is None) and not board.is_full:
        board.cpiece_id, _ = choice(list(board.unused_game_pieces))
    return board

@into_aiplayer
class ai_3(AIPlayerMaker):
    """This AI will always give a none-winable piece (if there is one) and will place a none-winable piece
    """
    def select_piece_placement(self, board: BoardState, cur_piece: GamePiece) -> Optional[BoardState.ID]:
        return find_win_spot_in_board(board, cur_piece)
    def select_giving_piece(self, board: BoardState, cur_piece: Optional[GamePiece]) -> BoardState.DATA:
        return choose_none_winable_piece(board)

@into_aiplayer
class ai_3s(AIPlayerMaker):
    """This AI will always give a none-winable most similar piece (if there is one) and will place a none-winable piece
    """
    def select_piece_placement(self, board: BoardState, cur_piece: GamePiece) -> Optional[BoardState.ID]:
        return find_win_spot_in_board(board, cur_piece)
    def select_giving_piece(self, board: BoardState, cur_piece: Optional[GamePiece]) -> BoardState.DATA:
        if cur_piece is None:
            return choose_none_winable_piece(board)
        else:
            return find_most_similar_piece(board, cur_piece)

@into_aiplayer
class ai_3d(AIPlayerMaker):
    """This AI will always give a none-winable most dissimilar piece (if there is one) and will place a none-winable piece
    """
    def select_piece_placement(self, board: BoardState, cur_piece: GamePiece) -> Optional[BoardState.ID]:
        return find_win_spot_in_board(board, cur_piece)
    def select_giving_piece(self, board: BoardState, cur_piece: Optional[GamePiece]) -> BoardState.DATA:
        if cur_piece is None:
            return choose_none_winable_piece(board)
        else:
            return find_most_similar_piece(board, cur_piece)

@into_aiplayer
class ai_dp_ms(AIPlayerMaker):
    def select_piece_placement(self, board: BoardState, cur_piece: GamePiece) -> Optional[BoardState.ID]:
        return try_actions(board, cur_piece, [
            find_win_spot_in_board,
            partial(get_open_dissimilar_spot, axis=0),
            partial(get_open_dissimilar_spot, axis=1),
        ])
    def select_giving_piece(self, board: BoardState, cur_piece: Optional[GamePiece]) -> BoardState.DATA:
        if cur_piece is None:
            return choose_none_winable_piece(board)
        else:
            return find_most_similar_piece(board, cur_piece)

@into_aiplayer
class ai_sp_ms(AIPlayerMaker):
    def select_piece_placement(self, board: BoardState, cur_piece: GamePiece) -> Optional[BoardState.ID]:
        return try_actions(board, cur_piece, [
            find_win_spot_in_board,
            partial(get_open_similar_spot, axis=0),
            partial(get_open_similar_spot, axis=1),
        ])
    def select_giving_piece(self, board: BoardState, cur_piece: Optional[GamePiece]) -> BoardState.DATA:
        if cur_piece is None:
            return choose_none_winable_piece(board)
        else:
            return find_most_similar_piece(board, cur_piece)

@into_aiplayer
class ai_sp_dp(AIPlayerMaker):
    def select_piece_placement(self, board: BoardState, cur_piece: GamePiece) -> Optional[BoardState.ID]:
        return try_actions(board, cur_piece, [
            find_win_spot_in_board,
            partial(get_open_similar_spot, axis=0),
            partial(get_open_similar_spot, axis=1),
        ])
    def select_giving_piece(self, board: BoardState, cur_piece: Optional[GamePiece]) -> BoardState.DATA:
        if cur_piece is None:
            return choose_none_winable_piece(board)
        else:
            return find_most_dissimilar_piece(board, cur_piece)

@into_aiplayer
class ai_dp_dp(AIPlayerMaker):
    def select_piece_placement(self, board: BoardState, cur_piece: GamePiece) -> Optional[BoardState.ID]:
        return try_actions(board, cur_piece, [
            find_win_spot_in_board,
            partial(get_open_dissimilar_spot, axis=0),
            partial(get_open_dissimilar_spot, axis=1),
        ])
    def select_giving_piece(self, board: BoardState, cur_piece: Optional[GamePiece]) -> BoardState.DATA:
        if cur_piece is None:
            return choose_none_winable_piece(board)
        else:
            return find_most_dissimilar_piece(board, cur_piece)
