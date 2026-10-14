# Inventory Replenishment Game｜庫存補貨決策遊戲

每天只有一筆固定補貨額度：**只能選一種商品補 10 件**。你能否在不知道當日需求的情況下，把缺貨造成的少賣降到最低？

[Streamlit DEMO](https://inventory-replenishment-game.streamlit.app/)

> 當每天的補貨能力有限時，應優先補哪一種商品，才能減少缺貨造成的銷售損失？

這是一個用於**練習補貨決策**的互動模型。

## 功能

- 商品種類 N：3～8 種，預設 5 種；遊戲天數：7～30 天，預設 14 天。
- 所有商品初始庫存 5 件，每日只能選一種商品補貨 10 件，當日營業前到貨。
- 商品每日需求彼此獨立，以各自的公開需求範圍從整數均勻分布抽樣。
- 每天選完補貨品項，才公布當天需求量、賣出數與少賣數。
- 顯示當日商品明細、累計少賣與需求滿足率。
- 玩家和兩個自動補貨策略使用**完全相同**的需求序列比賽。
- 可設定隨機種子、重新挑戰同一組需求、下載 CSV 紀錄。

## 模型流程

每日：查看庫存 → 補一種商品 10 件 → 發生隨機需求 → 實際售出 / 缺貨流失 → 進入下一天。

- `sold = min(stock_after_restock, demand)`
- `lost = demand - sold`
- `stock_end = stock_after_restock - sold`
- `service_rate = total_sold / total_demand`（若需求為零，定義為 100%）

**自動比較策略**（只使用已知資訊）：

1. **最低庫存優先**：優先補絕對剩餘件數最少的商品；平手時優先補平均需求較高者。
2. **庫存可支撐天數最短優先**：優先補 `現有庫存 / 已知平均日需求` 最小的商品。

策略比較並不等於證明最佳化，也沒有偷看當天或未來需求。

## 技術

- Python 3.12（建議部署版本）
- Streamlit 1.65.0
- Python 標準函式庫：`random`、`dataclasses`、`csv`
- pytest（只用於開發測試，部署不需要）
- 無資料庫、無 API key、無任何必須上傳的資料集

## 本機執行

將整個專案資料夾放到電腦上，在該資料夾執行：

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Windows PowerShell / Miniforge 環境中也可以用以上單行指令。

執行測試（pytest 需另行安裝）：

```bash
python -m pip install pytest
python -m pytest -q
```

## 專案結構

```text
inventory-replenishment-game/
├── app.py                     # 介面：玩家操作、表格、排行榜與 CSV
├── simulation.py              # 可獨立測試的核心邏輯
├── requirements.txt           # 雲端部署依賴
├── .streamlit/config.toml     # 基本配色
├── .gitignore
├── tests/test_simulation.py   # 邏輯測試
└── README.md
```

<!--

## 限制與未來方向

- 沒有售價、單位毛利、庫存持有成本，第一版以「少賣件數」為目標；這還不是真實獲利最佳化。
- 固定補貨數量為 10 件，忽略供應商交貨時間、儲存容量、有效期限等因素。
- 需求是人工設定的機率分布，沒有使用真實銷售或未滿足需求資料校準。
- 遊戲進度放在 Streamlit session，伺服器重啟或連線重設可能遺失；沒有跨裝置儲存。
- 未來可加入不同商品毛利、庫存持有成本、可比較的補貨策略，以及以實際需求資料校準模型。

-->

## 驗收

- 每天補貨**恰好一次**，只補一種商品 10 件。
- 賣出不超過現有庫存，庫存永不為負。
- 少賣量 = 當日需求量 − 當日實際銷售量。
- 使用相同種子得到相同需求序列，玩家的選擇不影響未來需求。
- 只有遊戲結束才顯示自動策略比較，並且每種策略使用相同需求。
