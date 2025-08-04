# 最开始的试验
# # 运行前：pip install pandas requests
# import pandas as pd, requests, pathlib
#
# URLS = {
#     2:  "https://caniwin.com/texasholdem/preflop/heads-up.php",          # 穷举法 · 精确 :contentReference[oaicite:0]{index=0}
#     10: "https://caniwin.com/poker/texas-holdem/pre-flop/10-player-odds/" # 15 亿次模拟 :contentReference[oaicite:1]{index=1}
# }
#
# frames = []
# for n_players, url in URLS.items():
#     html = requests.get(url, timeout=10).text
#     df = pd.read_html(html, header=0)[0]               # 页面上唯一的表
#     df = (
#         df.rename(columns={'Name': 'hand', 'Win %': 'win_pct'})  # 只保留手牌 & 胜率
#           .loc[:, ['hand', 'win_pct']]
#     )
#     # '84.93' → 0.8493
#     df['win_pct'] = df['win_pct'].astype(float) / 100
#     df['players'] = n_players
#     frames.append(df)
#
# full = pd.concat(frames, ignore_index=True)
# pathlib.Path("data").mkdir(exist_ok=True)
# full.to_csv("C:/Users/ray/Desktop/postgraduate learning/dissertation/preflop_equity_canIWin.csv", index=False)
# print("✅ Saved to data/preflop_equity_canIWin.csv")

#从github找到的数据  2-10人
# import pathlib, requests, sys
#
# DATA = pathlib.Path(__file__).resolve().parent / "data"
# DATA.mkdir(exist_ok=True)
#
# base = ("https://raw.githubusercontent.com/oscar6echo/"
#         "Poker2/master/Tables/preflop_equity_{}_players.csv")
#
# for n in range(2, 11):                # 2‥10 人
#     url = base.format(n)
#     try:
#         r = requests.get(url, timeout=15)
#         r.raise_for_status()
#         out_file = DATA / f"preflop_equity_{n}_players.csv"
#         out_file.write_bytes(r.content)
#         print(f"✔  saved {out_file.name}")
#     except Exception as e:
#         print(f"✘  {url}  下载失败：{e}", file=sys.stderr)
#
# print(f"\n✅  ALL DONE → {DATA}")

#弄出完整的表
import pandas as pd
import pathlib

# ───────────────── ① 路径 ────────────────────────────────────────────────
IN_F = pathlib.Path(
    r"C:\Users\ray\Desktop\postgraduate learning\dissertation\poker\data\Poker2\Tables\df_equity_montecarlo_1m_300.csv"
)
OUT_F = pathlib.Path(
    r"C:\Users\ray\Desktop\postgraduate learning\dissertation\poker\data\date ready for using.csv"
)

df = pd.read_csv(IN_F)

# ───────────────── ② 通用阈值函数 ───────────────────────────────────────
THRESH_RAISE = 0.30  # Raise ≥ 0.30 BB
THRESH_CALL = 0.00  # Call  0 – 0.30 BB


def rec(ev):  # recommendation
    if ev >= THRESH_RAISE:
        return "Raise"
    elif ev >= THRESH_CALL:
        return "Call"
    else:
        return "Fold"


def tag(ev):  # tag 分级
    if ev >= 0.50:
        return "Premium"
    elif ev >= 0.10:
        return "Strong"
    elif ev >= -0.20:
        return "Speculative"
    else:
        return "Marginal"


# ───────────────── ③ 逐桌人数批量计算 ──────────────────────────────────
for opp in range(1, 10):  # 对手数 1–9 → 总玩家 2–10
    N = opp + 1
    win_col = f"{opp}_win"  # 例：1_win, 2_win …
    tie_col = f"{opp}_tie"

    ev_col = f"EV_{N}p"
    rec_col = f"rec_{N}p"
    tag_col = f"tag_{N}p"

    # EV = 胜*N + 平*N/2 – 1  （单位 BB）
    df[ev_col] = df[win_col] * N + df[tie_col] * (N / 2) - 1
    df[rec_col] = df[ev_col].apply(rec)
    df[tag_col] = df[ev_col].apply(tag)

# ───────────────── ④ 保存 & 小预览 ─────────────────────────────────────
df.to_csv(OUT_F, index=False)
print(f"✅ 已生成：{OUT_F}")
print(df.loc[:4, ["hand", "EV_2p", "rec_2p", "tag_2p", "EV_6p", "rec_6p", "tag_6p"]])
