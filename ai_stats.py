from typing import List, Dict, Any
from tqdm import tqdm
from pandas import DataFrame
from src.ai import (
    ai_dumb, ai_1, ai_2, ai_3,
    ai_3s, ai_3d,
    ai_dp_dp, ai_sp_dp,
    ai_dp_ms, ai_sp_ms,
    run_sim_once,
    AIPlayer
)
from src.ai.stats import compute_stats

results = compute_stats(
    rounds = 1000,
    ai_list = [
        ai_dumb, ai_1, ai_2, ai_3,
        ai_3s, ai_3d,
        ai_dp_dp, ai_sp_dp,
        ai_dp_ms, ai_sp_ms,
    ],
    out_filepath = "ai_stats_res.csv"
)

print(results)