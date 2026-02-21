# 漢字 Tile 圖形分析

## 映射公式 (已確認)

透過 Mesen debugger 追蹤，確認了漢字 tile 的儲存位置：

```
PRG_ROM_offset = 0x20004 + tile_id × 32
File_offset = PRG_ROM_offset + 0x10 (iNES header)
```

- **基址 (PRG ROM)**: `0x20004`
- **基址 (檔案)**: `0x20014`
- **每個 tile**: 8 bytes (只有 Plane 0)
- **每個漢字**: 32 bytes (4 tiles × 8 bytes)
- **Tile 排列**: `[0][1]` 在 offset+0, offset+8；`[2][3]` 在 offset+16, offset+24

### 特殊處理

ROM 中只儲存 Plane 0 (8 bytes/tile)。遊戲載入時將 Plane 0 複製到 Plane 1，
因此漢字只有黑白兩色（無灰階）。

### 驗證範例

「曹」字 (tile_id = 0x8E):
- PRG ROM offset = 0x20004 + 0x8E × 32 = 0x211C4 ✓
- 4 tiles 位於: 0x211C4, 0x211CC, 0x211D4, 0x211DC (每個間隔 8 bytes)

---

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
- 每個 tile: 8 bytes (只有 Plane 0，遊戲載入時複製到 Plane 1)
- 每個漢字: 32 bytes
- 顏色: 黑白兩色 (無灰階)

### 預估儲存空間
- Page 0: 241 × 32 = 7,712 bytes
- Page 1: 66 × 32 = 2,112 bytes
- 總計: ~9,824 bytes ≈ 9.6 KB

## 儲存位置

### Page 0 漢字 (已確認)
- **位置**: Bank 8 (0x20010-0x2400F)
- **漢字基址**: PRG 0x20004 / File 0x20014
- **範圍**: tile_id 0x01-0xFF (241 個漢字)
- **假名字體**: 0x22CA0 (同 Bank)

### Page 1 漢字 (待確認)
- 推測在 Page 0 之後或其他 Bank
- 需要追蹤 Page 1 漢字的實際載入位置

## 已解決問題

### ✓ Tile ID → ROM 偏移映射
透過 Mesen debugger 追蹤確認：
- 基址: `0x20004` (PRG ROM) / `0x20014` (檔案)
- 公式: `offset = base + tile_id × 32`
- 4 tiles 間隔 8 bytes 存放 (offset+0, +8, +16, +24)

### Page 1 漢字位置 (待確認)
Page 1 (擴展) 漢字的 tile 圖形位置尚未追蹤確認。
推測可能在 Page 0 之後，但需要進一步驗證。

## 追蹤方法 (已完成)

使用 **Mesen** 模擬器的 debug 功能：

1. 設定 PPU VRAM 寫入斷點 ($1BE0，「曹」字左上角 tile)
2. 追蹤到 tile 資料先存入 RAM ($04xx)
3. 再往上追蹤到 PRG ROM 讀取位置
4. 最終在 Memory Viewer 搜尋 tile 資料，找到 PRG ROM $211C4

## 相關檔案

| 檔案 | 說明 |
|------|------|
| `kanji_export.py` | 漢字圖形匯出工具 |
| `kanji_output/kanji_atlas_page0.png` | Page 0 完整字型表 (256 字) |
| `kanji_output/individual/` | 所有個別漢字圖片 |

## 後續工作

1. ~~使用模擬器 debug 功能追蹤實際 tile 載入~~ ✓
2. ~~確認 tile_id → ROM 偏移映射關係~~ ✓
3. ~~匯出所有漢字圖形~~ ✓
4. 使用 OCR 或人工對照建立正確的 KANJI_TILE_MAP
5. 追蹤 Page 1 漢字的 ROM 位置
