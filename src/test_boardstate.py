from boardstate import BoardState

    
b = BoardState()

b[(0,0)] = 0
b[(1,0)] = 1
b[(2,0)] = 2
b[(3,0)] = 3

assert b.win_state == BoardState.WinType.VERTICAL

b = BoardState()

b[(0,0)] = 0
b[(0,1)] = 1
b[(0,2)] = 2
b[(0,3)] = 3

assert b.win_state == BoardState.WinType.HORIZONTAL

b = BoardState()

b[(0,0)] = 0
b[(1,1)] = 1
b[(2,2)] = 2
b[(3,3)] = 3

assert b.win_state == BoardState.WinType.DIAGNAL

b = BoardState()

b[(0,3)] = 0
b[(1,2)] = 1
b[(2,1)] = 2
b[(3,0)] = 3

assert b.win_state == BoardState.WinType.DIAGNAL