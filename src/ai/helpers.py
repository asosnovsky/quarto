import numpy as np
from time import sleep
from typing import Iterator, Optional, Callable, List
from random import choice
from itertools import repeat
from ..boardstate import BoardState, GamePieceTuple, GamePiece

AIPlayer = Callable[[BoardState], BoardState]

def run_sim_once(ai1: AIPlayer, ai2: AIPlayer, use_names = True) -> Optional[str]:
    """Runs a simulation of two ais, returns the winning player or None if a ties
    
    Arguments:
        ai1 {AIPlayer}
        ai2 {AIPlayer}
    
    Returns:
        Optional[int] -- 0 for player 1, 1 for player 2 or None for a tie
    """
    ai1_name = f"Player 1: {ai1.__name__}" if use_names else 'Player 1'
    ai2_name = f"Player 2: {ai1.__name__}" if use_names else 'Player 2'
    current_ai = ai1_name
    board = BoardState()
    try:
        while True:
            if board.win_state is None:
                if board.is_full:
                    return None
                else:
                    if current_ai == ai1_name:
                        board = ai1(board)
                        current_ai = ai2_name
                    else:
                        current_ai = ai1_name
                        board = ai2(board)
            else:
                return ai1_name if current_ai == ai2_name else ai2_name
    except Exception as e:
        print(board)
        raise e


def run_vizsim_once(ai1: AIPlayer, ai2: AIPlayer) -> Optional[int]:
    """Runs a simulation of two ais, returns the winning player or None if a ties
        This differs from `run_sim_once` since it shows in console the simulation (slower)
    
    Arguments:
        ai1 {AIPlayer}
        ai2 {AIPlayer}
    
    Returns:
        Optional[int] -- 0 for player 1, 1 for player 2 or None for a tie
    """
    current_ai = 0
    board = BoardState()
    try:
        while True:
            print('\n'*100)
            print("current player:", current_ai)
            print("current piece:", board.cpiece)
            print(board)
            if board.win_state is None:
                if board.is_full:
                    return None
                else:
                    if current_ai == 0:
                        board = ai1(board)
                    else:
                        board = ai2(board)
                    current_ai = 1-current_ai
            else:
                print("The winner is Player #", current_ai)
                return 1-current_ai
            sleep(0.5)
    except Exception as e:
        print(board)
        raise e
    
def iter_to_pieces(board: BoardState, i: Iterator[BoardState.ID], cond: Callable[[BoardState.ID], bool]) -> Iterator[Optional[GamePieceTuple]]:
    """yeilds GamePieces in tuple form who's id are in the id list and match the condition
    loops over the provided id list, checks the condition against those i
    ds then yeilds if the cond return true otherwise return None
    
    Arguments:
        board {BoardState}
        i {Iterator[BoardState.ID]} -- a list of ids
        cond {Callable[[BoardState.ID], bool]} -- the condition that validates the id
    
    Returns:
        Iterator[Optional[GamePieceTuple]]
    """
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


def choose_none_winable_pieces(board: BoardState) -> Iterator[int]:
    for id, gp in board.unused_game_pieces:
        if find_win_spot(gp, board) is None:
            yield id

def choose_none_winable_piece(board: BoardState) -> Optional[int]:
    none_winable_pieces = list(choose_none_winable_pieces(board))
    if len(none_winable_pieces) > 0:
        return choice(none_winable_pieces)
    return None

def find_most_similar_piece(board: BoardState, cpiece: GamePiece) -> Optional[int]:
    p_np = np.array(cpiece.into_tuple(), dtype='int')
    it = choose_none_winable_pieces(board)

    try:
        c_p = next(it)
    except StopIteration:
        return None

    c_pn = np.array(board.get_piece(c_p).into_tuple(), dtype='int')
    c_sim = ((c_pn - p_np) ** 2).sum()

    for p in it:
        pn = np.array(board.get_piece(p).into_tuple(), dtype='int')
        sim = ((pn - p_np) ** 2).sum()
        if sim < c_sim:
            c_p, c_pn, c_sim = p, pn, sim

    return c_p


def find_most_dissimilar_piece(board: BoardState, cpiece: GamePiece) -> Optional[int]:
    p_np = np.array(cpiece.into_tuple(), dtype='int')
    it = choose_none_winable_pieces(board)

    try:
        c_p = next(it)
    except StopIteration:
        return None

    c_pn = np.array(board.get_piece(c_p).into_tuple(), dtype='int')
    c_sim = ((c_pn - p_np) ** 2).sum()

    for p in it:
        pn = np.array(board.get_piece(p).into_tuple(), dtype='int')
        sim = ((pn - p_np) ** 2).sum()
        if sim > c_sim:
            c_p, c_pn, c_sim = p, pn, sim

    return c_p


def get_open_dissimilar_spot(board: BoardState, cpiece: GamePiece, axis = 0) -> Optional[BoardState.ID]:
    b_np = board.into_numpy(True)
    p_np = np.array(cpiece.into_tuple())
    open_spots = np.array(list(board.open_spots))
    if open_spots.shape[0] == 0:
        return None
    it = iter(set(open_spots[:,axis]))

    def compute_sim(r: int) -> int:
        if axis == 0:
            filled_ones = b_np[r,:,:-1][b_np[r,:,-1]]
        else:
            filled_ones = b_np[:,r,:-1][b_np[:,r,-1]]
        if filled_ones.shape[0] > 0:
            return ((filled_ones == p_np).sum(axis=1) > 0).sum() / filled_ones.shape[0]
        return 0

    c_r, c_sim = 0, compute_sim(next(it))
    for r in it:
        sim = compute_sim(r)
        if sim > c_sim:
            c_r, c_sim = r, sim

    return tuple(open_spots[(open_spots[:,0] == c_r).argmax(),:])

def get_open_similar_spot(board: BoardState, cpiece: GamePiece, axis = 0) -> Optional[BoardState.ID]:
    b_np = board.into_numpy(True)
    p_np = np.array(cpiece.into_tuple())
    open_spots = np.array(list(board.open_spots))
    if open_spots.shape[0] == 0:
        return None
    it = iter(set(open_spots[:,axis]))

    def compute_sim(r: int) -> int:
        if axis == 0:
            filled_ones = b_np[r,:,:-1][b_np[r,:,-1]]
        else:
            filled_ones = b_np[:,r,:-1][b_np[:,r,-1]]
        if filled_ones.shape[0] > 0:
            return ((filled_ones == p_np).sum(axis=1) > 0).sum() / filled_ones.shape[0]
        return 0

    c_r, c_sim = 0, compute_sim(next(it))
    for r in it:
        sim = compute_sim(r)
        if sim < c_sim:
            c_r, c_sim = r, sim

    return tuple(open_spots[(open_spots[:,0] == c_r).argmax(),:])
