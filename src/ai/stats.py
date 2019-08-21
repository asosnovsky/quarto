from typing import List, Dict, Any, Optional, Iterable
from tqdm import tqdm
from pandas import DataFrame
from src.ai import (
    run_sim_once,
    AIPlayer
)

def compute_stats(ai_list: List[AIPlayer], rounds: int, out_filepath: Optional[str]) -> DataFrame:
    def write(row: Iterable[Any], mode='a'):
        if out_filepath is None:
            return;
        else:
            open(out_filepath, mode).write(",".join([
                f'"{n}"' for n in row
            ]) + "\n")

    results: List[Dict[str, Any]] = []
    write([
        "Player 1","Player 2","Player 1 Wins","Player 2 Wins","Tie","Rounds"
    ], 'w+')

    for ai0 in tqdm(ai_list, position=0):
        for ai1 in tqdm(ai_list, position=1):
            stats = {'Player 1 Wins': 0, 'Player 2 Wins': 0, 'Tie': 0}
            for _ in tqdm(range(rounds), desc=f'Testing {ai0.__name__} vs {ai1.__name__}', position=2):
                winner = run_sim_once(ai0, ai1, False)
                if winner is not None:
                    stats[ winner + ' Wins'] += 1
                else:
                    stats['Tie'] += 1
            results.append({
                'Player 1': ai0.__name__,
                'Player 2': ai1.__name__,
                **stats,
                'Rounds': rounds,
            })
            write(results[-1].values())

    return DataFrame(results)