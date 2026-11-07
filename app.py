from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import game_logic as gl

st.set_page_config(page_title="2048", page_icon="🔢", layout="centered")
st.markdown(
    "<style>.block-container{padding-top:1.5rem;max-width:520px}</style>",
    unsafe_allow_html=True,
)

# 自定义组件：负责渲染棋盘、滑动/键盘输入、计时、浏览器自动存档
game_ui = components.declare_component(
    "game2048", path=str(Path(__file__).parent / "game_component")
)

S = st.session_state
if "g" not in S:
    S.g = gl.new_game()
    S.booted = False   # 是否已经尝试从浏览器读取过存档
    S.last_ev = None
    S.rev = 0


def handle(ev):
    g = S.g
    kind = ev.get("type")
    if kind == "boot":
        S.booted = True
        restored = gl.restore(ev.get("data"))
        if restored:
            S.g = restored
        return
    el = ev.get("elapsed")
    if isinstance(el, (int, float)) and el >= 0:
        g["elapsed"] = float(el)
    if kind == "move":
        gl.apply_move(g, ev.get("dir"))
    elif kind == "undo":
        gl.undo(g)
    elif kind == "new":
        S.g = gl.new_game(best=g["best"])


ev = game_ui(
    state={**gl.view(S.g), "rev": S.rev},
    save=gl.export_save(S.g),
    boot=not S.booted,
    key="game",
    default=None,
)

if ev and ev.get("id") != S.last_ev:
    S.last_ev = ev["id"]
    handle(ev)
    S.rev += 1
    st.rerun()

st.caption("进度会自动保存在当前浏览器中，刷新页面可继续；换设备或清除浏览器数据后不会保留。")
