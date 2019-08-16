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
from src.ais import ai_1, ai_2, ai_3, dumb_ai

def run_sim_once(ai1: AIPlayer, ai2: AIPlayer) -> Optional[int]:
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

run_sim_once(ai_3, ai_3)