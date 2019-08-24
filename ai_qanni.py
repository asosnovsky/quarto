import keras
import keras.layers
import numpy as np
from random import random, choice
from functools import reduce
from typing import Iterator, Tuple, Dict, NamedTuple, Optional
from src.boardstate import BoardState
from src.ai.trainer import AITrainer, AIModel, STATE, ACTION
from src.ai import ai_dumb, ai_3, run_vizsim_once

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
            keras.layers.Conv1D(input_shape=(17,5), kernel_size=3, filters=3, strides=3),
            keras.layers.Flatten(),
            keras.layers.Dense(20),
            keras.layers.Dense(5),
            keras.layers.Dense(16, activation='tanh'),
        ])
        pmodel.compile(optimizer='adamax',loss='mse')
        gmodel = keras.Sequential([
            keras.layers.Conv2D(input_shape=(4,4,5), kernel_size=3, filters=3, strides=3),
            keras.layers.Flatten(),
            keras.layers.Dense(20),
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
            _, _, move = self.predict_next_action_place_pair(X)
            return move

    def fit_next_placement_move(self, state: STATE, action: ACTION, reward: float):
        (b_np, cp) = state
        X = np.append(b_np.reshape(16,5), np.array([*cp, True]).reshape(1,5), axis=0).reshape(1,17,5)
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

    def predict_next_giving_move(self, state: np.ndarray) -> int:
        if random() < self.params.gdrop_rate * ( self.params.drop_decy_rate ** self.gdecay ):
            ep = state.reshape(16, 5)
            ep = ep[ep[:,-1], :-1].dot([ 2**n for n in reversed(range(4)) ])
            allowed_moves = [ i for i in range(16) if i not in ep ] 
            return choice(allowed_moves)       
        else:
            X = state.reshape(1, 4, 4, 5)
            _, piece = self.predict_next_action_give(X)
            return piece

    def fit_next_giving_move(self, state: np.ndarray, p: int, reward: float):
        X = state.reshape(1, 4, 4, 5)
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



trainer = AITrainer(QNNAI())

# for i in range(10):
#     trainer.train(ai_dumb, 10)
#     run_vizsim_once(ai_dumb, trainer.as_ai_player())

print("training against dumb-ai")
trainer.train(ai_dumb, 1000)
trainer.play_against(ai_dumb, rounds=100, load_bar_position=0)

print("retraining...")
trainer.retrain()
trainer.play_against(ai_dumb, rounds=100, load_bar_position=0)
trainer.play_against(ai_3, rounds=100, load_bar_position=0)

print("training against ai3")
trainer.train(ai_3, 1000)
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