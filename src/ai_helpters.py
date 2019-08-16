from typing import Iterator, Optional, Callable
from random import choice
from itertools import repeat
from .boardstate import BoardState, GamePieceTuple, GamePiece

AIPlayer = Callable[[BoardState], BoardState]

def iter_to_pieces(board: BoardState, i: Iterator[BoardState.ID], cond: Callable[[BoardState.ID], bool]) -> Iterator[Optional[GamePieceTuple]]:
    for t in i:
        if not cond(t):
            p = board[t]
            if p is None:
                yield None
            else:
                yield board.get_piece(p).into_tuple()

def update_board_then_give_random(board: BoardState, move: BoardState.ID) -> BoardState:
    board[move] = board.cpiece_id
    if not board.is_full:
        board.cpiece_id, _ = choice(list(board.unused_game_pieces))
    return board

def find_win_spot(cur_piece: GamePiece, board: BoardState) -> Optional[BoardState.ID]:
    for (x,y) in board.open_spots:
        if cur_piece.is_matched_with(iter_to_pieces(
            board,
            zip(range(4), repeat(y, 4)),
            lambda t: t[0] == x
        )): return (x,y)
        if cur_piece.is_matched_with(iter_to_pieces(
            board,
            zip(repeat(x, 4), range(4)),
            lambda t: t[1] == y
        )): return (x,y)
        if cur_piece.is_matched_with(iter_to_pieces(
            board,
            zip(range(4),range(4)),
            lambda t: t[1] == y
        )): return (x,y)
        if cur_piece.is_matched_with(iter_to_pieces(
            board,
            zip(range(3,-1,-1),range(4)),
            lambda t: t[1] == y
        )): return (x,y)
    return None


def choose_none_winable_piece(board) -> Optional[int]:
    none_winable_pieces = [
        id
        for id, gp in board.unused_game_pieces
        if find_win_spot(gp, board) is None
    ]
    if len(none_winable_pieces) > 0:
        return choice(none_winable_pieces)
    return None