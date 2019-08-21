
import numpy as np

from tqdm import tqdm
from random import choice
from typing import Iterator, Optional, Callable, List, Dict
from src.ai.helpers import (
    run_vizsim_once,
    run_sim_once,
    find_win_spot,
    choose_none_winable_piece,
    choose_none_winable_pieces,
    find_most_similar_piece,
    find_most_dissimilar_piece,
    get_open_dissimilar_spot,
    get_open_similar_spot,
    AIPlayer
)
from src.ai import ai_1, ai_2, ai_3, dumb_ai, AIPlayerMaker
from src.boardstate import BoardState, GamePiece


ai_4 = AI4()

rounds = 1000

stats: Dict[Optional[str], int] = {}
for _ in tqdm(range(rounds), desc=f"Testing", position=0):
    winner = run_sim_once(ai_4, ai_3)
    stats[winner] = stats.get(winner, 0) + 1
print(stats)

stats = {}
for _ in tqdm(range(rounds), desc=f"Testing", position=0):
    winner = run_sim_once(ai_4, ai_3)
    stats[winner] = stats.get(winner, 0) + 1
print(stats)

stats = {}
for _ in tqdm(range(rounds), desc=f"Testing", position=0):
    winner = run_sim_once(ai_4, ai_4)
    stats[winner] = stats.get(winner, 0) + 1
print(stats)



