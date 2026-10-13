"""Streamlit front end for Inventory Replenishment Game."""

import csv
from io import StringIO

import streamlit as st

from simulation import InventoryGame, new_game, run_baseline

st.set_page_config(page_title="庫存補貨決策遊戲", page_icon="📦", layout="wide")


def export_history_csv(game: InventoryGame) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "day",
            "product",
            "stock_before",
            "restocked",
            "demand",
            "sold",
            "lost",
            "stock_end",
        ]
    )
    for result in game.history:
        for i, item in enumerate(game.products):
            writer.writerow(
                [
                    result.day,
                    item.name,
                    result.stock_before[i],
                    game.restock_units if i == result.choice else 0,
                    result.demand[i],
                    result.sold[i],
                    result.lost[i],
                    result.stock_end[i],
                ]
            )
    return output.getvalue()


if "game" not in st.session_state:
    st.session_state.game = new_game()

st.title("📦 庫存補貨決策遊戲")
st.caption("每天只能補一種商品 10 件。用有限的補貨能力，盡量滿足顧客需求。")

with st.sidebar:
    st.header("⚙️ 遊戲設定")
    with st.form("settings"):
        n = st.slider("商品種類 N", min_value=3, max_value=8, value=5, step=1)
        days = st.slider("營業天數", min_value=7, max_value=30, value=14, step=1)
        seed = st.number_input(
            "隨機種子（可重現）", min_value=0, max_value=999999, value=2026, step=1
        )
        new_round = st.form_submit_button("開始新遊戲", use_container_width=True)
    if new_round:
        st.session_state.game = new_game(n=n, days=days, seed=int(seed))
        st.rerun()
    st.info("修改設定後按『開始新遊戲』才會生效，進度將歸零。")
    st.caption("每種商品起始 5 件；每天補一種商品 10 件，補貨立即到貨。")


game: InventoryGame = st.session_state.game
m1, m2, m3, m4 = st.columns(4)
m1.metric("進度", f"{game.day} / {game.days} 天")
m2.metric("累計售出", f"{game.total_sold} 件")
m3.metric("累計少賣", f"{game.total_lost} 件")
m4.metric("需求滿足率", f"{game.service_rate:.1%}")

left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("目前庫存")
    stock_rows = [
        {
            "商品": product.name,
            "剩餘庫存": game.stock[i],
            "每日需求範圍": f"0～{product.max_demand} 件",
            "估計日均需求": f"{product.average_demand:g} 件",
        }
        for i, product in enumerate(game.products)
    ]
    st.dataframe(stock_rows, hide_index=True, width="stretch")
    st.caption(
        "每日需求在表列整數範圍內均勻抽樣，各商品彼此獨立；玩家不會提前看到當日實際需求。"
    )

with right:
    st.subheader("今日決策")
    if not game.finished:
        st.write(f" **第 {game.day + 1} 天：** 請選擇唯一要補貨的商品。")
        choice = st.selectbox(
            "要補哪種商品？",
            range(len(game.products)),
            format_func=lambda i: f"{game.products[i].name}（目前 {game.stock[i]} 件）",
        )
        if st.button("補貨 +10 件，開始營業", type="primary", use_container_width=True):
            game.step(int(choice))
            st.rerun()
    else:
        st.success("🎉 挑戰結束！下方可比較不同策略的結果。")
        if st.button("以同一組需求重新挑戰", use_container_width=True):
            st.session_state.game = InventoryGame(
                products=game.products,
                schedule=game.schedule,
                starting_units=game.starting_units,
                restock_units=game.restock_units,
            )
            st.rerun()
    st.caption("目標：在不知道當天實際需求的情況下，盡可能減少少賣件數。")

if game.history:
    last = game.history[-1]
    st.divider()
    st.subheader(f"第 {last.day} 天營業結果")
    st.write(
        f"補貨：**{game.products[last.choice].name} +{game.restock_units} 件**　|　"
        f"需求：**{last.total_demand} 件**　|　"
        f"售出：**{last.total_sold} 件**　|　"
        f"少賣：**{last.total_lost} 件**"
    )
    st.dataframe(
        [
            {
                "商品": product.name,
                "今日需求": last.demand[i],
                "賣出": last.sold[i],
                "少賣": last.lost[i],
                "剩餘庫存": last.stock_end[i],
            }
            for i, product in enumerate(game.products)
        ],
        hide_index=True,
        width="stretch",
    )

    with st.expander("查看每天的營運紀錄"):
        st.dataframe(
            [
                {
                    "天數": result.day,
                    "補貨商品": game.products[result.choice].name,
                    "當日需求": result.total_demand,
                    "實際售出": result.total_sold,
                    "少賣件數": result.total_lost,
                }
                for result in game.history
            ],
            hide_index=True,
            width="stretch",
        )
        st.download_button(
            "下載逐商品營運紀錄 CSV",
            data="\ufeff" + export_history_csv(game),
            file_name="inventory_game_history.csv",
            mime="text/csv",
        )

if game.finished:
    st.divider()
    st.subheader("📊 同一組需求下的策略比較")
    least_stock = run_baseline(game, "lowest_stock")
    shortest_cover = run_baseline(game, "shortest_cover")
    results = [
        {
            "策略": "玩家",
            "售出件數": game.total_sold,
            "少賣件數": game.total_lost,
            "需求滿足率": f"{game.service_rate:.1%}",
        },
        {
            "策略": "最低庫存優先",
            "售出件數": least_stock.total_sold,
            "少賣件數": least_stock.total_lost,
            "需求滿足率": f"{least_stock.service_rate:.1%}",
        },
        {
            "策略": "庫存可支撐天數最短優先",
            "售出件數": shortest_cover.total_sold,
            "少賣件數": shortest_cover.total_lost,
            "需求滿足率": f"{shortest_cover.service_rate:.1%}",
        },
    ]
    st.dataframe(results, hide_index=True, width="stretch")
    st.caption(
        "三種策略面對完全相同的需求序列。兩個自動策略只根據當時庫存及已公開的需求範圍做決策，不偷看未來。"
    )
    st.info(
        "這是教學模型，不代表真實門市的成本最佳解。部分商品設定下，長期總需求可能大於每日補貨 10 件，因此無法完全避免缺貨。"
    )
else:
    st.divider()
    st.caption("策略比較會在挑戰結束後公布。任何策略都必須每天先補貨，再揭曉當天需求。")

with st.expander("ℹ️ 模型假設與限制"):
    st.markdown("""
- 每天只補一種商品、固定 10 件，立刻到貨。
- 每種商品起始 5 件；每日需求量從 0 到指定上限的整數均勻分布抽樣。
- 未賣出的需求視為當日流失，不會變成隔天的未完成訂單。
- 沒有售價、進貨成本、庫存持有成本、效期或供應商交期。
- 遊戲進度只保存在目前的瀏覽器連線工作階段；重新連線或伺服器重啟可能遺失。
- 目前使用的主要指標為「需求滿足率」和「少賣件數」，不能直接推算真實獲利。
""")
