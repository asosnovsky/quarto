from tqdm import tqdm
from time import sleep
from typing import Iterator, Optional, Callable
from random import choice
from itertools import repeat
from functools import reduce
from src.boardstate import BoardState, GamePieceTuple
from src.ai_helpters import (
    iter_to_pieces, update_board_then_give_random, find_win_spot, 
    choose_none_winable_piece,
    AIPlayer
)

dumb_ai = lambda b: b.ai_random_move()

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

def ai_3(board: BoardState) -> BoardState:
    """This AI will always give a none-winable piece (if there is one) and will place randomly
    """
    cur_piece = board.cpiece
    if cur_piece is not None:
        moved = False
        for (x,y) in board.open_spots:
            move = find_win_spot(cur_piece, board)
            if move:
                board[move] = board.cpiece_id
                moved = True
                break
        if not moved:
            board[choice(list(board.open_spots))] = board.cpiece_id
        board.cpiece_id = choose_none_winable_piece(board)
    else:
        board.cpiece_id = choose_none_winable_piece(board)

    if (board.cpiece_id is None) and not board.is_full:
        board.cpiece_id, _ = choice(list(board.unused_game_pieces))
    return board
