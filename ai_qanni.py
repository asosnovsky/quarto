import keras
import keras.layers
import numpy as np
from random import random, choice
from functools import reduce
from typing import Iterator, Tuple, Dict, NamedTuple, Optional
from src.boardstate import BoardState
from src.ai.trainer import AITrainer, AIModel, STATE, ACTION, AITrainerParams
from src.ai import ai_dumb, ai_3, run_vizsim_once

gmodel = keras.Sequential([
    keras.layers.Conv2D(input_shape=(4,4,5), kernel_size=4, filters=1, strides=1),
    keras.layers.Reshape((4,4)),
    keras.layers.LSTM(10),
    keras.layers.Dense(4, activation='relu'),
    # keras.layers.Flatten(),
    keras.layers.Dense(16, activation='tanh'),
])
gmodel.compile(optimizer='adamax',loss='mse')

class QNNAIParams(NamedTuple):
    learning_rate: float = 0.1
    discount_factor: float = 0.9
    gdrop_rate: float = 0.5
    pdrop_rate: float = 0.5
    drop_decy_rate: float = 0.9
    drop_decay_round: int = 100 # every 100 rounds of training

class QNNAI(AIModel):
    def as_dict(self) -> Dict:
        return {
            "params": tuple(self.params),
            "pmodel": self.pmodel.get_config(),
            "trounds": self.trained_rounds,
            "decay": [self.pdecay, self.gdecay]
        }

    @classmethod
    def from_dict(cls, d: Dict):
        qnnai = QNNAI(QNNAIParams(*d["params"]))
        qnnai.pmodel = keras.Sequential.from_config(d["pmodel"])
        qnnai.gmodel = keras.Sequential.from_config(d["gmodel"])
        qnnai.trained_rounds = d["trounds"]
        qnnai.pdecay = d["decay"][0]
        qnnai.gdecay = d["decay"][1]
        return qnnai

    def __init__(self, params: Optional[QNNAIParams] = None):
        AIModel.__init__(self, self.__class__.__name__)
        pmodel = keras.Sequential([
            keras.layers.Conv1D(input_shape=(17,5), kernel_size=4, filters=1, strides=1),
            keras.layers.LSTM(10),
            keras.layers.Dense(4, activation='relu'),
            keras.layers.Flatten(),
            keras.layers.Dense(5),
            keras.layers.Dense(16, activation='tanh'),
        ])
        pmodel.compile(optimizer='adamax',loss='mse')
        gmodel = keras.Sequential([
            keras.layers.Conv2D(input_shape=(4,4,5), kernel_size=4, filters=1, strides=1),
            keras.layers.LSTM(10),
            keras.layers.Dense(4, activation='relu'),
            keras.layers.Flatten(),
            keras.layers.Dense(5),
            keras.layers.Dense(16, activation='tanh'),
        ])
        gmodel.compile(optimizer='adamax',loss='mse')
        self.pmodel = pmodel
        self.gmodel = gmodel
        self.params = params if params is not None else QNNAIParams()
        self.trained_rounds = [0, 0] 
        self.pdecay = 0
        self.gdecay = 0

    def predict_next_action_place_pair(self, X: np.ndarray) -> Tuple[np.ndarray, int, ACTION]:
        Q = self.pmodel.predict(X).reshape(16)
        a = Q.argmax()
        move = (int(a / 4), a % 4)   
        return Q, a, move

    def predict_next_action_give(self, X: np.ndarray) -> Tuple[np.ndarray, int]:
        Q = self.gmodel.predict(X).reshape(16)
        piece = Q.argmax()
        return Q, piece

    def predict_next_placement_move(self, state: STATE) -> ACTION:
        if random() < self.params.pdrop_rate * ( self.params.drop_decy_rate ** self.pdecay ):
            b_np, _ = state
            a = choice([ i for i, chk in enumerate(~b_np[:,:,-1].flatten()) if chk ])
            return (int(a / 4), a % 4) 
        else:
            b_np, cp = state
            X = np.append(b_np.reshape(16,5), np.array([*cp, True]).reshape(1,5), axis=0).reshape(1, 17, 5)
            Q, a, move = self.predict_next_action_place_pair(X)
            for _ in range(100):
                if b_np[move[0], move[1], -1]:
                    Q[b_np[:,:,-1].flatten()] = -1000
                    self.pmodel.fit(
                        x = X,
                        y = Q.reshape(1,16),
                        verbose=0
                    )
                    _, a, move = self.predict_next_action_place_pair(X)
                else:
                    return move
            Q[b_np[:,:,-1].flatten()] = -100
            a = Q.argmax()
            move = (int(a / 4), a % 4)  
            if b_np[move[0], move[1], -1]:
                raise Exception("Still cannot find place valid piece")
            return move

    def predict_next_giving_move(self, state: np.ndarray) -> int:
        ep = state.reshape(16, 5)
        ep = ep[ep[:,-1], :-1].dot([ 2**n for n in reversed(range(4)) ])
        if random() < self.params.gdrop_rate * ( self.params.drop_decy_rate ** self.gdecay ):
            allowed_moves = [ i for i in range(16) if i not in ep ] 
            return choice(allowed_moves)       
        else:
            X = state.reshape(1, 4, 4, 5)
            Q, piece = self.predict_next_action_give(X)
            for _ in range(100):
                if piece in ep:
                    Q[ep] = -1000
                    self.gmodel.fit(
                        x = X,
                        y = Q.reshape(1,16),
                        verbose=0
                    )
                    _, piece = self.predict_next_action_give(X)
                else:
                    return piece
            Q[ep] = -100
            piece = Q.argmax()
            if piece in ep:
                raise Exception("Still cannot find valid piece")
            return piece

    def prep_next_placement_move(self, state: STATE) -> np.ndarray:
        (b_np, cp) = state
        return np.append(b_np.reshape(16,5), np.array([*cp, True]).reshape(1,5), axis=0).reshape(1,17,5)
        
    def fit_next_placement_move(self, state: STATE, action: ACTION, reward: float):
        X = self.prep_next_placement_move(state)
        Q = self.pmodel.predict(X).reshape(16,)
        a = action[0] * 4 + action[1]
        Q[a] = Q[a]*(1-self.params.learning_rate) + self.params.learning_rate*( reward + self.params.discount_factor * Q.max() )
        self.pmodel.fit(
            x = X,
            y = Q.reshape(1, 16),
            verbose=0
        )
        self.trained_rounds[0] += 1
        if self.trained_rounds[0] % 100 == 0:
            self.pdecay += 1

    def prep_next_giving_move(self, state: np.ndarray) -> np.ndarray:
        return state.reshape(1, 4, 4, 5)

    def fit_next_giving_move(self, state: np.ndarray, p: int, reward: float):
        X = self.prep_next_giving_move(state)
        Q = self.gmodel.predict(X).reshape(16,)
        Q[p] = Q[p]*(1-self.params.learning_rate) + self.params.learning_rate*( reward + self.params.discount_factor * Q.max() )
        self.gmodel.fit(
            x = X,
            y = Q.reshape(1, 16),
            verbose=0
        )
        self.trained_rounds[1] += 1
        if self.trained_rounds[1] % 100 == 0:
            self.gdecay += 1



trainer = AITrainer(
    QNNAI(),
    params=AITrainerParams(
        win_reward=10,
        loss_reward=-5,
        tie_reward=5
    )
)

print("training against dumb-ai")
trainer.train(ai_dumb, 10)

print("retraining...")
trainer.retrain()
trainer.play_against(ai_dumb, rounds=100, load_bar_position=0)

print("training against ai3")
trainer.train(ai_3, 1000)
trainer.play_against(ai_dumb, rounds=100, load_bar_position=0)
trainer.play_against(ai_3, rounds=100, load_bar_position=0)

trainer.retrain()
trainer.play_against(ai_dumb, rounds=100, load_bar_position=0)
trainer.play_against(ai_3, rounds=100, load_bar_position=0)

print("retraining...")
trainer.retrain()
trainer.play_against(ai_dumb, rounds=100, load_bar_position=0)
trainer.play_against(ai_3, rounds=100, load_bar_position=0)

# for i in range(10):
#     trainer.train(ai_3, 10)
#     run_vizsim_once(ai_3, trainer.as_ai_player())

# trainer.retrain()

import json

open('model.json', 'w').write(
    json.dumps(trainer.model.as_dict())
)

# board = BoardState()
# for _ in range(6):
#     board.ai_random_move()
# print(list(board.iter_datas()))
# trainer.determine_giving_action(board)
# state = board.into_numpy(True)

# trainer.model.predict_next_action_give(state.reshape(1,4,4,5))

import pandas as pd

ghist = pd.DataFrame(trainer.memory.game_ghistory)
phist = pd.DataFrame(trainer.memory.game_phistory)

ghist.to_pickle("ghist.pickle")
phist.to_pickle("phist.pickle")

row = trainer.memory.game_ghistory[0]

trainer.memory

ghist.loc[
    lambda r: r.state.apply(lambda s: s[:,:,-1].all())
]


ghist.assign(
    state = lambda x: x.state.apply(
        lambda s: "|".join(
            map(
                lambda n: str(n).zfill(2),
                s.dot([ 2**n for n in reversed(range(5)) ]).flatten()
            )
        )
    )
).groupby('state').apply(
    lambda g: pd.Series({"n": len(g)})
)
import matplotlib.pyplot as plt

plt.show()

