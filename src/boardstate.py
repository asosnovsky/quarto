import random
import numpy as np
from itertools import permutations, repeat
from enum import Enum
from typing import Tuple, Dict, Optional, Iterator, List
from dataclasses import dataclass

GamePieceTuple = Tuple[bool, bool, bool, bool]

@dataclass
class GamePiece:

    is_hole: bool
    is_circle: bool
    is_white: bool
    is_tall: bool

    def into_tuple(self) -> GamePieceTuple:
        return (
            self.is_hole,
            self.is_circle,
            self.is_white,
            self.is_tall
        )
    
    def is_matched_with(self, others: Iterator[Optional[GamePieceTuple]]) -> bool:
        agg = self.into_tuple()
        for p in others:
            if p is None: return False
            else: 
                agg = [
                    a+b
                    for a,b in zip(agg, p)
                ]
        for n in agg:
            if (n == 4) or (n == 0):
                return True
        return False

    def __repr__(self):
        id = ""
        id += ( "h" if self.is_hole else "_" )
        id += ( "c" if self.is_circle else "_" )
        id += ( "w" if self.is_white else "_" )
        id += ( "t" if self.is_tall else "_" )
        return id
    
        
class BoardState:
    class WinType(Enum):
        HORIZONTAL = (1,0,0,0)
        VERTICAL = (0,1,0,0)
        DIAGNAL = (0,0,1,0)
        SQUARE = (0,0,0,1)

    ID = Tuple[int, int]
    DATA = Optional[int]
    def __init__(self):
        self.__board: Dict[ID, DATA] = {
            (r,c): None
            for r in range(4)
            for c in range(4)
        }
        self.__game_pieces: List[GamePiece] = [
            GamePiece(is_hole=hole, is_circle=circle, is_white=white, is_tall=tall)
            for hole in [True, False]
            for tall in [True, False]
            for white in [True, False]
            for circle in [True, False]
        ]
        self.win_state: Optional[Tuple[BoardState.WinType, BoardState.ID]] = None
        self.cpiece_id: Optional[int] = None
    
    @property
    def cpiece(self) -> Optional[GamePiece]:
        if self.cpiece_id is not None:
            return self.get_piece(self.cpiece_id)
        return None

    def iter_gamepieces(self) -> Iterator[GamePiece]:
        return iter(self.__game_pieces)
    
    def iter_ids(self) -> Iterator[ID]:
        for k in self.__board.keys():
            yield k
            
    def iter_datas(self) -> Iterator[DATA]:
        for v in self.__board.values():
            yield v
    
    def iter_iddata(self) -> Iterator[Tuple[ID, DATA]]:
        for (r,c), v in self.__board.items():
            yield (r,c), v
    
    def iter_kp(self) -> Iterator[Tuple[ID, DATA, Optional[GamePiece]]]:
        for (r,c), v in self.__board.items():
            if v is not None:
                yield (r,c), v, self.get_piece(v)
            else:
                yield (r,c), v, None
    
    def is_piece_id_in_board(self, idx: int) -> bool:
        return idx in self.__board.values()
    
    def get_piece(self, idx: int) -> GamePiece:
        return self.__game_pieces[idx]

    @property
    def is_full(self) -> bool:
        for v in self.__board.values():
            if v is None:
                return False
        return True

    @property
    def open_spots(self):
        for k, v in self.__board.items():
            if v is None:
                yield k
    
    @property
    def unused_game_pieces(self) -> Iterator[Tuple[int, GamePiece]]:
        for i, gp in enumerate(self.iter_gamepieces()):
            if not self.is_piece_id_in_board(i):
                if i != self.cpiece_id:
                    yield i, gp
    
    def __getitem__(self, index: ID) -> DATA:
        return self.__board[index]

    def __setitem__(self, index: ID, value: DATA):
        (x,y) = index
        if (x < 4) & (y < 4):
            self.__board[index] = value
            self.win_state = self.check_win(x, y)
        else:
            raise Exception(f"Invalid index ({x},{y}) !")

    def check_win(self, x: int, y: int) -> Optional[Tuple[WinType, ID]]:
        if self.__check_win_across_h(y):
            return self.WinType.HORIZONTAL, (x, y)
        if self.__check_win_across_v(x):
            return self.WinType.VERTICAL, (x, y)
        if self.__check_win_across_d(x, y):
            return self.WinType.DIAGNAL, (x, y)
        return None

    def __check_win_across_h(self, y: int) -> bool:
        return self.check_points_match(
            zip( range(4), repeat(y,4) )
        )

    def __check_win_across_v(self, x: int) -> bool:
        return self.check_points_match(
            zip(repeat(x,4), range(4) )
        )

    def __check_win_across_d(self, x: int, y: int) -> bool:
        if x == y:
            return self.check_points_match(
                zip(range(4),range(4))
            )
        elif x + y == 3:
            return self.check_points_match(
                zip(range(3,-1,-1),range(4))
            )
        return False
    
    def check_points_match(self, points: Iterator[ID]) -> bool:
        p1 = self[next(points)]
        if p1 is None:
            return False
        else:
            def get_piece_or_none(id: BoardState.ID) -> Optional[GamePieceTuple]:
                p = self[id]
                if p is None: return None
                else: return self.get_piece(p).into_tuple()

            return self.get_piece(p1).is_matched_with(map(
                get_piece_or_none,
                points
            ))

    def __repr__(self):
        return f"<Board win={self.win_state}>\n " + (
            "\n ".join([
                " | ".join([
                    f"{self.get_piece(self[x,y])}" if self[x,y] is not None else f"    "
                    for x in range(4)
                ])
                for y in range(3,-1,-1)
            ])
        ) + "\n<Board/>"

    
    def ai_random_move(self):
        self[random.choice(list(self.open_spots))] = self.cpiece_id
        if not self.is_full:
            self.cpiece_id, _ = random.choice(list(self.unused_game_pieces))

    def get_piece_as_np(self, id: Optional[int]) -> np.ndarray:
        if id is not None:
            return np.array([*self.get_piece(id).into_tuple(), False], dtype="bool")
        else:
            return np.zeros(shape=(5,), dtype="bool")

    def into_numpy(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Converts the state into three numpy arrays
        
        Returns:
            Tuple[np.ndarray[4,], np.ndarray] -- the first is the currently selected piece, the second the state of the board
        """
        return (
            # Win State : anything but 4 zeros mean win!
            np.array((0,0,0,0) if self.win_state is None else self.win_state.value, dtype="bool"),
            # Piece provided by last player
            self.get_piece_as_np(self.cpiece_id),
            # Board
            np.array([[
                self.get_piece_as_np(self[x,y])
                for y in range(4)
            ] for x in range(4) ])
        )
