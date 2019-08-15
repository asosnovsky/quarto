from enum import Enum
from typing import Tuple, Dict, Optional, Iterator, List
from dataclasses import dataclass

@dataclass
class GamePiece:
    is_hole: bool
    is_circle: bool
    is_white: bool
    is_tall: bool

    def matched_with(self, other) -> bool:
        return (
            ( self.is_hole == other.is_hole ) |            
            ( self.is_circle == other.is_circle ) |            
            ( self.is_white == other.is_white ) |            
            ( self.is_tall== other.is_tall )             
        )
    def __repr__(self):
        id = ""
        id += ( "h" if self.is_hole else "_" )
        id += ( "c" if self.is_circle else "_" )
        id += ( "w" if self.is_white else "_" )
        id += ( "t" if self.is_tall else "_" )
        return id
        
class BoardState:
    class WinType(Enum):
        HORIZONTAL = "h"
        VERTICAL = "v"
        DIAGNAL = "d"
        SQUARE = "s"
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
        self.win_state = None
    
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
    
    def __getitem__(self, index: ID) -> DATA:
        return self.__board[index]

    def __setitem__(self, index: ID, value: DATA):
        (x,y) = index
        if (x < 4) & (y < 4):
            self.__board[index] = value
            self.win_state = self.check_win(x, y)
        else:
            raise Exception(f"Invalid index ({x},{y}) !")

    def check_win(self, x: int, y: int) -> Optional[WinType]:
        if self.__check_win_across_h(y):
            return self.WinType.VERTICAL
        if self.__check_win_across_v(x):
            return self.WinType.HORIZONTAL
        if self.__check_win_across_d(x, y):
            return self.WinType.DIAGNAL
        return None

    def __check_win_across_h(self, y: int) -> bool:
        idx = self[0, y]
        if idx is not None:
            cp = self.get_piece(idx)
            for x in range(1, 4):
                idx = self[x, y]
                if idx is not None:
                    if not cp.matched_with(self.get_piece(idx)):
                        return False
                else: return False
            return True
        return False

    def __check_win_across_v(self, x: int) -> bool:
        idx = self[x, 0]
        if idx is not None:
            cp = self.get_piece(idx)
            for y in range(1, 4):
                idx = self[x, y]
                if idx is not None:
                    if not cp.matched_with(self.get_piece(idx)):
                        return False
                else: return False
            return True
        return False

    def __check_win_across_d(self, x: int, y: int) -> bool:
        if x == y:
            idx = self[0,0]
            if idx is not None:
                cp = self.get_piece(idx)
                for t in range(1, 4):
                    idx = self[t, t]
                    if idx is not None:
                        if not cp.matched_with(self.get_piece(idx)):
                            return False
                    else: return False
                return True
        elif x + y == 3:
            idx = self[0,3]
            if idx is not None:
                cp = self.get_piece(idx)
                for t in range(1, 4):
                    idx = self[t, 3-t]
                    if idx is not None:
                        if not cp.matched_with(self.get_piece(idx)):
                            return False
                    else: return False
                return True
        return False
    def __repr__(self):
        return f"<Board win={self.win_state}>\n " + (
            "\n ".join([
                " | ".join([
                    f"{self.get_piece(self[x,y])}" if self[x,y] is not None else f"    "
                    for y in range(4)
                ])
                for x in range(4)
            ])
        ) + "\n<Board/>"
