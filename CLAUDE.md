# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案概述

FC/NES 版《三國志》(KOEI, 1988) ROM 逆向工程專案。解析 iNES 格式 ROM 中的武將資料、頭像圖像等遊戲內容。

## 常用指令

```bash
# 執行武將資料匯出 (產生 CSV + XLSX)
python3 sangokushi_extract_v2.py

# 指定其他 ROM 檔案
python3 sangokushi_extract_v2.py path/to/rom.nes
```

依賴: Python 3, openpyxl (可選, 用於 Excel 匯出)

## 關鍵檔案

| 檔案 | 用途 |
|------|------|
| `sangokushi_extract_v2.py` | 主程式: 解析 ROM 並匯出武將資料 |
| `docs/DATA_FORMAT.md` | 武將資料表格式技術規格 |
| `MEMORY.md` | 逆向工程研究筆記 (ROM 結構、頭像系統分析) |

## ROM 結構

- 格式: iNES, Mapper 1 (MMC1)
- PRG ROM: 256 KB (16 banks × 16 KB), 偏移 0x00010–0x4000F
- CHR ROM: 0 KB (CHR-RAM, tile 圖形存於 PRG ROM)
- Bank 偏移計算: `file_offset = bank × 0x4000 + 0x10`
- 武將資料表: Bank 14 (0x38010), 256 筆 × 17 bytes

## 開發慣例

- 外部資料 (非 ROM 解析) 欄位名加 `[EXT]` 前綴
- 程式碼註解與文件以中文為主
- 輸出檔案使用 UTF-8-BOM 編碼 (Excel 相容)

## 目前進度

- ✓ 武將資料表完整解析 (256 筆記錄, 12 欄位)
- ✓ CSV/XLSX 匯出工具
- ⏳ 頭像系統 (已知 6×6 tiles, 待完成圖像匯出)
