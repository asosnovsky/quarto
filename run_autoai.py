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
                return 1-current_ai
    except Exception as e:
        print(board)
        raise e


test = [
    ("dumb ai fight", dumb_ai, dumb_ai),
    ("dumb ai vs ai1", dumb_ai, ai_1),
    ("ai1 vs dumb ai", ai_1, dumb_ai),
    ("ai1 fight", ai_1, ai_1),
    
    ("dumb ai vs ai2", dumb_ai, ai_2),
    ("ai2 vs dumb ai", ai_2, dumb_ai),
    ("ai2 ai vs ai1", ai_2, ai_1),
    ("ai1 ai vs ai2", ai_1, ai_2),
    ("ai2 fight", ai_2, ai_2),

    ("dumb ai vs ai3", dumb_ai, ai_3),
    ("ai3 vs dumb ai", ai_3, dumb_ai),
    ("ai3 ai vs ai1", ai_3, ai_1),
    ("ai1 ai vs ai3", ai_1, ai_3),
    ("ai3 ai vs ai2", ai_3, ai_2),
    ("ai2 ai vs ai3", ai_2, ai_3),
    ("ai3 fight", ai_3, ai_3),
]
completed_tests = {}
for name, ai1, ai2 in tqdm(test, desc="Testing...", position=0):
    stats = {0: 0, 1: 0, None: 0}
    for _ in tqdm(range(1000), desc=f"Testing {name}", position=1):
        stats[run_sim_once(ai1, ai2)] += 1
    completed_tests[name] = {
        "#1": stats[0],
        "#2": stats[1],
        "Tie": stats[None],
    }

print(completed_tests)
