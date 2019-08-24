import keras
import keras.layers
import numpy as np
from functools import reduce
from typing import Iterator, Tuple, Dict
from src.boardstate import BoardState
from src.ai.trainer import AITrainer, AIModel, STATE, ACTION
from src.ai import ai_dumb, ai_3, run_vizsim_once

class QNNAI(AIModel):
    def as_dict(self) -> Dict:
        return {
            "lr": self.lr,
            "df": self.df,
            "pmodel": self.pmodel.get_config()
        }

    @classmethod
    def from_dict(cls, d: Dict):
        qnnai = QNNAI(d["lr"], d["df"])
        qnnai.pmodel = keras.Sequential.from_config(d["pmodel"])
        qnnai.gmodel = keras.Sequential.from_config(d["gmodel"])
        return qnnai

    def __init__(self, learning_rate = 0.1, discount_factor = 0.9, drop_rate = 0.5, drop_decy_rate = 0.9):
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
        self.lr = learning_rate
        self.df = discount_factor
        self.dr = drop_rate
        self.dcr = drop_decy_rate    

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
        (b_np, cp) = state
        X = np.append(b_np.reshape(16,5), np.array([*cp, True]).reshape(1,5), axis=0).reshape(1, 17, 5)
        _, _, move = self.predict_next_action_place_pair(X)
        # for _ in range(100):
        #     if b_np[move[0], move[1], -1]:
        #         Q[b_np[:,:,-1].flatten()] = -100
        #         self.pmodel.fit(
        #             x = X,
        #             y = Q.reshape(1,16),
        #             verbose=0
        #         )
        #         _, a, move = self.predict_next_action_place_pair(X)
        #     else:
        #         return move
        # Q[b_np[:,:,-1].flatten()] = -100
        # a = Q.argmax()
        # move = (int(a / 4), a % 4)  
        # if b_np[move[0], move[1], -1]:
        #     raise Exception("Still cannot find place valid piece")
        return move

    def fit_next_placement_move(self, state: STATE, action: ACTION, reward: float):
        (b_np, cp) = state
        X = np.append(b_np.reshape(16,5), np.array([*cp, True]).reshape(1,5), axis=0).reshape(1,17,5)
        Q = self.pmodel.predict(X).reshape(16,)
        a = action[0] * 4 + action[1]
        Q[a] = Q[a]*(1-self.lr) + self.lr*( reward + self.df * Q.max() )
        self.pmodel.fit(
            x = X,
            y = Q.reshape(1, 16),
            verbose=0
        )

    def predict_next_giving_move(self, state: np.ndarray) -> int:
        X = state.reshape(1, 4, 4, 5)
        # ep = state.reshape(16, 5)
        # ep = ep[ep[:,-1], :-1].dot([ 2**n for n in reversed(range(4)) ])
        _, piece = self.predict_next_action_give(X)
        # for _ in range(100):
        #     if piece in ep:
        #         Q[ep] = -100
        #         self.gmodel.fit(
        #             x = X,
        #             y = Q.reshape(1,16),
        #             verbose=0
        #         )
        #         _, piece = self.predict_next_action_give(X)
        #     else:
        #         return piece
        # Q[ep] = -100
        # piece = Q.argmax()
        # if piece in ep:
        #     raise Exception("Still cannot find valid piece")
        return piece


    def fit_next_giving_move(self, state: np.ndarray, p: int, reward: float):
        X = state.reshape(1, 4, 4, 5)
        Q = self.gmodel.predict(X).reshape(16,)
        Q[p] = Q[p]*(1-self.lr) + self.lr*( reward + self.df * Q.max() )
        self.gmodel.fit(
            x = X,
            y = Q.reshape(1, 16),
            verbose=0
        )



trainer = AITrainer(QNNAI())

for i in range(10):
    trainer.train(ai_dumb, 10)
    run_vizsim_once(ai_dumb, trainer.as_ai_player())
    trainer.play_against(ai_dumb, rounds=100, load_bar_position=0)

trainer.retrain()
trainer.train(ai_dumb, 1000)
trainer.retrain()
trainer.train(ai_3, 1000)


for i in range(10):
    trainer.train(ai_3, 10)
    run_vizsim_once(ai_3, trainer.as_ai_player())
    trainer.play_against(ai_3, rounds=100, load_bar_position=0)

trainer.retrain()

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