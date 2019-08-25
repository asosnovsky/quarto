from tqdm import tqdm
from abc import abstractmethod
from typing import NamedTuple, Any, Tuple, List, Optional, Dict
from numpy import ndarray, append as np_append
from ..boardstate import BoardState, GamePieceTuple, GamePiece
from .maker import AIPlayerMaker, AIPlayer
from .helpers import choose_none_winable_piece, run_sim_once

ACTION = Tuple[int, int]
STATE = Tuple[ndarray, GamePieceTuple]

class AIModel:
    def __init__(self, name: str):
        self.__name__ = name
    @abstractmethod
    def fit_next_placement_move(self, state: STATE, action: ACTION, reward: float):
        pass
    @abstractmethod
    def predict_next_placement_move(self, state: STATE) -> ACTION:
        pass
    @abstractmethod
    def fit_next_giving_move(self, state: ndarray, action: int, reward: float):
        pass
    @abstractmethod
    def predict_next_giving_move(self, state: ndarray) -> int:
        pass
    @abstractmethod
    def prep_next_placement_move(self, state: STATE) -> ndarray:
        pass
    @abstractmethod
    def prep_next_giving_move(self, state: ndarray) -> ndarray:
        pass

    @abstractmethod
    def as_dict(self) -> Dict:
        pass

class AIMemory:
    class CGamePlacementRecord(NamedTuple):
        game_id: int
        state: STATE
        action: ACTION
    
    class CGameGivingRecord(NamedTuple):
        game_id: int
        state: ndarray
        action: int

    class HistGamePlacementRecord(NamedTuple):
        game_id: int
        state: STATE
        action: ACTION
        reward: float

    class HistGameGivingRecord(NamedTuple):
        game_id: int
        state: ndarray
        action: int
        reward: float
    
    def __init__(self):
        self.current_game_phistory: List[AIMemory.CGamePlacementRecord]  = []
        self.current_game_ghistory: List[AIMemory.CGameGivingRecord]  = []
        self.game_phistory: List[AIMemory.HistGamePlacementRecord]  = []
        self.game_ghistory: List[AIMemory.HistGameGivingRecord]  = []
        self.current_game_id = 0
    
    def record_placement(self, state: STATE, action: ACTION):
        self.current_game_phistory.append(AIMemory.CGamePlacementRecord(
            self.current_game_id,
            state,
            action,
        ))

    def record_giving(self, state: ndarray, action: int):
        self.current_game_ghistory.append(AIMemory.CGameGivingRecord(
            self.current_game_id,
            state,
            action,
        ))
    
    def into_recent_game_iter(self):
        while len(self.current_game_ghistory) > 0:
            gr, pr = self.current_game_ghistory.pop(), self.current_game_phistory.pop()
            grew, prew = yield gr, pr
            self.game_ghistory.append(AIMemory.HistGameGivingRecord(*gr, grew))
            self.game_phistory.append(AIMemory.HistGamePlacementRecord(*pr, prew))
        self.current_game_ghistory = []
        self.current_game_phistory = []
        self.current_game_id += 1
    
    def into_full_hist_iter(self):
        for gr, pr in zip(self.game_ghistory, self.game_phistory):
            yield gr, pr


class AITrainerParams(NamedTuple):
    win_reward: float = 1
    loss_reward: float = -2
    tie_reward: float = -1
    reward_df: float = 0.9
    bad_move_reward: float = -1000
    max_bad_iter: int = 1000

class AITrainer:

    def __init__(self, model: AIModel, params: Optional[AITrainerParams] = None):
        self.model = model
        self.memory = AIMemory()
        self.params: AITrainerParams = params if params is not None else AITrainerParams()
        self.stats = {"wins": 0, "losses": 0, "ties": 0}
        # self.win_reward = win_reward
        # self.loss_reward = loss_reward
        # self.tie_reward = tie_reward
        # self.reward_df = reward_df
        # self.bad_move_reward = bad_move_reward

    def determine_placement_action(self, board: BoardState, dont_record = True) -> ACTION:
        if board.cpiece is None:
            raise Exception("Attempting to save None cpiece")
        state = (board.into_numpy(True), board.cpiece.into_tuple())
        for _ in range(self.params.max_bad_iter):
            action = self.model.predict_next_placement_move(state)
            if board[action] is not None:
                self.model.fit_next_placement_move(state, action, self.params.bad_move_reward)
                if not dont_record:
                    self.memory.game_phistory.append(AIMemory.HistGamePlacementRecord(
                        self.memory.current_game_id,
                        state, action,
                        self.params.bad_move_reward
                    ))
            else:
                break
        if board[action] is not None:
            raise Exception("Still can't find next placement")
        if not dont_record:
            self.memory.record_placement(state, action)
        return action

    def determine_giving_action(self, board: BoardState, dont_record = True) -> int:
        if board.cpiece is None:
            raise Exception("Attempting to save None cpiece")
        state = board.into_numpy(True)
        for _ in range(self.params.max_bad_iter):
            action = self.model.predict_next_giving_move(state)
            if board.is_piece_id_in_board(action):
                self.model.fit_next_giving_move(state, action, self.params.bad_move_reward)
                if not dont_record:
                    self.memory.game_ghistory.append(AIMemory.HistGameGivingRecord(
                        self.memory.current_game_id,
                        state, action,
                        self.params.bad_move_reward
                    ))
            else:
                break
        if board.is_piece_id_in_board(action):
            raise Exception("Still can't find next piece")
        if not dont_record:
            self.memory.record_giving(state, action)
        return action

    def digest(self, as_winner: bool, is_tie = False):
        reward = self.params.win_reward
        if not as_winner:
            if is_tie:
                reward = self.params.tie_reward
                self.stats["ties"] += 1
            else:
                reward = self.params.loss_reward
                self.stats["losses"] += 1
        else:
            self.stats["wins"] += 1
        rgiter = self.memory.into_recent_game_iter()
        grecord, precord = next(rgiter)
        i = 0
        while True:
            rew = reward * ( self.params.reward_df**i )
            self.model.fit_next_placement_move(precord.state, precord.action, rew)
            self.model.fit_next_giving_move(grecord.state, grecord.action, rew)
            try:
                grecord, precord = rgiter.send((rew, rew))
                i += 1
            except StopIteration:
                break

    def retrain(self):
        for gr, pr in self.memory.into_full_hist_iter():
            self.model.fit_next_placement_move(pr.state, pr.action, pr.reward)
            self.model.fit_next_giving_move(gr.state, gr.action, gr.reward)

    def as_ai_player(self) -> AIPlayer:
        class AI(AIPlayerMaker):
            def select_piece_placement(aself, board: BoardState, cur_piece: GamePiece) -> Optional[BoardState.ID]:
                return self.determine_placement_action(board, True)
            def select_giving_piece(aself, board: BoardState, cur_piece: Optional[GamePiece]) -> BoardState.DATA:
                if cur_piece is None:
                    return choose_none_winable_piece(board)
                else:
                    return self.determine_giving_action(board, True)
        return AI(self.model.__name__)
    
    def play_against(self, ai: AIPlayer, me_first = False, rounds = 1, load_bar_position = 0):
        stats = {'Player 1': 0, 'Player 2': 0, None: 0}
        if me_first:
            for _ in tqdm(range(rounds), desc=f"ai vs aiq", position=load_bar_position):
                stats[run_sim_once(self.as_ai_player(), ai, use_names=False)] += 1
            return {
                "QAI": stats['Player 1'],
                "ai": stats['Player 2'],
                "Tie": stats[None],
            }
        else:
            for _ in tqdm(range(rounds), desc=f"aiq vs ai", position=load_bar_position):
                stats[run_sim_once(ai, self.as_ai_player(), use_names=False)] += 1
            return {
                "ai": stats['Player 1'],
                "QAI": stats['Player 2'],
                "Tie": stats[None],
            }

    def train(self, ai_enemy: AIPlayer, rounds: int = 100):
        self.stats = {"wins": 0, "losses": 0, "ties": 0}
        with tqdm(range(rounds), desc="Training...", position=0) as waiter:
            for _ in waiter:
                waiter.set_description(
                    f'Trainning...vs {ai_enemy.__name__} {self.stats["wins"]}/{self.stats["losses"]}-{self.stats["ties"]}'
                )
                # init application
                board = BoardState()
                curr_player = 0
                # randomly choose first piece
                board = board.ai_random_move()
                for _ in range(20):
                    if board.is_full:
                        self.digest(False, True)
                        break
                    if curr_player == 0:
                        board[self.determine_placement_action(board, dont_record=False)] = board.cpiece_id
                        if board.is_full:
                            self.digest(False, True)
                            break
                        board.cpiece_id = self.determine_giving_action(board, dont_record=False)
                    else:
                        board = ai_enemy(board)
                    if board.win_state is not None:
                        self.digest(curr_player == 0)
                        break

                    curr_player = 1 - curr_player

                # init application
                board = BoardState()
                curr_player = 0
                # randomly choose first piece
                board = board.ai_random_move()
                for _ in range(20):
                    if board.is_full:
                        self.digest(False, True)
                        break
                    if curr_player == 1:
                        board[self.determine_placement_action(board, dont_record=False)] = board.cpiece_id
                        if board.is_full:
                            self.digest(False, True)
                            break
                        board.cpiece_id = self.determine_giving_action(board, dont_record=False)
                    else:
                        board = ai_enemy(board)
                    if board.win_state is not None:
                        self.digest(curr_player == 0)
                        break

                    curr_player = 1 - curr_player


