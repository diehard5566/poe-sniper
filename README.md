# POE 交易搶道具助手

Path of Exile 市集 live search 一鍵觸發「Travel to Hideout」搶道具。

## 使用方式

1. 安裝依賴：`pip3 install -r requirements.txt`（若沒有 pip3，用 `python3 -m pip install -r requirements.txt`）
2. 執行：`python3 main.py`

**macOS 若出現 `No module named '_tkinter'`**：Homebrew 的 Python 預設沒帶 Tk，請先安裝：
`brew install python-tk@3.12`（數字改成你目前的 Python 小版，如 3.11 就用 `python-tk@3.11`）。若 brew 權限錯誤，先執行：`sudo chown -R $(whoami) /opt/homebrew` 再重試。
3. 在介面新增你的 pathofexile.tw/trade/search 網址（可多個）
4. 設定熱鍵（預設 ctrl+alt+t），按「套用熱鍵」
5. 按「啟動監控」開啟 Chrome 並載入所有 live search 分頁
6. 看到想要的物品時按熱鍵，程式會掃描所有分頁並點擊第一個可用的 Travel to Hideout

## 設定檔

- `poe_urls.json`：儲存的 live search 網址清單
- `config.json`：熱鍵、按鈕 selector、視窗大小（自動產生）

## 打包成 exe（PyInstaller）

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "POE-Sniper" main.py
```

執行檔會產生在 `dist/`。注意：仍須本機已安裝 Chrome；ChromeDriver 由 webdriver-manager 在首次執行時下載。
