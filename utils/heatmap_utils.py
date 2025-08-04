# poker/utils/heatmap_utils.py
import pandas as pd

RANKS = ['A','K','Q','J','T','9','8','7','6','5','4','3','2']

def to_matrix(df: pd.DataFrame, players: int) -> pd.DataFrame:
    matrix = pd.DataFrame(index=RANKS, columns=RANKS, dtype=float)
    sub = df[df["players"] == players]

    for _, row in sub.iterrows():
        hand, win = row["hand"], row["win_pct"]
        r1, r2 = hand[0], hand[1]
        suited = hand.endswith("s")
        if r1 == r2:
            matrix.loc[r1, r2] = win
        elif suited:
            matrix.loc[r1, r2] = win
        else:
            matrix.loc[r2, r1] = win
    return matrix
