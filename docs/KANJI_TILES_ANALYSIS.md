# 漢字 Tile 圖形分析

## 已確認資訊

### 姓名表結構 (0x3A314)
每筆記錄 15 bytes：
```
+0-7:   假名 (半角片假名, 8 bytes)
+8:     第一個漢字 tile ID
+9:     Page 指示器 (0=Page0, 1=Page1)
+10:    第二個漢字 tile ID
+11:    Page 指示器
+12:    第三個漢字 tile ID
+13:    Page 指示器
+14:    排序索引
```

### Tile ID 分布

| Page | Tile ID 範圍 | 數量 | 說明 |
|------|-------------|------|------|
| Page 0 | 0x01-0xFF | 241 個 | 基本漢字 |
| Page 1 | 0x01-0x42 | 66 個 | 擴展漢字 |
| **總計** | | **307 個** | |

### 漢字規格
- 尺寸: 16×16 像素 (遊戲畫面觀察)
- 組成: 4 個 8×8 NES tiles
- 每個 tile: 16 bytes (2 bitplanes × 8 rows)
- 每個漢字: 64 bytes

### 預估儲存空間
- Page 0: 241 × 64 = 15,424 bytes
- Page 1: 66 × 64 = 4,224 bytes
- 總計: ~19,648 bytes ≈ 19.2 KB

## 候選儲存位置

### Bank 8 (0x20010-0x2400F)
- 含有假名字體 (0x22CA0)
- 發現連續的 tile-like 資料區塊
- **但 tile_id 與 ROM 偏移的映射關係未確認**

### 其他圖形 Banks (3-7)
- Bank 4-7 也包含 tile 圖形資料
- 可能是頭像或地圖 tiles

## 未解決問題

### 1. Tile ID → ROM 偏移映射
已嘗試但未成功的映射方式：
- `offset = base + tile_id × 64` (連續 16x16 儲存)
- `offset = base + tile_id × 16` (單一 8x8 tile)
- PPU nametable 風格: `[id, id+1, id+16, id+17]`

可能原因：
- 漢字可能使用 lookup table 映射
- 可能有壓縮或特殊編碼
- 4 個 tiles 可能分散存放

### 2. Page 1 漢字位置
Page 1 (擴展) 漢字的 tile 圖形位置未知。

## 建議追蹤方法

使用 NES 模擬器的 debug 功能追蹤：

1. **FCEUX** 或 **Mesen** 模擬器
2. 設定 PPU 讀取斷點
3. 觀察顯示人名時讀取的 ROM 地址
4. 記錄 tile_id 與實際 ROM 偏移的對應

### 追蹤步驟
```
1. 載入遊戲，進入可顯示武將名字的畫面
2. 設定 PPU VRAM 寫入斷點 (CHR-RAM: $0000-$1FFF)
3. 觀察哪些 PRG-ROM 地址被讀取並複製到 CHR-RAM
4. 記錄 tile ID 與 ROM 偏移的關係
```

## 相關檔案

| 檔案 | 說明 |
|------|------|
| `kanji_tiles_page0.png` | 嘗試匯出的 Page 0 tiles (映射未確認) |
| `kanji_8E_*.png` | 「曹」字的各種嘗試 |

## 後續工作

1. 使用模擬器 debug 功能追蹤實際 tile 載入
2. 確認 tile_id → ROM 偏移映射關係
3. 匯出所有漢字圖形
4. 使用 OCR 或人工對照建立正確的 KANJI_TILE_MAP
