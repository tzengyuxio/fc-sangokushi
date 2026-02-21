# 漢字 Tile 圖形分析

## 映射公式 (已確認)

透過 Mesen debugger 追蹤，確認了漢字 tile 的儲存位置：

```
PRG_ROM_offset = 0x205E4 + (tile_id + 0x30) × 16
File_offset = PRG_ROM_offset + 0x10 (iNES header)
```

- **基址 (PRG ROM)**: `0x205E4`
- **基址 (檔案)**: `0x205F4`
- **PPU 偏移量**: `0x30` (tile_id + 0x30 = PPU tile index)
- **每個 tile**: 16 bytes (8×8 pixels)
- **每個漢字**: 64 bytes (4 tiles, 16×16 pixels)

### 驗證範例

「曹」字 (tile_id = 0x8E):
- PPU tile index = 0x8E + 0x30 = 0xBE
- PRG ROM offset = 0x205E4 + 0xBE × 16 = 0x211C4 ✓
- 4 tiles 位於: 0x211C4, 0x211D4, 0x211E4, 0x211F4

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

## 已解決問題

### ✓ Tile ID → ROM 偏移映射
透過 Mesen debugger 追蹤確認：
- 基址: `0x205E4` (PRG ROM) / `0x205F4` (檔案)
- 公式: `offset = base + (tile_id + 0x30) × 16`
- 4 tiles 連續存放

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
