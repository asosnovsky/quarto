import numpy as np
import pandas as pd
import dataclasses
import matplotlib.pyplot as plt

from typing import NamedTuple, Tuple, Optional, List

from tqdm import tqdm
from src.ais import ai_3, AIPlayer
from src.boardstate import BoardState, GamePieceTuple, GamePiece

@dataclasses.dataclass
class Observation:
    game_id: int
    board: str
    piece_to_place: int
    # piece_to_place: int
    placement: Tuple[int, int]
    piece_to_give: int
    # piece_to_give: int
    reward: float = 0.0

def gen_train_samples(AI: AIPlayer, runs=1000, discount_factor = 0.9, win_reward = 1, lose_reward = -1) -> List[Observation]:
    obs : List[Observation] = []
    for game_id in tqdm(range(runs), desc='generating train samples'):
        board = BoardState()
        board.ai_random_move()
        first_idx = len(obs)
        for i in range(20):
            b = QTable.get_key_from_board(board)
            ptp = board.cpiece_id
            # ptp = board.get_piece_as_np(board.cpiece_id)
            board = AI(board)
            placement = board.last_move[0]
            ptg = board.cpiece_id
            ptg = board.get_piece_as_np(board.cpiece_id)
            if board.win_state is not None:
                win_player = game_id % 2 == 0
                df = discount_factor
                obs[-1].reward = lose_reward
                for obs_id in reversed(range(first_idx, i-1)):
                    if (obs_id % 2 == 0) == win_player:
                        obs[obs_id].reward = df*win_reward  
                    else:
                        obs[obs_id].reward = df*lose_reward
                        df *= discount_factor
                obs.append(Observation(game_id, b, ptp, placement, ptg, win_reward))
                break
            elif board.is_full:
                obs.append(Observation(game_id, b, ptp, placement, ptg, 0))
                break
            else:
                obs.append(Observation(game_id, b, ptp, placement, ptg))
        if i > 16:
            raise Exception(f"Too many iters i = {i} > 16")
            
    return obs

train = gen_train_samples(ai_3, 1)
train_df = pd.DataFrame(map(dataclasses.asdict, train))

for row in train_df.iterrows():
    qtable.update(row.board, row)


