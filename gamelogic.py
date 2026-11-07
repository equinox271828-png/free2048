"""2048 纯逻辑（不依赖 streamlit，方便测试）。状态全部放在一个 dict 里。"""
import random

SIZE = 4
MAX_HISTORY = 1000  # 撤销步数上限（足够多，基本等于不限）


def new_game(best=0):
    g = {
        "board": [[0] * SIZE for _ in range(SIZE)],
        "score": 0,
        "best": best,
        "history": [],      # 每项: [棋盘, 分数]
        "elapsed": 0.0,     # 已用秒数（由前端同步）
        "running": False,   # 第一次有效移动后开始计时
        "won": False,
        "over": False,
        "new_idx": -1,      # 最新生成方块的位置，用于动画
    }
    _spawn(g)
    _spawn(g)
    g["new_idx"] = -1
    return g


def _spawn(g):
    empties = [(r, c) for r in range(SIZE) for c in range(SIZE) if g["board"][r][c] == 0]
    if not empties:
        return
    r, c = random.choice(empties)
    g["board"][r][c] = 4 if random.random() < 0.1 else 2
    g["new_idx"] = r * SIZE + c


def _slide_left(row):
    tiles = [v for v in row if v]
    out, gained, i = [], 0, 0
    while i < len(tiles):
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            merged = tiles[i] * 2
            out.append(merged)
            gained += merged
            i += 2
        else:
            out.append(tiles[i])
            i += 1
    return out + [0] * (SIZE - len(out)), gained


def move_board(board, direction):
    """返回 (新棋盘, 本次得分)。其他方向通过转置/翻转复用"向左"。"""
    b = [row[:] for row in board]
    if direction in ("up", "down"):
        b = [list(r) for r in zip(*b)]
    if direction in ("right", "down"):
        b = [r[::-1] for r in b]
    gained, nb = 0, []
    for r in b:
        nr, g = _slide_left(r)
        nb.append(nr)
        gained += g
    if direction in ("right", "down"):
        nb = [r[::-1] for r in nb]
    if direction in ("up", "down"):
        nb = [list(r) for r in zip(*nb)]
    return nb, gained


def can_move(board):
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:
                return True
            if c + 1 < SIZE and board[r][c] == board[r][c + 1]:
                return True
            if r + 1 < SIZE and board[r][c] == board[r + 1][c]:
                return True
    return False


def apply_move(g, direction):
    if g["over"] or direction not in ("up", "down", "left", "right"):
        return False
    nb, gained = move_board(g["board"], direction)
    if nb == g["board"]:
        return False
    g["history"].append([g["board"], g["score"]])
    del g["history"][:-MAX_HISTORY]
    g["board"] = nb
    g["score"] += gained
    _spawn(g)
    g["best"] = max(g["best"], g["score"])
    g["running"] = True
    if any(v >= 2048 for row in nb for v in row):
        g["won"] = True
    if not can_move(g["board"]):
        g["over"] = True
        g["running"] = False
    return True


def undo(g):
    if not g["history"]:
        return False
    board, score = g["history"].pop()
    if g["over"]:
        g["running"] = True
    g["board"], g["score"] = board, score
    g["over"] = False
    g["new_idx"] = -1
    return True


def view(g):
    """发给前端渲染的数据。"""
    return {
        "board": g["board"], "score": g["score"], "best": g["best"],
        "elapsed": g["elapsed"], "running": g["running"],
        "won": g["won"], "over": g["over"],
        "undo_n": len(g["history"]), "new_idx": g["new_idx"],
    }


def export_save(g):
    """写入浏览器 localStorage 的完整存档（含撤销历史）。"""
    return {
        "v": 1, "board": g["board"], "score": g["score"], "best": g["best"],
        "history": g["history"], "elapsed": g["elapsed"], "running": g["running"],
        "won": g["won"], "over": g["over"],
    }


def _valid_board(b):
    return (
        isinstance(b, list) and len(b) == SIZE
        and all(isinstance(r, list) and len(r) == SIZE
                and all(isinstance(v, int) and v >= 0 for v in r) for r in b)
    )


def restore(d):
    """从存档恢复；数据不合法返回 None。"""
    try:
        if not isinstance(d, dict) or d.get("v") != 1 or not _valid_board(d["board"]):
            return None
        hist = [[h[0], int(h[1])] for h in d.get("history", []) if _valid_board(h[0])]
        score = int(d["score"])
        over = not can_move(d["board"])
        return {
            "board": d["board"], "score": score,
            "best": max(int(d.get("best", 0)), score),
            "history": hist[-MAX_HISTORY:],
            "elapsed": max(0.0, float(d.get("elapsed", 0))),
            "running": bool(d.get("running")) and not over,
            "won": bool(d.get("won")), "over": over, "new_idx": -1,
        }
    except (KeyError, TypeError, ValueError, IndexError):
        return None

